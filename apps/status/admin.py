from django.contrib import admin

from .models import ServiceStatus


@admin.register(ServiceStatus)
class ServiceStatusAdmin(admin.ModelAdmin):
    list_display = ('service_name', 'status', 'latency_ms', 'last_checked', 'checked_by')
    list_filter = ('status',)
    readonly_fields = ('last_checked',)
