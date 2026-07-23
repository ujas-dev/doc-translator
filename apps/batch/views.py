import os
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from rest_framework import generics, permissions, status
from rest_framework.response import Response

from .models import BatchJob, BatchFile
from .serializers import BatchJobSerializer, BatchCreateSerializer
from .services import extract_zip_to_files
from apps.core.decorators import plan_required


@login_required
@plan_required('batch')
def batch_list(request):
    batches = BatchJob.objects.filter(user=request.user).order_by('-created_at')[:20]
    return render(request, 'batch/list.html', {'batches': batches})


@login_required
@plan_required('batch')
def batch_upload(request):
    if request.method == 'POST':
        zip_file = request.FILES.get('zip_file')
        if not zip_file or not zip_file.name.endswith('.zip'):
            return JsonResponse({'error': 'Please upload a ZIP file'}, status=400)

        batch = BatchJob.objects.create(
            user=request.user,
            name=zip_file.name,
            source_language=request.POST.get('source_language', 'auto'),
            target_language=request.POST.get('target_language', 'en'),
            style_mode=request.POST.get('style_mode', 'fluid'),
            bilingual=request.POST.get('bilingual') == 'on',
        )

        zip_content = zip_file.read()
        files = extract_zip_to_files(zip_content)

        batch.total_files = len(files)
        batch.save(update_fields=['total_files'])

        for file_info in files:
            from django.core.files.base import ContentFile
            bf = BatchFile(batch=batch, original_name=file_info['name'])
            bf.file.save(file_info['name'], ContentFile(file_info['data']))
            bf.save()

        from .tasks import process_batch
        process_batch.delay(batch.pk)

        return redirect('batch_detail', batch_id=batch.pk)

    return render(request, 'batch/upload.html')


@login_required
@plan_required('batch')
def batch_detail(request, batch_id):
    batch = get_object_or_404(BatchJob, pk=batch_id, user=request.user)
    files = batch.files.all()
    return render(request, 'batch/detail.html', {'batch': batch, 'files': files})


@login_required
@plan_required('batch')
@require_POST
def batch_download(request, batch_id):
    batch = get_object_or_404(BatchJob, pk=batch_id, user=request.user)
    if batch.status != 'completed' or not batch.output_zip:
        return JsonResponse({'error': 'Batch not ready'}, status=409)

    file_path = batch.output_zip.path
    if not os.path.exists(file_path):
        raise Http404("ZIP not found")

    return FileResponse(
        open(file_path, 'rb'),
        as_attachment=True,
        filename=os.path.basename(file_path),
    )


@login_required
@plan_required('batch')
def batch_status(request, batch_id):
    batch = get_object_or_404(BatchJob, pk=batch_id, user=request.user)
    return JsonResponse({
        'status': batch.status,
        'total_files': batch.total_files,
        'completed_files': batch.completed_files,
        'failed_files': batch.failed_files,
        'progress': batch.progress_percent,
    })


class BatchJobListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        from apps.accounts.models import UserProfile
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        if not profile.has_feature('batch'):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('This feature requires a higher plan.')

    def get_queryset(self):
        return BatchJob.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return BatchCreateSerializer
        return BatchJobSerializer

    def create(self, request, *args, **kwargs):
        serializer = BatchCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        zip_file = serializer.validated_data['zip_file']
        if not zip_file.name.endswith('.zip'):
            return Response(
                {'error': 'Please upload a ZIP file'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        batch = BatchJob.objects.create(
            user=request.user,
            name=serializer.validated_data.get('name', zip_file.name),
            source_language=serializer.validated_data['source_language'],
            target_language=serializer.validated_data['target_language'],
            style_mode=serializer.validated_data['style_mode'],
            bilingual=serializer.validated_data['bilingual'],
        )

        zip_content = zip_file.read()
        files = extract_zip_to_files(zip_content)
        batch.total_files = len(files)
        batch.save(update_fields=['total_files'])

        for file_info in files:
            from django.core.files.base import ContentFile
            bf = BatchFile(batch=batch, original_name=file_info['name'])
            bf.file.save(file_info['name'], ContentFile(file_info['data']))
            bf.save()

        from .tasks import process_batch as process_batch_task
        process_batch_task.delay(batch.pk)

        return Response(
            BatchJobSerializer(batch).data,
            status=status.HTTP_201_CREATED,
        )


class BatchJobStatusView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = BatchJobSerializer

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        from apps.accounts.models import UserProfile
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        if not profile.has_feature('batch'):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('This feature requires a higher plan.')

    def get_queryset(self):
        return BatchJob.objects.filter(user=self.request.user)

