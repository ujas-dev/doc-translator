import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.documents.models import DocumentJob


@pytest.mark.django_db
class TestDocumentJobModel:
    def test_job_creation(self, sample_txt_file):
        job = DocumentJob.objects.create(
            source_file=sample_txt_file,
            source_language="en",
            target_language="hi",
        )
        assert job.pk is not None
        assert job.status == "queued"

    def test_job_str(self, sample_txt_file):
        job = DocumentJob.objects.create(source_file=sample_txt_file, status="completed")
        assert "completed" in str(job)

    def test_job_default_status(self, sample_txt_file):
        job = DocumentJob.objects.create(source_file=sample_txt_file)
        assert job.status == "queued"

    def test_job_status_choices(self, sample_txt_file):
        for status in ("queued", "processing", "translated", "converted", "completed", "failed"):
            job = DocumentJob.objects.create(source_file=sample_txt_file, status=status)
            assert job.status == status
            job.delete()

    def test_job_pages_default(self, sample_txt_file):
        job = DocumentJob.objects.create(source_file=sample_txt_file)
        assert job.pages == 0

    def test_job_error_message_blank(self, sample_txt_file):
        job = DocumentJob.objects.create(source_file=sample_txt_file)
        assert job.error_message == ""

    def test_job_output_file_nullable(self, sample_txt_file):
        job = DocumentJob.objects.create(source_file=sample_txt_file)
        assert not job.output_file.name

    def test_job_source_format(self, sample_txt_file):
        job = DocumentJob.objects.create(
            source_file=sample_txt_file, source_format="txt"
        )
        assert job.source_format == "txt"

    def test_job_user_field(self, sample_txt_file, user):
        job = DocumentJob.objects.create(
            source_file=sample_txt_file,
            user=user,
        )
        assert job.user == user

    def test_job_user_nullable(self, sample_txt_file):
        job = DocumentJob.objects.create(source_file=sample_txt_file)
        assert job.user is None

    def test_job_page_count_default(self, sample_txt_file):
        job = DocumentJob.objects.create(source_file=sample_txt_file)
        assert job.page_count == 0

    def test_job_character_count_default(self, sample_txt_file):
        job = DocumentJob.objects.create(source_file=sample_txt_file)
        assert job.character_count == 0


@pytest.mark.django_db
class TestDocumentJobAPI:
    def test_list_jobs(self, authenticated_client, sample_txt_file):
        DocumentJob.objects.create(source_file=sample_txt_file, status="completed")
        resp = authenticated_client.get("/api/jobs/")
        assert resp.status_code == 200

    def test_create_job(self, authenticated_client, sample_txt_file):
        resp = authenticated_client.post(
            "/api/jobs/",
            {
                "source_file": sample_txt_file,
                "source_language": "en",
                "target_language": "hi",
            },
            format="multipart",
        )
        assert resp.status_code == 201

    def test_retrieve_job(self, authenticated_client, sample_txt_file):
        job = DocumentJob.objects.create(source_file=sample_txt_file, status="completed")
        resp = authenticated_client.get(f"/api/jobs/{job.pk}/")
        assert resp.status_code == 200

    def test_job_detail_page(self, authenticated_client, sample_txt_file):
        job = DocumentJob.objects.create(source_file=sample_txt_file, status="completed")
        resp = authenticated_client.get(f"/api/jobs/{job.pk}/detail/")
        assert resp.status_code == 200


@pytest.mark.django_db
class TestDocumentJobDownload:
    def test_download_not_ready(self, authenticated_client, sample_txt_file):
        job = DocumentJob.objects.create(source_file=sample_txt_file, status="processing")
        resp = authenticated_client.get(f"/api/jobs/{job.pk}/download/")
        assert resp.status_code in (409, 404)

    def test_download_nonexistent_job(self, authenticated_client):
        resp = authenticated_client.get("/api/jobs/99999/download/")
        assert resp.status_code == 404


