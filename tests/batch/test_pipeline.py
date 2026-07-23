import io
import os
import tempfile
import zipfile
import pytest
from unittest.mock import patch, MagicMock
from django.core.files.base import ContentFile

from apps.batch.models import BatchJob, BatchFile
from apps.batch.tasks import process_batch_file, complete_batch, process_batch
from apps.batch.services import create_batch_zip


@pytest.fixture
def batch_with_files(user):
    batch = BatchJob.objects.create(
        user=user,
        name='Pipeline test',
        status='processing',
        source_language='en',
        target_language='hi',
        style_mode='fluid',
        bilingual=False,
        total_files=2,
        completed_files=0,
        failed_files=0,
    )
    bf1 = BatchFile(batch=batch, original_name='file1.txt')
    bf1.file.save('file1.txt', ContentFile(b'File 1 content'))
    bf1.save()

    bf2 = BatchFile(batch=batch, original_name='file2.txt')
    bf2.file.save('file2.txt', ContentFile(b'File 2 content'))
    bf2.save()

    return batch, bf1, bf2


@pytest.mark.django_db
class TestProcessBatchFile:
    @patch('apps.documents.tasks.process_document')
    def test_process_batch_file_success(self, mock_process, batch_with_files):
        batch, bf1, bf2 = batch_with_files
        mock_process.delay = MagicMock()

        process_batch_file(bf1.pk)

        bf1.refresh_from_db()
        assert bf1.status == 'completed'
        assert bf1.job is not None
        batch.refresh_from_db()
        assert batch.completed_files == 1

    @patch('apps.documents.tasks.process_document')
    def test_process_batch_file_exception(self, mock_process, batch_with_files):
        batch, bf1, bf2 = batch_with_files
        mock_process.delay.side_effect = Exception("Unexpected error")

        process_batch_file(bf1.pk)

        bf1.refresh_from_db()
        assert bf1.status == 'failed'
        assert 'Unexpected error' in bf1.error_message
        batch.refresh_from_db()
        assert batch.failed_files == 1


@pytest.mark.django_db
class TestCompleteBatch:
    @patch('apps.batch.services.create_batch_zip')
    def test_complete_batch_success(self, mock_zip, batch_with_files):
        batch, bf1, bf2 = batch_with_files
        mock_zip.return_value = '/media/batch_outputs/batch_1_output.zip'

        complete_batch(batch.pk)

        batch.refresh_from_db()
        assert batch.status == 'completed'
        assert batch.output_zip is not None

    @patch('apps.batch.services.create_batch_zip')
    def test_complete_batch_exception(self, mock_zip, batch_with_files):
        batch, bf1, bf2 = batch_with_files
        mock_zip.side_effect = Exception("ZIP creation failed")

        complete_batch(batch.pk)

        batch.refresh_from_db()
        assert batch.status == 'failed'


@pytest.mark.django_db
class TestProcessBatch:
    @patch('apps.batch.tasks.chord')
    def test_process_batch_dispatches(self, mock_chord, batch_with_files):
        batch, bf1, bf2 = batch_with_files
        mock_chord.return_value = MagicMock(return_value=MagicMock(delay=MagicMock()))

        process_batch(batch.pk)

        batch.refresh_from_db()
        assert batch.status == 'processing'

    @patch('apps.batch.tasks.chord')
    def test_process_batch_exception(self, mock_chord, batch_with_files):
        batch, bf1, bf2 = batch_with_files
        mock_chord.side_effect = Exception("Chord error")

        process_batch(batch.pk)

        batch.refresh_from_db()
        assert batch.status == 'failed'


@pytest.mark.django_db
class TestCreateBatchZip:
    def test_creates_zip_with_completed_jobs(self, user):
        batch = BatchJob.objects.create(
            user=user, name='Zip test', status='completed',
            source_language='en', target_language='hi',
        )

        out_dir = os.path.join(tempfile.gettempdir(), 'test_outputs')
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, 'output1.txt')
        with open(out_path, 'w') as f:
            f.write("translated content")

        job = MagicMock()
        job.status = 'completed'
        job.output_file = MagicMock()
        job.output_file.path = out_path
        job.output_file.url = '/media/outputs/output1.txt'

        with patch('apps.documents.models.DocumentJob') as MockJob:
            MockJob.objects.filter.return_value = [job]
            zip_path = create_batch_zip(batch)

            assert os.path.exists(zip_path)
            with zipfile.ZipFile(zip_path) as zf:
                names = zf.namelist()
                assert len(names) == 1

            os.unlink(zip_path)

    def test_creates_empty_zip_when_no_completed(self, user):
        batch = BatchJob.objects.create(
            user=user, name='Empty zip', status='completed',
            source_language='en', target_language='hi',
        )

        with patch('apps.documents.models.DocumentJob') as MockJob:
            MockJob.objects.filter.return_value = []
            zip_path = create_batch_zip(batch)

            assert os.path.exists(zip_path)
            with zipfile.ZipFile(zip_path) as zf:
                assert len(zf.namelist()) == 0

            os.unlink(zip_path)
