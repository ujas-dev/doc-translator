import os
import tempfile
import pytest
from unittest.mock import MagicMock
from django.core.files.base import ContentFile
from django.conf import settings

from apps.documents.models import DocumentJob


@pytest.mark.django_db
class TestDownloadOutput:
    def test_download_completed_job(self, authenticated_client, user):
        job = DocumentJob.objects.create(
            user=user,
            source_language='en',
            target_language='hi',
            status='completed',
        )
        out_dir = os.path.join(settings.MEDIA_ROOT, 'outputs')
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, f'test_output_{job.pk}.txt')
        with open(out_path, 'w') as f:
            f.write("translated text")

        job.output_file = f'outputs/test_output_{job.pk}.txt'
        job.save(update_fields=['output_file'])

        resp = authenticated_client.get(f'/api/jobs/{job.pk}/download/')
        assert resp.status_code == 200

    def test_download_not_ready(self, authenticated_client, user):
        job = DocumentJob.objects.create(
            user=user,
            source_language='en',
            target_language='hi',
            status='processing',
        )
        resp = authenticated_client.get(f'/api/jobs/{job.pk}/download/')
        assert resp.status_code == 409
        assert resp.json()['error'] == 'File not ready yet'

    def test_download_not_found(self, authenticated_client):
        resp = authenticated_client.get('/api/jobs/99999/download/')
        assert resp.status_code == 404

    def test_download_no_output_file(self, authenticated_client, user):
        job = DocumentJob.objects.create(
            user=user,
            source_language='en',
            target_language='hi',
            status='completed',
            output_file=None,
        )
        resp = authenticated_client.get(f'/api/jobs/{job.pk}/download/')
        assert resp.status_code == 409


@pytest.mark.django_db
class TestJobPreview:
    def test_preview_source_file(self, authenticated_client, user, sample_txt_file):
        job = DocumentJob.objects.create(
            user=user,
            source_file=sample_txt_file,
            source_language='en',
            target_language='hi',
            status='queued',
        )
        resp = authenticated_client.get(f'/api/jobs/{job.pk}/preview/?type=source')
        assert resp.status_code == 200

    def test_preview_output_file(self, authenticated_client, user):
        job = DocumentJob.objects.create(
            user=user,
            source_language='en',
            target_language='hi',
            status='completed',
        )
        out_dir = os.path.join(settings.MEDIA_ROOT, 'outputs')
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, f'preview_output_{job.pk}.txt')
        with open(out_path, 'w') as f:
            f.write("preview content")

        job.output_file = f'outputs/preview_output_{job.pk}.txt'
        job.save(update_fields=['output_file'])

        resp = authenticated_client.get(f'/api/jobs/{job.pk}/preview/?type=output')
        assert resp.status_code == 200

    def test_preview_output_not_ready(self, authenticated_client, user):
        job = DocumentJob.objects.create(
            user=user,
            source_language='en',
            target_language='hi',
            status='processing',
        )
        resp = authenticated_client.get(f'/api/jobs/{job.pk}/preview/?type=output')
        assert resp.status_code == 404

    def test_preview_job_not_found(self, authenticated_client):
        resp = authenticated_client.get('/api/jobs/99999/preview/')
        assert resp.status_code == 404

    def test_preview_default_type_is_source(self, authenticated_client, user, sample_txt_file):
        job = DocumentJob.objects.create(
            user=user,
            source_file=sample_txt_file,
            source_language='en',
            target_language='hi',
            status='queued',
        )
        resp = authenticated_client.get(f'/api/jobs/{job.pk}/preview/')
        assert resp.status_code == 200


@pytest.mark.django_db
class TestJobDetailTemplate:
    def test_job_detail_page(self, authenticated_client, user, sample_txt_file):
        job = DocumentJob.objects.create(
            user=user,
            source_file=sample_txt_file,
            source_language='en',
            target_language='hi',
            status='completed',
        )
        resp = authenticated_client.get(f'/api/jobs/{job.pk}/detail/')
        assert resp.status_code == 200

    def test_job_detail_not_found(self, authenticated_client):
        resp = authenticated_client.get('/api/jobs/99999/detail/')
        assert resp.status_code == 404
