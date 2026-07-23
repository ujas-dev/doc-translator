from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.shortcuts import render

from .models import ServiceStatus
from .services import run_all_checks, SERVICES


def public_status(request):
    statuses = ServiceStatus.objects.all()
    status_map = {s.service_name: s for s in statuses}

    service_list = []
    for svc in SERVICES:
        st = status_map.get(svc["name"])
        service_list.append({
            "name": svc["name"],
            "label": svc["label"],
            "icon": svc["icon"],
            "status": st.status if st else "unknown",
            "latency_ms": st.latency_ms if st else None,
            "error_message": st.error_message if st else "",
            "last_checked": st.last_checked if st else None,
        })

    overall = "healthy"
    for s in service_list:
        if s["status"] == "down":
            overall = "down"
            break
        if s["status"] == "degraded":
            overall = "degraded"

    return render(request, 'status/public_status.html', {
        'services': service_list,
        'overall': overall,
    })


@staff_member_required
def detail_status(request):
    statuses = ServiceStatus.objects.all()
    status_map = {s.service_name: s for s in statuses}

    service_list = []
    for svc in SERVICES:
        st = status_map.get(svc["name"])
        service_list.append({
            "name": svc["name"],
            "label": svc["label"],
            "icon": svc["icon"],
            "status": st.status if st else "unknown",
            "latency_ms": st.latency_ms if st else None,
            "error_message": st.error_message if st else "",
            "last_checked": st.last_checked if st else None,
            "checked_by": st.checked_by if st else None,
        })

    overall = "healthy"
    for s in service_list:
        if s["status"] == "down":
            overall = "down"
            break
        if s["status"] == "degraded":
            overall = "degraded"

    return render(request, 'status/detail_status.html', {
        'services': service_list,
        'overall': overall,
    })


@staff_member_required
def check_service(request, service_name):
    svc_config = next((s for s in SERVICES if s["name"] == service_name), None)
    if not svc_config:
        return JsonResponse({"error": f"Unknown service: {service_name}"}, status=404)

    from . import services as svc_module
    fn = getattr(svc_module, svc_config["check_fn"])
    try:
        result = fn()
    except Exception as e:
        result = {"status": "down", "latency_ms": 0, "error": str(e)}

    status_obj, _ = ServiceStatus.objects.update_or_create(
        service_name=service_name,
        defaults={
            "status": result["status"],
            "latency_ms": result.get("latency_ms"),
            "error_message": result.get("error", result.get("detail", "")),
            "checked_by": request.user if request.user.is_authenticated else None,
        },
    )

    return JsonResponse({
        "name": service_name,
        "status": status_obj.status,
        "latency_ms": status_obj.latency_ms,
        "error_message": status_obj.error_message,
        "last_checked": status_obj.last_checked.isoformat() if status_obj.last_checked else None,
    })


@staff_member_required
def check_all_services(request):
    results = run_all_checks()

    for svc_result in results["services"]:
        ServiceStatus.objects.update_or_create(
            service_name=svc_result["name"],
            defaults={
                "status": svc_result["status"],
                "latency_ms": svc_result.get("latency_ms"),
                "error_message": svc_result.get("error", svc_result.get("detail", "")),
                "checked_by": request.user if request.user.is_authenticated else None,
            },
        )

    return JsonResponse({
        "overall": results["overall"],
        "services": results["services"],
    })
