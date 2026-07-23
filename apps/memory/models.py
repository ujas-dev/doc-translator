from django.conf import settings
from django.db import models


class TMEntry(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tm_entries')
    source_lang = models.CharField(max_length=10)
    target_lang = models.CharField(max_length=10)
    source_text = models.TextField()
    target_text = models.TextField()
    context = models.TextField(blank=True, help_text="Source document context")
    quality_score = models.FloatField(default=1.0, help_text="0.0-1.0 quality score")
    team = models.ForeignKey('teams.Team', on_delete=models.SET_NULL, null=True, blank=True, related_name='tm_entries')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', 'source_lang', 'target_lang']),
        ]

    def __str__(self):
        return f"{self.source_text[:50]} → {self.target_text[:50]}"
