import io
import os
import zipfile
import pytest
from unittest.mock import patch, MagicMock

from apps.batch.models import BatchJob, BatchFile


@pytest.mark.django_db
class TestBatchTaskHelpers:
    def test_extract_zip_to_files_basic(self):
        from apps.batch.services import extract_zip_to_files

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zf:
            zf.writestr('test.txt', 'Hello')
            zf.writestr('doc.pdf', 'PDF content')

        files = extract_zip_to_files(zip_buffer.getvalue())
        assert len(files) == 2
        names = [f['name'] for f in files]
        assert 'test.txt' in names
        assert 'doc.pdf' in names

    def test_extract_zip_skips_directories(self):
        from apps.batch.services import extract_zip_to_files

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zf:
            zf.writestr('folder/', '')
            zf.writestr('folder/file.txt', 'content')

        files = extract_zip_to_files(zip_buffer.getvalue())
        assert len(files) == 1

    def test_extract_zip_filters_unsupported(self):
        from apps.batch.services import extract_zip_to_files

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zf:
            zf.writestr('script.exe', 'binary')
            zf.writestr('data.txt', 'text')

        files = extract_zip_to_files(zip_buffer.getvalue())
        assert len(files) == 1
        assert files[0]['name'] == 'data.txt'

    def test_batch_job_progress_percent(self):
        batch = BatchJob(total_files=10, completed_files=5)
        assert batch.progress_percent == 50

    def test_batch_job_progress_zero(self):
        batch = BatchJob(total_files=0, completed_files=0)
        assert batch.progress_percent == 0

    def test_batch_job_progress_full(self):
        batch = BatchJob(total_files=5, completed_files=5)
        assert batch.progress_percent == 100
