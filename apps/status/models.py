from django.conf import settings
from django.db import models


class ServiceStatus(models.Model):
    STATUS_CHOICES = [
        ('healthy', 'Healthy'),
        ('degraded', 'Degraded'),
        ('down', 'Down'),
        ('unknown', 'Unknown'),
    ]

    service_name = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='unknown')
    latency_ms = models.IntegerField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    last_checked = models.DateTimeField(auto_now=True)
    checked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='status_checks',
    )

    class Meta:
        ordering = ['service_name']

    def __str__(self):
        return f"{self.service_name}: {self.status}"

    @property
    def status_color(self):
        return {
            'healthy': 'green',
            'degraded': 'yellow',
            'down': 'red',
            'unknown': 'gray',
        }.get(self.status, 'gray')

    @property
    def status_icon(self):
        return {
            'healthy': 'fa-check-circle',
            'degraded': 'fa-exclamation-triangle',
            'down': 'fa-times-circle',
            'unknown': 'fa-question-circle',
        }.get(self.status, 'fa-question-circle')
