from django.contrib import admin
from .models import QARule, QAScore


@admin.register(QARule)
class QARuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'rule_type', 'severity', 'weight', 'enabled']
    list_filter = ['severity', 'enabled']


@admin.register(QAScore)
class QAScoreAdmin(admin.ModelAdmin):
    list_display = ['job', 'rule', 'score', 'created_at']
    list_filter = ['rule']
