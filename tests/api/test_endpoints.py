import pytest
from django.test import Client

from apps.documents.models import DocumentJob


@pytest.mark.django_db
class TestAPIJobEndpoints:
    def test_list_jobs_unauthenticated(self, client):
        resp = client.get("/api/jobs/")
        assert resp.status_code == 200

    def test_create_job_unauthenticated(self, client, sample_txt_file):
        resp = client.post(
            "/api/jobs/",
            {
                "source_file": sample_txt_file,
                "source_language": "en",
                "target_language": "hi",
            },
            format="multipart",
        )
        assert resp.status_code == 201

    def test_retrieve_job(self, client, sample_txt_file):
        job = DocumentJob.objects.create(source_file=sample_txt_file, status="completed")
        resp = client.get(f"/api/jobs/{job.pk}/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "completed"

    def test_retrieve_nonexistent_job(self, client):
        resp = client.get("/api/jobs/99999/")
        assert resp.status_code == 404


@pytest.mark.django_db
class TestAPIRateLimiting:
    def test_api_key_in_header(self, authenticated_client, api_key):
        resp = authenticated_client.get(
            "/api/jobs/",
            HTTP_X_API_KEY=api_key.key,
        )
        assert resp.status_code == 200


@pytest.mark.django_db
class TestAPISchemaEndpoints:
    def test_schema_endpoint(self, client):
        resp = client.get("/api/schema/")
        assert resp.status_code == 200

    def test_swagger_ui(self, client):
        resp = client.get("/api/docs/")
        assert resp.status_code == 200

    def test_redoc(self, client):
        resp = client.get("/api/redoc/")
        assert resp.status_code == 200
