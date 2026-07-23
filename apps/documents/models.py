from django.conf import settings
from django.db import models


class DocumentJob(models.Model):
    STATUS_CHOICES = [
        ('queued', 'Queued'),
        ('processing', 'Processing'),
        ('translated', 'Translated'),
        ('converted', 'Converted'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    STYLE_CHOICES = [
        ('faithful', 'Faithful'),
        ('fluid', 'Fluid'),
        ('creative', 'Creative'),
        ('formal', 'Formal'),
        ('casual', 'Casual'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='document_jobs',
    )
    source_file = models.FileField(upload_to='uploads/')
    output_file = models.FileField(upload_to='outputs/', blank=True, null=True)
    source_language = models.CharField(max_length=20, default='auto')
    target_language = models.CharField(max_length=20, default='en')
    source_format = models.CharField(max_length=20, blank=True)
    target_format = models.CharField(max_length=20, blank=True)
    style_mode = models.CharField(max_length=20, choices=STYLE_CHOICES, default='fluid')
    bilingual = models.BooleanField(default=False)
    webhook_url = models.URLField(blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='queued')
    error_message = models.TextField(blank=True)
    pages = models.IntegerField(default=0)
    page_count = models.IntegerField(default=0)
    character_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Job #{self.pk} - {self.status}'
