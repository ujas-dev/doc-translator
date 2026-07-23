from django.urls import path
from .views import (
    DocumentJobListCreateView, DocumentJobRetrieveView,
    download_output, job_detail_template, job_preview,
    job_status_partial, job_preview_partial,
)

urlpatterns = [
    path('jobs/', DocumentJobListCreateView.as_view(), name='document-job-list-create'),
    path('jobs/<int:pk>/', DocumentJobRetrieveView.as_view(), name='document-job-retrieve'),
    path('jobs/<int:job_id>/download/', download_output, name='document-job-download'),
    path('jobs/<int:pk>/detail/', job_detail_template, name='job-detail'),
    path('jobs/<int:pk>/preview/', job_preview, name='job-preview'),
    path('jobs/<int:job_id>/status-partial/', job_status_partial, name='document-job-status-partial'),
    path('jobs/<int:job_id>/preview-partial/', job_preview_partial, name='document-job-preview-partial'),
]
