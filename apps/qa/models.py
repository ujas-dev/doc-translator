from django.conf import settings
from django.db import models


class QARule(models.Model):
    SEVERITY_CHOICES = [
        ('critical', 'Critical'),
        ('major', 'Major'),
        ('minor', 'Minor'),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    rule_type = models.CharField(max_length=50)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='major')
    weight = models.FloatField(default=1.0)
    enabled = models.BooleanField(default=True)
    auto_approve_threshold = models.FloatField(default=0.8, help_text="Score threshold for auto-approval (0.0-1.0)")

    class Meta:
        ordering = ['-weight', 'name']

    def __str__(self):
        return f"{self.name} ({self.severity})"


class QAScore(models.Model):
    job = models.ForeignKey('documents.DocumentJob', on_delete=models.CASCADE, related_name='qa_scores')
    rule = models.ForeignKey(QARule, on_delete=models.CASCADE, related_name='scores')
    score = models.FloatField(default=0.0)
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-score']
        unique_together = ['job', 'rule']

    def __str__(self):
        return f"Job {self.job.pk} - {self.rule.name}: {self.score:.2f}"
