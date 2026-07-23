import os
import pytest
from unittest.mock import patch, MagicMock
from django.core.files.base import ContentFile

from apps.documents.models import DocumentJob
from apps.documents.tasks import process_document, _fire_webhook, _run_qa_checks


@pytest.mark.django_db
class TestFireWebhook:
    def test_fire_webhook_on_completion(self, sample_txt_file, monkeypatch):
        called_with = {}

        def mock_post(url, json, timeout):
            called_with['url'] = url
            called_with['payload'] = json

        monkeypatch.setattr(
            'apps.documents.tasks.requests.post', mock_post,
        )

        job = DocumentJob.objects.create(
            source_file=sample_txt_file,
            status='completed',
            webhook_url='https://example.com/hook',
        )
        _fire_webhook(job, 'completed')

        assert called_with['url'] == 'https://example.com/hook'
        assert called_with['payload']['event'] == 'completed'
        assert called_with['payload']['job_id'] == job.pk

    def test_fire_webhook_on_failure(self, sample_txt_file, monkeypatch):
        called_with = {}

        def mock_post(url, json, timeout):
            called_with['payload'] = json

        monkeypatch.setattr(
            'apps.documents.tasks.requests.post', mock_post,
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
        call_count = [0]

        def mock_post(url, json, timeout):
            call_count[0] += 1

        monkeypatch.setattr(
            'apps.documents.tasks.requests.post', mock_post,
        )

        job = DocumentJob.objects.create(
            source_file=sample_txt_file,
            status='completed',
            webhook_url='',
        )
        _fire_webhook(job, 'completed')
        assert call_count[0] == 0

    def test_fire_webhook_handles_exception(self, sample_txt_file, monkeypatch):
        def mock_post(url, json, timeout):
            raise ConnectionError("Network error")

        monkeypatch.setattr(
            'apps.documents.tasks.requests.post', mock_post,
        )

        job = DocumentJob.objects.create(
            source_file=sample_txt_file,
            status='completed',
            webhook_url='https://example.com/hook',
        )
        _fire_webhook(job, 'completed')


@pytest.mark.django_db
class TestRunQAChecks:
    def test_run_qa_checks_creates_scores(self, sample_txt_file):
        job = DocumentJob.objects.create(
            source_file=sample_txt_file,
            status='completed',
        )
        _run_qa_checks(job, "Hello world", "Hola mundo")

        from apps.qa.models import QAScore, QARule
        scores = QAScore.objects.filter(job=job)
        assert scores.exists()
        assert scores.count() >= 3

        rules = QARule.objects.filter(scores__job=job).distinct()
        rule_names = [r.name for r in rules]
        assert 'Length Consistency' in rule_names

    def test_run_qa_checks_handles_empty_text(self, sample_txt_file):
        job = DocumentJob.objects.create(
            source_file=sample_txt_file,
            status='completed',
        )
        _run_qa_checks(job, "", "")

        from apps.qa.models import QAScore
        scores = QAScore.objects.filter(job=job)
        assert scores.exists()

    def test_run_qa_checks_handles_exception(self, sample_txt_file):
        job = DocumentJob.objects.create(
            source_file=sample_txt_file,
            status='completed',
        )
        with patch('apps.qa.services.QAScoringService.run_all_checks', side_effect=Exception("Service down")):
            _run_qa_checks(job, "Hello", "Hola")
        from apps.qa.models import QAScore
        assert QAScore.objects.filter(job=job).count() == 0


@pytest.mark.django_db
class TestProcessDocumentTask:
    @patch('apps.documents.parsers.write_output')
    @patch('apps.translation.services.translate_document')
    @patch('apps.documents.parsers.extract_text')
    def test_process_document_sets_processing(self, mock_extract, mock_translate, mock_write, sample_txt_file):
        mock_extract.return_value = ("Hello world", 1)
        mock_translate.return_value = "Translated text"
        mock_write.return_value = None

        job = DocumentJob.objects.create(
            source_file=sample_txt_file,
            source_language='en',
            target_language='hi',
            status='queued',
        )
        process_document(job.pk)

        job.refresh_from_db()
        assert job.status == 'completed'

    @patch('apps.documents.parsers.extract_text')
    def test_process_document_sets_failed_on_error(self, mock_extract, sample_txt_file):
        mock_extract.side_effect = Exception("Parse error")

        job = DocumentJob.objects.create(
            source_file=sample_txt_file,
            source_language='en',
            target_language='hi',
            status='queued',
        )

        with pytest.raises(Exception):
            process_document(job.pk)

        job.refresh_from_db()
        assert job.status == 'failed'
        assert 'Parse error' in job.error_message

    @patch('apps.documents.parsers.write_output')
    @patch('apps.translation.services.translate_document')
    @patch('apps.documents.parsers.extract_text')
    def test_process_document_sets_pages(self, mock_extract, mock_translate, mock_write, sample_txt_file):
        mock_extract.return_value = ("Hello world test", 3)
        mock_translate.return_value = "नमस्ते दुनिया परीक्षा"
        mock_write.return_value = None

        job = DocumentJob.objects.create(
            source_file=sample_txt_file,
            source_language='en',
            target_language='hi',
            status='queued',
        )
        process_document(job.pk)

        job.refresh_from_db()
        assert job.status == 'completed'
        assert job.pages == 3

    @patch('apps.documents.parsers.write_output')
    @patch('apps.translation.services.translate_document')
    @patch('apps.documents.parsers.extract_text')
    def test_bilingual_txt_output(self, mock_extract, mock_translate, mock_write, sample_txt_file, settings):
        mock_extract.return_value = ("Hello world", 1)
        mock_translate.return_value = "नमस्ते दुनिया"

        os.makedirs(os.path.join(settings.MEDIA_ROOT, 'outputs'), exist_ok=True)

        job = DocumentJob.objects.create(
            source_file=sample_txt_file,
            source_language='en',
            target_language='hi',
            status='queued',
            bilingual=True,
            target_format='txt',
        )
        process_document(job.pk)

        job.refresh_from_db()
        assert job.status == 'completed'
        assert job.output_file

    def test_process_document_source_not_found(self, sample_txt_file, monkeypatch):
        monkeypatch.setattr('os.path.exists', lambda p: False)

        job = DocumentJob.objects.create(
            source_file=sample_txt_file,
            source_language='en',
            target_language='hi',
            status='queued',
        )

        with pytest.raises(FileNotFoundError):
            process_document(job.pk)

        job.refresh_from_db()
        assert job.status == 'failed'

    @patch('apps.documents.parsers.write_pdf_layout')
    @patch('apps.translation.services.translate_text')
    def test_pdf_layout_path(self, mock_translate, mock_pdf, sample_txt_file, settings):
        mock_translate.return_value = "translated"
        mock_pdf.return_value = {'pages': 5}

        os.makedirs(os.path.join(settings.MEDIA_ROOT, 'outputs'), exist_ok=True)

        src_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')
        os.makedirs(src_dir, exist_ok=True)
        src_path = os.path.join(src_dir, 'layout_test.pdf')
        with open(src_path, 'w') as f:
            f.write("fake pdf content")

        job = DocumentJob.objects.create(
            source_file='uploads/layout_test.pdf',
            source_language='en',
            target_language='hi',
            status='queued',
            target_format='pdf',
        )

        process_document(job.pk)

        job.refresh_from_db()
        assert job.status == 'completed'
        mock_pdf.assert_called_once()
        assert job.output_file

    @patch('apps.documents.parsers.write_docx_layout')
    @patch('apps.translation.services.translate_text')
    def test_docx_layout_path(self, mock_translate, mock_docx, sample_txt_file, settings):
        mock_translate.return_value = "translated"
        mock_docx.return_value = {'pages': 1}

        os.makedirs(os.path.join(settings.MEDIA_ROOT, 'outputs'), exist_ok=True)

        src_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')
        os.makedirs(src_dir, exist_ok=True)
        src_path = os.path.join(src_dir, 'layout_test.docx')
        with open(src_path, 'w') as f:
            f.write("fake docx content")

        job = DocumentJob.objects.create(
            source_file='uploads/layout_test.docx',
            source_language='en',
            target_language='hi',
            status='queued',
            target_format='docx',
        )

        process_document(job.pk)

        job.refresh_from_db()
        assert job.status == 'completed'
        mock_docx.assert_called_once()
        assert job.output_file
