import pytest
from unittest.mock import patch
from apps.batch.models import BatchJob
from apps.documents.models import DocumentJob


@pytest.mark.django_db
class TestBatchViews:
    def test_batch_list(self, authenticated_client):
        resp = authenticated_client.get('/batch/')
        assert resp.status_code == 200

    def test_batch_list_requires_login(self, client):
        resp = client.get('/batch/')
        assert resp.status_code == 302

    def test_batch_upload_page(self, authenticated_client):
        resp = authenticated_client.get('/batch/upload/')
        assert resp.status_code == 200

    def test_batch_detail(self, authenticated_client, user):
        batch = BatchJob.objects.create(
            user=user,
            name='Test batch',
            status='completed',
            total_files=2,
        )
        resp = authenticated_client.get(f'/batch/{batch.pk}/')
        assert resp.status_code == 200

    def test_batch_detail_not_found(self, authenticated_client):
        resp = authenticated_client.get('/batch/99999/')
        assert resp.status_code == 404

    def test_batch_status(self, authenticated_client, user):
        batch = BatchJob.objects.create(
            user=user,
            name='Status test',
            status='processing',
            total_files=5,
            completed_files=2,
            failed_files=0,
        )
        resp = authenticated_client.get(f'/batch/{batch.pk}/status/')
        assert resp.status_code == 200
        data = resp.json()
        assert data['status'] == 'processing'
        assert data['total_files'] == 5
        assert data['completed_files'] == 2

    def test_batch_download_not_ready(self, authenticated_client, user):
        batch = BatchJob.objects.create(
            user=user,
            name='Not ready',
            status='processing',
        )
        resp = authenticated_client.post(f'/batch/{batch.pk}/download/')
        assert resp.status_code == 409

    def test_batch_detail_other_user(self, authenticated_client, pro_user):
        batch = BatchJob.objects.create(
            user=pro_user,
            name='Other users batch',
            status='completed',
        )
        resp = authenticated_client.get(f'/batch/{batch.pk}/')
        assert resp.status_code == 404


@pytest.mark.django_db
class TestBatchUploadPost:
    @patch('apps.batch.tasks.process_batch')
    def test_upload_valid_zip(self, mock_process, authenticated_client):
        import io, zipfile
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zf:
            zf.writestr('file1.txt', 'Hello')
            zf.writestr('file2.txt', 'World')
        zip_buffer.seek(0)

        from django.core.files.uploadedfile import SimpleUploadedFile
        zip_file = SimpleUploadedFile('test.zip', zip_buffer.read(), content_type='application/zip')

        resp = authenticated_client.post('/batch/upload/', {
            'zip_file': zip_file,
            'source_language': 'en',
            'target_language': 'hi',
        })
        assert resp.status_code == 302

        batch = BatchJob.objects.latest('pk')
        assert batch.source_language == 'en'
        assert batch.target_language == 'hi'
        assert batch.total_files == 2

    def test_upload_non_zip_rejected(self, authenticated_client):
        from django.core.files.uploadedfile import SimpleUploadedFile
        bad_file = SimpleUploadedFile('test.txt', b'content', content_type='text/plain')
        resp = authenticated_client.post('/batch/upload/', {'zip_file': bad_file})
        assert resp.status_code == 400

    def test_upload_no_file(self, authenticated_client):
        resp = authenticated_client.post('/batch/upload/', {})
        assert resp.status_code == 400
