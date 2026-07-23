from django.contrib import admin
from .models import BatchJob, BatchFile


@admin.register(BatchJob)
class BatchJobAdmin(admin.ModelAdmin):
    list_display = ['pk', 'user', 'status', 'total_files', 'completed_files', 'failed_files', 'created_at']
    list_filter = ['status']


@admin.register(BatchFile)
class BatchFileAdmin(admin.ModelAdmin):
    list_display = ['original_name', 'batch', 'status', 'created_at']
    list_filter = ['status']
