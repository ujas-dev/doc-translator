import pytest
from apps.documents.models import DocumentJob


@pytest.mark.django_db
class TestJobStatusPartial:
    def test_status_partial_completed(self, authenticated_client, sample_txt_file):
        job = DocumentJob.objects.create(
            source_file=sample_txt_file,
            source_language='en',
            target_language='hi',
            status='completed',
        )
        resp = authenticated_client.get(f'/api/jobs/{job.pk}/status-partial/')
        assert resp.status_code == 200

    def test_status_partial_queued(self, authenticated_client, sample_txt_file):
        job = DocumentJob.objects.create(
            source_file=sample_txt_file,
            source_language='en',
            target_language='hi',
            status='queued',
        )
        resp = authenticated_client.get(f'/api/jobs/{job.pk}/status-partial/')
        assert resp.status_code == 200

    def test_status_partial_not_found(self, authenticated_client):
        resp = authenticated_client.get('/api/jobs/99999/status-partial/')
        assert resp.status_code == 404


@pytest.mark.django_db
class TestJobPreviewPartial:
    def test_preview_partial_completed(self, authenticated_client, sample_txt_file):
        job = DocumentJob.objects.create(
            source_file=sample_txt_file,
            source_language='en',
            target_language='hi',
            status='completed',
        )
        resp = authenticated_client.get(f'/api/jobs/{job.pk}/preview-partial/')
        assert resp.status_code == 200

    def test_preview_partial_queued(self, authenticated_client, sample_txt_file):
        job = DocumentJob.objects.create(
            source_file=sample_txt_file,
            source_language='en',
            target_language='hi',
            status='queued',
        )
        resp = authenticated_client.get(f'/api/jobs/{job.pk}/preview-partial/')
        assert resp.status_code == 200

    def test_preview_partial_not_found(self, authenticated_client):
        resp = authenticated_client.get('/api/jobs/99999/preview-partial/')
        assert resp.status_code == 404
