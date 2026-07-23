from django.conf import settings
from django.db import models


class Glossary(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='glossaries')
    name = models.CharField(max_length=200)
    source_lang = models.CharField(max_length=10, default='en')
    target_lang = models.CharField(max_length=10, default='hi')
    description = models.TextField(blank=True)
    is_public = models.BooleanField(default=False)
    team = models.ForeignKey('teams.Team', on_delete=models.SET_NULL, null=True, blank=True, related_name='glossaries')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        unique_together = ['user', 'name']

    def __str__(self):
        return f"{self.name} ({self.source_lang}→{self.target_lang})"

    @property
    def entry_count(self):
        return self.entries.count()


class GlossaryEntry(models.Model):
    glossary = models.ForeignKey(Glossary, on_delete=models.CASCADE, related_name='entries')
    source = models.CharField(max_length=500)
    target = models.CharField(max_length=500)
    context = models.TextField(blank=True, help_text="Optional context for when to use this term")
    is_preferred = models.BooleanField(default=False, help_text="Mark as preferred translation")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['source']
        unique_together = ['glossary', 'source']

    def __str__(self):
        return f"{self.source} → {self.target}"