@pytest.mark.django_db
class TestDocumentJobPreview:
    def test_preview_source(self, authenticated_client, sample_txt_file):
        job = DocumentJob.objects.create(source_file=sample_txt_file, status="completed")
        resp = authenticated_client.get(f"/api/jobs/{job.pk}/preview/?type=source")
        assert resp.status_code == 200

    def test_preview_output_not_ready(self, authenticated_client, sample_txt_file):
        job = DocumentJob.objects.create(source_file=sample_txt_file, status="queued")
        resp = authenticated_client.get(f"/api/jobs/{job.pk}/preview/?type=output")
        assert resp.status_code == 404

    def test_preview_default_type(self, authenticated_client, sample_txt_file):
        job = DocumentJob.objects.create(source_file=sample_txt_file, status="completed")
        resp = authenticated_client.get(f"/api/jobs/{job.pk}/preview/")
        assert resp.status_code == 200


@pytest.mark.django_db
class TestWebhookField:
    def test_webhook_url_default_empty(self, sample_txt_file):
        job = DocumentJob.objects.create(source_file=sample_txt_file)
        assert job.webhook_url == ''

    def test_webhook_url_stored(self, sample_txt_file):
        job = DocumentJob.objects.create(
            source_file=sample_txt_file,
            webhook_url='https://example.com/hook',
        )
        assert job.webhook_url == 'https://example.com/hook'


@pytest.mark.django_db
class TestWebhookDispatch:
    def test_fire_webhook_on_completion(self, sample_txt_file, monkeypatch):
        from apps.documents.tasks import _fire_webhook
        import apps.documents.tasks as tasks_mod

        called_with = {}

        def mock_post(url, json, timeout):
            called_with['url'] = url
            called_with['payload'] = json

        monkeypatch.setattr(tasks_mod.requests, 'post', mock_post)

        job = DocumentJob.objects.create(
            source_file=sample_txt_file,
            status='completed',
            webhook_url='https://example.com/hook',
        )
        _fire_webhook(job, 'completed')

        assert called_with['url'] == 'https://example.com/hook'
        assert called_with['payload']['event'] == 'completed'
        assert called_with['payload']['job_id'] == job.pk
        assert called_with['payload']['status'] == 'completed'

    def test_fire_webhook_on_failure(self, sample_txt_file, monkeypatch):
        from apps.documents.tasks import _fire_webhook

        called_with = {}

        def mock_post(url, json, timeout):
            called_with['payload'] = json

        monkeypatch.setattr(
            __import__('apps.documents.tasks', fromlist=['requests']).requests,
            'post', mock_post,
        )

        job = DocumentJob.objects.create(
            source_file=sample_txt_file,
            status='failed',
            error_message='Something broke',
            webhook_url='https://example.com/hook',
        )
        _fire_webhook(job, 'failed')

        assert called_with['payload']['event'] == 'failed'
        assert called_with['payload']['error'] == 'Something broke'

    def test_fire_webhook_skipped_when_no_url(self, sample_txt_file, monkeypatch):
        from apps.documents.tasks import _fire_webhook

        call_count = [0]

        def mock_post(url, json, timeout):
            call_count[0] += 1

        monkeypatch.setattr(
            __import__('apps.documents.tasks', fromlist=['requests']).requests,
            'post', mock_post,
        )

        job = DocumentJob.objects.create(
            source_file=sample_txt_file,
            status='completed',
            webhook_url='',
        )
        _fire_webhook(job, 'completed')

        assert call_count[0] == 0

    def test_fire_webhook_handles_request_failure(self, sample_txt_file, monkeypatch):
        from apps.documents.tasks import _fire_webhook

        def mock_post(url, json, timeout):
            raise ConnectionError("Network error")

        monkeypatch.setattr(
            __import__('apps.documents.tasks', fromlist=['requests']).requests,
            'post', mock_post,
        )

        job = DocumentJob.objects.create(
            source_file=sample_txt_file,
            status='completed',
            webhook_url='https://example.com/hook',
        )
        _fire_webhook(job, 'completed')
