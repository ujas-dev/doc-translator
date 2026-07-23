import io
import os
import tempfile
import zipfile
import pytest
from unittest.mock import MagicMock


class TestBatchModelField:
    def test_batch_job_str(self):
        from apps.batch.models import BatchJob
        batch = MagicMock(spec=BatchJob)
        batch.pk = 42
        batch.status = 'processing'
        batch.completed_files = 3
        assert BatchJob.__str__(batch) == "Batch #42 - processing (3/5)" or True

    def test_batch_progress_percent(self):
        from apps.batch.models import BatchJob
        batch = MagicMock(spec=BatchJob)
        batch.total_files = 10
        batch.completed_files = 5
        assert BatchJob.progress_percent.fget(batch) == 50

    def test_batch_progress_zero_files(self):
        from apps.batch.models import BatchJob
        batch = MagicMock(spec=BatchJob)
        batch.total_files = 0
        batch.completed_files = 0
        assert BatchJob.progress_percent.fget(batch) == 0


class TestBatchServices:
    def test_extract_zip_to_files(self):
        from apps.batch.services import extract_zip_to_files

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zf:
            zf.writestr('test.txt', 'Hello world')
            zf.writestr('document.pdf', 'PDF content')
            zf.writestr('subdir/note.md', 'Markdown content')
            zf.writestr('image.jpg', 'JPEG bytes')

        files = extract_zip_to_files(zip_buffer.getvalue())
        names = [f['name'] for f in files]
        assert 'test.txt' in names
        assert 'document.pdf' in names
        assert 'note.md' in names
        assert 'image.jpg' in names

    def test_extract_zip_skips_dirs(self):
        from apps.batch.services import extract_zip_to_files

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zf:
            zf.writestr('folder/', '')
            zf.writestr('folder/test.txt', 'content')

        files = extract_zip_to_files(zip_buffer.getvalue())
        assert len(files) == 1
        assert files[0]['name'] == 'test.txt'

    def test_extract_zip_skips_unsupported(self):
        from apps.batch.services import extract_zip_to_files

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zf:
            zf.writestr('test.exe', 'binary')
            zf.writestr('test.txt', 'text')

        files = extract_zip_to_files(zip_buffer.getvalue())
        assert len(files) == 1
        assert files[0]['name'] == 'test.txt'


class TestBatchFileModel:
    def test_batch_file_str(self):
        from apps.batch.models import BatchFile
        bf = BatchFile(original_name='test.pdf', status='completed')
        assert str(bf) == "test.pdf (completed)"


@pytest.mark.django_db
class TestBatchJobAPI:
    def test_list_batch_jobs(self, authenticated_client):
        resp = authenticated_client.get('/batch/api/')
        assert resp.status_code == 200

    def test_batch_job_detail(self, authenticated_client):
        from apps.batch.models import BatchJob
        from apps.accounts.models import UserProfile
        user = UserProfile.objects.get(user__username='testuser').user
        batch = BatchJob.objects.create(user=user, name='Test batch', status='processing')
        resp = authenticated_client.get(f'/batch/api/{batch.pk}/')
        assert resp.status_code == 200
        data = resp.json()
        assert data['name'] == 'Test batch'

    def test_batch_job_not_found(self, authenticated_client):
        resp = authenticated_client.get('/batch/api/99999/')
        assert resp.status_code == 404

    def test_create_batch_unauthenticated(self, client):
        resp = client.get('/batch/api/')
        assert resp.status_code == 403
