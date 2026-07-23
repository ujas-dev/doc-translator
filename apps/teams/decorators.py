from functools import wraps
from django.http import HttpResponseForbidden
from .models import TeamMember


def team_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        team_id = kwargs.get('team_id')
        if not team_id:
            return HttpResponseForbidden("Team ID required")
        if not TeamMember.objects.filter(user=request.user, team_id=team_id).exists():
            return HttpResponseForbidden("Not a team member")
        return view_func(request, *args, **kwargs)
    return wrapper


def owner_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        team_id = kwargs.get('team_id')
        if not team_id:
            return HttpResponseForbidden("Team ID required")
        if not TeamMember.objects.filter(user=request.user, team_id=team_id, role='owner').exists():
            return HttpResponseForbidden("Owner access required")
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_or_owner_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        team_id = kwargs.get('team_id')
        if not team_id:
            return HttpResponseForbidden("Team ID required")
        if not TeamMember.objects.filter(
            user=request.user, team_id=team_id, role__in=['owner', 'admin']
        ).exists():
            return HttpResponseForbidden("Admin or owner access required")
        return view_func(request, *args, **kwargs)
    return wrapper
