from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.core.paginator import Paginator

from .models import AuditLog
from apps.core.decorators import plan_required


@login_required
@plan_required('audit')
def audit_list(request):
    logs = AuditLog.objects.filter(user=request.user)

    action = request.GET.get('action')
    if action:
        logs = logs.filter(action=action)

    resource_type = request.GET.get('resource_type')
    if resource_type:
        logs = logs.filter(resource_type=resource_type)

    paginator = Paginator(logs, 50)
    page = request.GET.get('page')
    logs = paginator.get_page(page)

    return render(request, 'audit/list.html', {'logs': logs})


@login_required
@plan_required('audit')
def audit_detail(request, log_id):
    log = get_object_or_404(AuditLog, pk=log_id, user=request.user)
    return render(request, 'audit/detail.html', {'log': log})


@login_required
@plan_required('audit')
def audit_export(request):
    logs = AuditLog.objects.filter(user=request.user)[:1000]

    data = []
    for log in logs:
        data.append({
            'timestamp': log.created_at.isoformat(),
            'action': log.action,
            'resource_type': log.resource_type,
            'resource_id': log.resource_id,
            'details': log.details,
            'ip_address': log.ip_address,
        })

    return JsonResponse({'logs': data})
