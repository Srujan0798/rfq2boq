"""A/B Testing infrastructure for model comparison.

Routes requests between production and candidate models.
Tracks per-model latency, error rate, and user feedback.
Computes statistical significance.
"""

from __future__ import annotations

import logging
import random
import time
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ModelMetrics:
    total_requests: int = 0
    errors: int = 0
    latencies: list[float] = field(default_factory=list)
    feedbacks: list[int] = field(default_factory=list)

    @property
    def error_rate(self) -> float:
        return self.errors / self.total_requests if self.total_requests > 0 else 0.0

    @property
    def avg_latency(self) -> float:
        return sum(self.latencies) / len(self.latencies) if self.latencies else 0.0

    @property
    def avg_feedback(self) -> float | None:
        return sum(self.feedbacks) / len(self.feedbacks) if self.feedbacks else None


@dataclass
class ABTestResult:
    model_a_name: str
    model_b_name: str
    sample_size: int
    statistical_significance: float
    winner: str | None
    confidence: float
    latency_a_avg: float
    latency_b_avg: float
    error_rate_a: float
    error_rate_b: float
    recommendation: str


class ABTestRouter:
    def __init__(
        self,
        production_model: str,
        candidate_model: str,
        experiment_name: str = "rfq2boq-ab-test",
        tracking_uri: str | None = None,
    ):
        self.production_model = production_model
        self.candidate_model = candidate_model
        self.experiment_name = experiment_name
        self.tracking_uri = tracking_uri

        self._metrics_a: dict[str, ModelMetrics] = defaultdict(ModelMetrics)
        self._metrics_b: dict[str, ModelMetrics] = defaultdict(ModelMetrics)

        if tracking_uri:
            import mlflow
            mlflow.set_tracking_uri(tracking_uri)
            mlflow.set_experiment(self.experiment_name)

    def route(
        self,
        request_id: str,
        handler: Callable[[], Any],
        candidate_ratio: float = 0.1,
    ) -> tuple[Any, str]:
        is_candidate = random.random() < candidate_ratio
        model_name = self.candidate_model if is_candidate else self.production_model
        metrics = self._metrics_b if is_candidate else self._metrics_a

        start = time.time()
        try:
            result = handler()
            latency = time.time() - start
            metrics[request_id].total_requests += 1
            metrics[request_id].latencies.append(latency)
            return result, model_name
        except Exception as e:
            latency = time.time() - start
            metrics[request_id].errors += 1
            metrics[request_id].latencies.append(latency)
            logger.warning(f"Model {model_name} error: {e}")
            raise

    def record_feedback(self, request_id: str, rating: int, model_name: str) -> None:
        if model_name == self.candidate_model:
            self._metrics_b[request_id].feedbacks.append(rating)
        else:
            self._metrics_a[request_id].feedbacks.append(rating)

    def analyze(self) -> ABTestResult:
        total_a = sum(m.total_requests for m in self._metrics_a.values())
        total_b = sum(m.total_requests for m in self._metrics_b.values())
        errors_a = sum(m.errors for m in self._metrics_a.values())
        errors_b = sum(m.errors for m in self._metrics_b.values())
        latencies_a = [lat for m in self._metrics_a.values() for lat in m.latencies]
        latencies_b = [lat for m in self._metrics_b.values() for lat in m.latencies]

        avg_lat_a = sum(latencies_a) / len(latencies_a) if latencies_a else 0.0
        avg_lat_b = sum(latencies_b) / len(latencies_b) if latencies_b else 0.0
        err_rate_a = errors_a / total_a if total_a > 0 else 0.0
        err_rate_b = errors_b / total_b if total_b > 0 else 0.0

        significance = self._compute_significance(latencies_a, latencies_b)
        winner = None
        confidence = 0.0

        if significance > 0.95:
            if avg_lat_b < avg_lat_a and err_rate_b <= err_rate_a:
                winner = self.candidate_model
                confidence = significance
            elif avg_lat_a <= avg_lat_b and err_rate_a < err_rate_b:
                winner = self.production_model
                confidence = significance

        recommendation = "promote_candidate" if winner == self.candidate_model else "keep_production"

        return ABTestResult(
            model_a_name=self.production_model,
            model_b_name=self.candidate_model,
            sample_size=total_a + total_b,
            statistical_significance=significance,
            winner=winner,
            confidence=confidence,
            latency_a_avg=avg_lat_a,
            latency_b_avg=avg_lat_b,
            error_rate_a=err_rate_a,
            error_rate_b=err_rate_b,
            recommendation=recommendation,
        )

    def _compute_significance(self, latencies_a: list[float], latencies_b: list[float]) -> float:
        if len(latencies_a) < 30 or len(latencies_b) < 30:
            return 0.0

        import math
        mean_a = sum(latencies_a) / len(latencies_a)
        mean_b = sum(latencies_b) / len(latencies_b)
        var_a = sum((x - mean_a) ** 2 for x in latencies_a) / len(latencies_a)
        var_b = sum((x - mean_b) ** 2 for x in latencies_b) / len(latencies_b)

        pooled_se = math.sqrt(var_a / len(latencies_a) + var_b / len(latencies_b))
        if pooled_se == 0:
            return 0.0

        t_stat = abs(mean_a - mean_b) / pooled_se
        try:
            from scipy.stats import t as t_dist
            p_value = 2 * (1 - t_dist.cdf(t_stat, len(latencies_a) + len(latencies_b) - 2))
            return 1.0 - p_value if p_value else 0.0
        except Exception:
            return 0.0

    def get_summary(self) -> dict[str, Any]:
        total_a = sum(m.total_requests for m in self._metrics_a.values())
        total_b = sum(m.total_requests for m in self._metrics_b.values())
        err_a = sum(m.errors for m in self._metrics_a.values())
        err_b = sum(m.errors for m in self._metrics_b.values())
        fb_a = [f for m in self._metrics_a.values() for f in m.feedbacks]
        fb_b = [f for m in self._metrics_b.values() for f in m.feedbacks]

        all_lat_a = [lat for m in self._metrics_a.values() for lat in m.latencies]
        all_lat_b = [lat for m in self._metrics_b.values() for lat in m.latencies]

        return {
            "production": {
                "requests": total_a,
                "errors": err_a,
                "error_rate": err_a / total_a if total_a > 0 else 0.0,
                "avg_latency": sum(all_lat_a) / len(all_lat_a) if all_lat_a else 0.0,
                "avg_feedback": sum(fb_a) / len(fb_a) if fb_a else None,
            },
            "candidate": {
                "requests": total_b,
                "errors": err_b,
                "error_rate": err_b / total_b if total_b > 0 else 0.0,
                "avg_latency": sum(all_lat_b) / len(all_lat_b) if all_lat_b else 0.0,
                "avg_feedback": sum(fb_b) / len(fb_b) if fb_b else None,
            },
        }
