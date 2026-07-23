from django.conf import settings
from django.db import models


class BatchJob(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='batch_jobs')
    name = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_files = models.IntegerField(default=0)
    completed_files = models.IntegerField(default=0)
    failed_files = models.IntegerField(default=0)
    output_zip = models.FileField(upload_to='batch_outputs/', blank=True, null=True)
    source_language = models.CharField(max_length=20, default='auto')
    target_language = models.CharField(max_length=20, default='en')
    style_mode = models.CharField(max_length=20, default='fluid')
    bilingual = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Batch #{self.pk} - {self.status} ({self.completed_files}/{self.total_files})"

    @property
    def progress_percent(self):
        if self.total_files == 0:
            return 0
        return int((self.completed_files / self.total_files) * 100)


class BatchFile(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    batch = models.ForeignKey(BatchJob, on_delete=models.CASCADE, related_name='files')
    job = models.OneToOneField('documents.DocumentJob', on_delete=models.SET_NULL, null=True, blank=True, related_name='batch_file')
    file = models.FileField(upload_to='batch_uploads/', blank=True, null=True)
    original_name = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.original_name} ({self.status})"
