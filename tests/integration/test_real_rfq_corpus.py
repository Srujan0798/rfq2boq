"""Integration tests for real RFQ corpus."""

import csv
import json
from pathlib import Path

import pytest


class TestManifestCSV:
    """Tests for manifest.csv validity."""

    def test_manifest_csv_exists(self):
        manifest = Path("data/real_rfqs/annotations/manifest.csv")
        assert manifest.exists(), f"manifest.csv not found at {manifest}"

    def test_manifest_csv_has_required_columns(self):
        with open("data/real_rfqs/annotations/manifest.csv") as f:
            rows = list(csv.DictReader(f))
        required = ["filename", "sha256", "pages", "source", "is_real"]
        for r in rows:
            assert all(col in r for col in required), f"Missing columns in {r.get('filename', '?')}"

    def test_manifest_50_plus_entries(self):
        with open("data/real_rfqs/annotations/manifest.csv") as f:
            rows = list(csv.DictReader(f))
        assert len(rows) >= 50, f"Only {len(rows)} entries in manifest"

    def test_manifest_sha256_valid(self):
        with open("data/real_rfqs/annotations/manifest.csv") as f:
            rows = list(csv.DictReader(f))
        for r in rows:
            sha = r.get("sha256", "")
            assert len(sha) == 64, f"Invalid SHA256 for {r['filename']}"
            assert all(c in "0123456789abcdef" for c in sha), f"Invalid chars in SHA256 for {r['filename']}"

    def test_all_pdfs_exist(self):
        with open("data/real_rfqs/annotations/manifest.csv") as f:
            manifest_rows = list(csv.DictReader(f))
        raw_dir = Path("data/real_rfqs/raw")
        existing = set(f.name for f in raw_dir.rglob("*.pdf"))
        missing = []
        for r in manifest_rows:
            fname = Path(r["filename"]).name
            if fname not in existing:
                missing.append(r["filename"])
        assert len(missing) == 0, f"Missing PDFs: {missing[:10]}..."


class TestGoldAnnotations:
    """Tests for gold_annotations.json validity."""

    def test_gold_file_exists(self):
        gold_path = Path("data/real_rfqs/annotations/gold_annotations.json")
        assert gold_path.exists(), f"gold_annotations.json not found at {gold_path}"

    def test_gold_has_20_entries(self):
        with open("data/real_rfqs/annotations/gold_annotations.json") as f:
            gold = json.load(f)
        assert isinstance(gold, list), "gold_annotations.json must be a list"
        assert len(gold) == 20, f"gold_annotations.json has {len(gold)} entries, need exactly 20"

    def test_all_gold_complete_and_filled(self):
        with open("data/real_rfqs/annotations/gold_annotations.json") as f:
            gold = json.load(f)
        complete = [x for x in gold if x.get("metadata", {}).get("status") == "complete"]
        filled = [x for x in gold if len(x.get("entities", [])) > 0]
        assert len(complete) >= 20, f"Only {len(complete)}/20 complete"
        assert len(filled) >= 20, f"Only {len(filled)}/20 filled"

    def test_gold_entities_valid_types(self):
        with open("data/real_rfqs/annotations/gold_annotations.json") as f:
            gold = json.load(f)
        valid_types = {"MATERIAL", "QUANTITY", "UNIT", "LOCATION", "DIMENSION", "STANDARD", "ACTION", "GRADE"}
        for ann in gold:
            for ent in ann.get("entities", []):
                assert ent["type"] in valid_types, f"Invalid type {ent['type']} in {ann.get('doc_id','?')}"

    def test_gold_relations_valid_types(self):
        with open("data/real_rfqs/annotations/gold_annotations.json") as f:
            gold = json.load(f)
        valid_types = {"HAS_QUANTITY", "HAS_UNIT", "AT_LOCATION", "OF_GRADE", "COMPLIES_WITH", "HAS_DIMENSION"}
        for ann in gold:
            for rel in ann.get("relations", []):
                assert rel["type"] in valid_types, f"Invalid relation {rel['type']} in {ann.get('doc_id','?')}"

    def test_gold_diverse_types(self):
        with open("data/real_rfqs/annotations/gold_annotations.json") as f:
            gold = json.load(f)
        sources = {ann.get("source_file", "") for ann in gold}
        building = any("building" in s or "RFQ5521" in s or "RFQ6053" in s or "RFQ1697" in s or "RFQ8237" in s for s in sources)
        road = any("road" in s for s in sources)
        electrical = any("electrical" in s for s in sources)
        plumbing = any("plumbing" in s for s in sources)
        assert building, "No building-type gold annotations"
        assert road, "No road-type gold annotations"
        assert electrical, "No electrical-type gold annotations"
        assert plumbing, "No plumbing-type gold annotations"


class TestPDFCount:
    """Tests for PDF collection count."""

    def test_50_plus_pdfs_total(self):
        raw_dir = Path("data/real_rfqs/raw")
        pdfs = list(raw_dir.rglob("*.pdf"))
        pdfs = [p for p in pdfs if p.name not in ("manifest.csv", "manifest.json", "metadata.json")]
        assert len(pdfs) >= 50, f"Only {len(pdfs)} PDFs found, need ≥50"

    def test_4_real_pdfs(self):
        with open("data/real_rfqs/annotations/manifest.csv") as f:
            rows = list(csv.DictReader(f))
        real_count = sum(1 for r in rows if r.get("is_real") == "True")
        assert real_count == 4, f"Expected 4 real PDFs, found {real_count}"

    def test_synthetic_archived(self):
        synth_dir = Path("data/real_rfqs/raw/synthetic_archive")
        if synth_dir.exists():
            synth_pdfs = list(synth_dir.glob("*.pdf"))
            assert len(synth_pdfs) >= 100, f"Only {len(synth_pdfs)} synthetic PDFs archived"


class TestRealWorldMetrics:
    """Tests for real-world evaluation results."""

    def test_real_world_metrics_exist(self):
        metrics_path = Path("results/real_world_metrics_v2.json")
        assert metrics_path.exists(), f"metrics not found at {metrics_path}"

    def test_real_f1_recorded(self):
        with open("results/real_world_metrics_v2.json") as f:
            metrics = json.load(f)
        f1_key = "real_test_f1" if "real_test_f1" in metrics else "micro_f1"
        assert f1_key in metrics, f"{f1_key} not in metrics"
        assert metrics[f1_key] > 0, f"{f1_key} must be positive"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
