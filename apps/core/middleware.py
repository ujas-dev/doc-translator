import time
from django.core.cache import cache
from django.http import JsonResponse


class RateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/api/'):
            rate_limit = self._get_rate_limit(request)
            if rate_limit and self._is_rate_limited(request, rate_limit):
                return JsonResponse(
                    {'error': 'Rate limit exceeded. Please try again later.'},
                    status=429,
                    headers={'Retry-After': '60'}
                )

        response = self.get_response(request)

        if request.path.startswith('/api/'):
            rate_limit = self._get_rate_limit(request)
            if rate_limit:
                identifier = self._get_identifier(request)
                cache_key = f'rate_limit:{identifier}'
                requests = cache.get(cache_key, [])
                now = time.time()
                requests = [r for r in requests if now - r < 3600]
                remaining = max(0, rate_limit - len(requests))
                reset_time = int(requests[0]) + 3600 if requests else int(now) + 3600

                response['X-RateLimit-Limit'] = str(rate_limit)
                response['X-RateLimit-Remaining'] = str(remaining)
                response['X-RateLimit-Reset'] = str(reset_time)

        return response

    def _get_rate_limit(self, request):
        if hasattr(request, 'user') and request.user.is_authenticated:
            profile = getattr(request.user, 'profile', None)
            if profile:
                limits = {'free': 30, 'pro': 200, 'team': 500, 'enterprise': 1000}
                return limits.get(profile.plan, 30)

        api_key = request.META.get('HTTP_AUTHORIZATION', '').replace('Bearer ', '')
        if api_key and api_key.startswith('dt_'):
            try:
                from apps.accounts.models import APIKey
                key_obj = APIKey.objects.get(key=api_key, is_active=True)
                return key_obj.rate_limit
            except APIKey.DoesNotExist:
                return 100

        return 20

    def _is_rate_limited(self, request, rate_limit):
        identifier = self._get_identifier(request)
        cache_key = f'rate_limit:{identifier}'
        requests = cache.get(cache_key, [])

        now = time.time()
        requests = [r for r in requests if now - r < 3600]

        if len(requests) >= rate_limit:
            return True

        requests.append(now)
        cache.set(cache_key, requests, 3600)
        return False

    def _get_identifier(self, request):
        if hasattr(request, 'user') and request.user.is_authenticated:
            return f'user:{request.user.id}'

        api_key = request.META.get('HTTP_AUTHORIZATION', '').replace('Bearer ', '')
        if api_key and api_key.startswith('dt_'):
            return f'apikey:{api_key[:16]}'

        ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
        if not ip:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        return f'ip:{ip}'
