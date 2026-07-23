from functools import wraps

from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect

from apps.accounts.models import UserProfile


def _get_profile(user):
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


def plan_required(feature):
    """Decorator for function-based views.

    Checks that the authenticated user's plan includes *feature*.
    * For HTML requests: flashes a message and redirects to /pricing/.
    * For JSON/API requests: returns 403.
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect(settings.LOGIN_URL or '/login/')
            profile = _get_profile(request.user)
            if profile.has_feature(feature):
                return view_func(request, *args, **kwargs)

            accept = request.META.get('HTTP_ACCEPT', '')
            if 'application/json' in accept or request.path.startswith('/api/'):
                return JsonResponse(
                    {'error': f'This feature requires a higher plan. Feature: {feature}'},
                    status=403,
                )
            messages.warning(request, f'Upgrade your plan to access {feature.replace("_", " ")}.')
            return redirect('pricing')

        return _wrapped

    return decorator
