"""Integration tests for API endpoints."""

import pytest

pytest.importorskip("fastapi")


class TestAPI:
    def test_health_endpoint(self):
        from fastapi.testclient import TestClient
        from src.api.main import app

        client = TestClient(app)
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_root_endpoint(self):
        from fastapi.testclient import TestClient
        from src.api.main import app

        client = TestClient(app)
        response = client.get("/")
        assert response.status_code == 200
        assert "message" in response.json()

    def test_extract_endpoint_with_text(self):
        from fastapi.testclient import TestClient
        from src.api.main import app

        client = TestClient(app)
        response = client.post(
            "/api/extract", json={"text": "Supply M20 concrete 150 cu.m", "project_name": "Test Project"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "extraction_id" in data

    def test_extract_endpoint_empty_text(self):
        from fastapi.testclient import TestClient
        from src.api.main import app

        client = TestClient(app)
        response = client.post("/api/extract", json={"text": "", "project_name": "Empty Test"})
        assert response.status_code == 200

    def test_boq_endpoint_not_found(self):
        from fastapi.testclient import TestClient
        from src.api.main import app

        client = TestClient(app)
        response = client.get("/api/boq/nonexistent-id-12345")
        assert response.status_code in [200, 404]


class TestAPISchemas:
    def test_upload_response_schema(self):
        from datetime import datetime

        from src.api.schemas import UploadResponse
        from src.domain.models import ExtractionMetadata, ExtractionResult

        result = ExtractionResult(
            doc_id="test-123",
            project_name="Test",
            extraction_date=datetime.now(),
            source_file="test.pdf",
            entities=[],
            boq_items=[],
            metadata=ExtractionMetadata(
                total_items=0,
                avg_confidence=0.0,
                processing_time_sec=0.0,
                pages_processed=0,
            ),
        )
        response = UploadResponse(extraction_id="abc", result=result)
        assert response.extraction_id == "abc"
        assert response.result.doc_id == "test-123"

    def test_extract_request_schema(self):
        from src.api.schemas import ExtractRequest

        req = ExtractRequest(text="test", project_name="Test")
        assert req.text == "test"
        assert req.project_name == "Test"

    def test_health_response_schema(self):
        from src.api.schemas import HealthResponse

        resp = HealthResponse(status="ok", model_loaded=True)
        assert resp.status == "ok"
        assert resp.model_loaded is True
