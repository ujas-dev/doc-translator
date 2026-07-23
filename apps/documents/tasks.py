import structlog
import os
import requests
from celery import shared_task
from django.conf import settings

logger = structlog.get_logger(__name__)


def _fire_webhook(job, event_type):
    if not job.webhook_url:
        return
    payload = {
        'event': event_type,
        'job_id': job.pk,
        'status': job.status,
        'output_url': job.output_file.url if job.output_file else None,
        'error': job.error_message or None,
    }
    try:
        requests.post(job.webhook_url, json=payload, timeout=10)
    except Exception as e:
        logger.warning("Webhook failed for job %d: %s", job.pk, e)


def _run_qa_checks(job, source_text, translated_text):
    try:
        from apps.qa.models import QAScore, QARule
        from apps.qa.services import QAScoringService

        results = QAScoringService.run_all_checks(source_text, translated_text)

        rules_map = {
            'length_consistency': 'Length Consistency',
            'term_consistency': 'Term Consistency',
            'untranslated': 'Untranslated Text',
            'empty_segments': 'Empty Segments',
        }

        for key, rule_name in rules_map.items():
            if key not in results:
                continue
            rule, _ = QARule.objects.get_or_create(
                name=rule_name,
                defaults={'rule_type': key, 'severity': 'major', 'weight': 1.0},
            )
            QAScore.objects.update_or_create(
                job=job,
                rule=rule,
                defaults={
                    'score': results[key]['score'],
                    'details': results[key].get('details', {}),
                },
            )
    except Exception as e:
        logger.warning("QA checks failed for job %d: %s", job.pk, e)


@shared_task(bind=True)
def process_document(self, job_id: int):
    from apps.documents.models import DocumentJob
    from apps.documents.parsers import extract_text, write_output, write_pdf_layout, write_docx_layout
    from apps.translation.services import translate_text, translate_document

    job = DocumentJob.objects.get(pk=job_id)
    try:
        job.status = 'processing'
        job.save(update_fields=['status'])

        file_path = job.source_file.path
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Source file not found: {file_path}")

        src_ext = os.path.splitext(file_path)[1].lstrip('.')
        out_fmt = job.target_format or src_ext
        style = job.style_mode or 'fluid'
        bilingual = job.bilingual

        use_pdf_layout = (
            out_fmt == 'pdf'
            and src_ext == 'pdf'
            and os.path.exists(file_path)
        )
        use_docx_layout = (
            out_fmt == 'docx'
            and src_ext == 'docx'
            and os.path.exists(file_path)
        )

        source_text = ''

        if use_pdf_layout:
            def translate_fn(text, source, target):
                return translate_text(text, source=source, target=target, style=style)

            base_name = os.path.splitext(os.path.basename(file_path))[0]
            suffix = "_bilingual" if bilingual else ""
            out_filename = f"{base_name}_{job.target_language}{suffix}.pdf"
            out_path = os.path.join(settings.MEDIA_ROOT, 'outputs', out_filename)

            if bilingual:
                from apps.documents.pdf_bilingual import create_bilingual_pdf
                stats = create_bilingual_pdf(
                    input_path=file_path,
                    output_path=out_path,
                    translate_fn=translate_fn,
                    source_lang=job.source_language,
                    target_lang=job.target_language,
                )
            else:
                stats = write_pdf_layout(
                    input_path=file_path,
                    output_path=out_path,
                    translate_fn=translate_fn,
                    source_lang=job.source_language,
                    target_lang=job.target_language,
                )
            job.pages = stats.get("pages", 0)
        elif use_docx_layout:
            def translate_fn(text, source, target):
                return translate_text(text, source=source, target=target, style=style)

            base_name = os.path.splitext(os.path.basename(file_path))[0]
            suffix = "_bilingual" if bilingual else ""
            out_filename = f"{base_name}_{job.target_language}{suffix}.docx"
            out_path = os.path.join(settings.MEDIA_ROOT, 'outputs', out_filename)

            if bilingual:
                from apps.documents.docx_bilingual import create_bilingual_docx
                stats = create_bilingual_docx(
                    input_path=file_path,
                    output_path=out_path,
                    translate_fn=translate_fn,
                    source_lang=job.source_language,
                    target_lang=job.target_language,
                )
            else:
                stats = write_docx_layout(
                    input_path=file_path,
                    output_path=out_path,
                    translate_fn=translate_fn,
                    source_lang=job.source_language,
                    target_lang=job.target_language,
                )
            job.pages = 1
        else:
            text, pages = extract_text(file_path)
            source_text = text
            job.pages = pages
            job.save(update_fields=['pages'])

            translated_text = translate_document(
                text,
                source=job.source_language,
                target=job.target_language,
                style=style,
            )

            base_name = os.path.splitext(os.path.basename(file_path))[0]
            out_filename = f"{base_name}_{job.target_language}.{out_fmt}"
            out_path = os.path.join(settings.MEDIA_ROOT, 'outputs', out_filename)

            if bilingual and out_fmt == 'txt':
                bilingual_content = f"--- SOURCE ---\n\n{text}\n\n--- TRANSLATION ---\n\n{translated_text}"
                os.makedirs(os.path.dirname(out_path), exist_ok=True)
                with open(out_path, 'w', encoding='utf-8') as f:
                    f.write(bilingual_content)
            else:
                write_output(translated_text, out_path, out_fmt, source_path=file_path)

        job.output_file = f'outputs/{out_filename}'
        job.status = 'completed'
        job.save(update_fields=['output_file', 'status'])

        _fire_webhook(job, 'completed')

        if source_text:
            _run_qa_checks(job, source_text, translated_text)

        return {'job_id': job_id, 'status': 'completed'}

    except Exception as e:
        logger.exception("Failed to process job %d", job_id)
        job.status = 'failed'
        job.error_message = str(e)
        job.save(update_fields=['status', 'error_message'])
        _fire_webhook(job, 'failed')
        raise
