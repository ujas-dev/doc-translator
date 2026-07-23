import mimetypes
import os
from django.conf import settings
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import render, get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from .models import DocumentJob
from .serializers import DocumentJobSerializer
from .tasks import process_document


class DocumentJobListCreateView(generics.ListCreateAPIView):
    queryset = DocumentJob.objects.all().order_by('-created_at')
    serializer_class = DocumentJobSerializer

    def perform_create(self, serializer):
        job = serializer.save(user=self.request.user if self.request.user.is_authenticated else None)
        process_document.delay(job.pk)


class DocumentJobRetrieveView(generics.RetrieveAPIView):
    queryset = DocumentJob.objects.all()
    serializer_class = DocumentJobSerializer


def job_detail_template(request, pk):
    job = get_object_or_404(DocumentJob, pk=pk)
    job.source_file_name = job.source_file.name.split('/')[-1] if job.source_file else 'Unknown'
    return render(request, 'documents/job_detail.html', {'job': job})


def job_status_partial(request, job_id):
    job = get_object_or_404(DocumentJob, pk=job_id)
    return render(request, 'documents/partials/status_badge.html', {'status': job.status})


def job_preview_partial(request, job_id):
    job = get_object_or_404(DocumentJob, pk=job_id)
    output_file = job.output_file.url if job.output_file else None
    return render(request, 'documents/partials/preview.html', {
        'status': job.status,
        'output_file': output_file,
        'job_id': job_id,
    })


def download_output(request, job_id):
    try:
        job = DocumentJob.objects.get(pk=job_id)
    except DocumentJob.DoesNotExist:
        raise Http404("Job not found")

    if job.status != 'completed' or not job.output_file:
        return JsonResponse(
            {'error': 'File not ready yet'},
            status=409,
        )

    file_path = job.output_file.path
    if not os.path.exists(file_path):
        raise Http404("Output file not found on disk")

    return FileResponse(
        open(file_path, 'rb'),
        as_attachment=True,
        filename=os.path.basename(file_path),
    )


def job_preview(request, pk):
    job = get_object_or_404(DocumentJob, pk=pk)
    file_type = request.GET.get('type', 'source')

    if file_type == 'output':
        if job.status != 'completed' or not job.output_file:
            raise Http404("Output file not ready")
        file_path = job.output_file.path
    else:
        if not job.source_file:
            raise Http404("Source file not found")
        file_path = job.source_file.path

    if not os.path.exists(file_path):
        raise Http404("File not found on disk")

    content_type, _ = mimetypes.guess_type(file_path)
    if not content_type:
        content_type = 'application/octet-stream'

    return FileResponse(
        open(file_path, 'rb'),
        content_type=content_type,
        filename=os.path.basename(file_path),
    )
