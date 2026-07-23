import structlog
import os
from celery import chord, group, shared_task
from django.conf import settings

logger = structlog.get_logger(__name__)


@shared_task(bind=True)
def process_batch_file(self, batch_file_id: int):
    from apps.batch.models import BatchFile
    from apps.documents.models import DocumentJob
    from apps.documents.tasks import process_document

    batch_file = BatchFile.objects.get(pk=batch_file_id)
    try:
        batch_file.status = 'processing'
        batch_file.save(update_fields=['status'])

        batch = batch_file.batch

        job = DocumentJob.objects.create(
            source_file=batch_file.file,
            source_language=batch.source_language,
            target_language=batch.target_language,
            style_mode=batch.style_mode,
            bilingual=batch.bilingual,
        )

        batch_file.job = job
        batch_file.save(update_fields=['job'])

        process_document.delay(job.pk)

        batch_file.status = 'completed'
        batch_file.save(update_fields=['status'])

        batch.completed_files += 1
        batch.save(update_fields=['completed_files'])

    except Exception as e:
        logger.exception("Failed to process batch file %d", batch_file_id)
        batch_file.status = 'failed'
        batch_file.error_message = str(e)
        batch_file.save(update_fields=['status', 'error_message'])

        batch = batch_file.batch
        batch.failed_files += 1
        batch.save(update_fields=['failed_files'])


@shared_task(bind=True)
def complete_batch(self, batch_id: int):
    from apps.batch.models import BatchJob
    from apps.batch.services import create_batch_zip

    batch = BatchJob.objects.get(pk=batch_id)
    try:
        zip_path = create_batch_zip(batch)
        batch.output_zip = f'batch_outputs/{os.path.basename(zip_path)}'
        batch.status = 'completed'
        batch.save(update_fields=['output_zip', 'status'])
    except Exception as e:
        logger.exception("Failed to complete batch %d", batch_id)
        batch.status = 'failed'
        batch.save(update_fields=['status'])


@shared_task(bind=True)
def process_batch(self, batch_id: int):
    from apps.batch.models import BatchJob, BatchFile

    batch = BatchJob.objects.get(pk=batch_id)
    try:
        batch.status = 'processing'
        batch.save(update_fields=['status'])

        files = BatchFile.objects.filter(batch=batch)

        header = group(process_batch_file.s(f.id) for f in files)
        callback = complete_batch.s(batch_id)

        chord(header)(callback)

    except Exception as e:
        logger.exception("Failed to process batch %d", batch_id)
        batch.status = 'failed'
        batch.save(update_fields=['status'])
