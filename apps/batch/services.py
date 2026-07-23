import io
import structlog
import os
import tempfile
import zipfile

from django.conf import settings

logger = structlog.get_logger(__name__)


def create_batch_zip(batch_job) -> str:
    from apps.documents.models import DocumentJob

    zip_filename = f"batch_{batch_job.pk}_output.zip"
    zip_path = os.path.join(settings.MEDIA_ROOT, 'batch_outputs', zip_filename)
    os.makedirs(os.path.dirname(zip_path), exist_ok=True)

    jobs = DocumentJob.objects.filter(
        batch_file__batch=batch_job,
        status='completed',
        output_file__isnull=False,
    )

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for job in jobs:
            if job.output_file and os.path.exists(job.output_file.path):
                arcname = os.path.basename(job.output_file.path)
                zf.write(job.output_file.path, arcname)

    return zip_path


def extract_zip_to_files(zip_content: bytes) -> list:
    files = []
    with zipfile.ZipFile(io.BytesIO(zip_content), 'r') as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            ext = os.path.splitext(info.filename)[1].lower()
            if ext in ('.txt', '.docx', '.pdf', '.xlsx', '.pptx', '.html', '.csv', '.md',
                       '.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.webp'):
                files.append({
                    'name': os.path.basename(info.filename),
                    'data': zf.read(info.filename),
                })
    return files
