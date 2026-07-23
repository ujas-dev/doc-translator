import time
from unittest.mock import patch

import pytest
from django.core.cache import cache
from django.test import RequestFactory

from apps.core.middleware import RateLimitMiddleware
from apps.accounts.models import APIKey


@pytest.mark.django_db
class TestRateLimitMiddleware:
    def setup_method(self):
        self.factory = RequestFactory()
        self.cache_key_prefix = 'rate_limit:'
        cache.clear()

    def _make_middleware(self):
        def dummy_view(request):
            from django.http import HttpResponse
            return HttpResponse("OK")
        return RateLimitMiddleware(dummy_view)

    def test_non_api_path_bypasses_rate_limit(self):
        middleware = self._make_middleware()
        request = self.factory.get('/dashboard/')
        response = middleware(request)
        assert response.status_code == 200

    def test_free_user_rate_limit(self, user):
        middleware = self._make_middleware()
        request = self.factory.get('/api/translate/')
        request.user = user

        for _ in range(30):
            cache.delete(f'{self.cache_key_prefix}user:{user.id}')
            response = middleware(request)
            assert response.status_code == 200

        cache.delete(f'{self.cache_key_prefix}user:{user.id}')
        response = middleware(request)
        assert response.status_code == 429
        assert b'Rate limit exceeded' in response.content

    def test_pro_user_rate_limit(self, pro_user):
        middleware = self._make_middleware()
        request = self.factory.get('/api/translate/')
        request.user = pro_user

        for _ in range(200):
            cache.delete(f'{self.cache_key_prefix}user:{pro_user.id}')
            response = middleware(request)
            assert response.status_code == 200

        cache.delete(f'{self.cache_key_prefix}user:{pro_user.id}')
        response = middleware(request)
        assert response.status_code == 429

    def test_team_user_rate_limit(self, team_user):
        middleware = self._make_middleware()
        request = self.factory.get('/api/translate/')
        request.user = team_user

        for _ in range(500):
            cache.delete(f'{self.cache_key_prefix}user:{team_user.id}')
            response = middleware(request)
            assert response.status_code == 200

        cache.delete(f'{self.cache_key_prefix}user:{team_user.id}')
        response = middleware(request)
        assert response.status_code == 429

    def test_enterprise_user_rate_limit(self, enterprise_user):
        middleware = self._make_middleware()
        request = self.factory.get('/api/translate/')
        request.user = enterprise_user

        for _ in range(1000):
            cache.delete(f'{self.cache_key_prefix}user:{enterprise_user.id}')
            response = middleware(request)
            assert response.status_code == 200

        cache.delete(f'{self.cache_key_prefix}user:{enterprise_user.id}')
        response = middleware(request)
        assert response.status_code == 429

    def test_anonymous_ip_rate_limit(self):
        middleware = self._make_middleware()
        request = self.factory.get('/api/translate/', REMOTE_ADDR='192.168.1.1')

        for _ in range(20):
            cache.delete(f'{self.cache_key_prefix}ip:192.168.1.1')
            response = middleware(request)
            assert response.status_code == 200

        cache.delete(f'{self.cache_key_prefix}ip:192.168.1.1')
        response = middleware(request)
        assert response.status_code == 429

    def test_api_key_rate_limit(self, user, api_key):
        middleware = self._make_middleware()
        request = self.factory.get('/api/translate/',
                                   HTTP_AUTHORIZATION=f'Bearer {api_key.key}')
        request.user = user

        for _ in range(100):
            cache.delete(f'{self.cache_key_prefix}user:{user.id}')
            response = middleware(request)
            assert response.status_code == 200

        cache.delete(f'{self.cache_key_prefix}user:{user.id}')
        response = middleware(request)
        assert response.status_code == 429

    def test_rate_limit_response_headers(self, user):
        middleware = self._make_middleware()
        request = self.factory.get('/api/translate/')
        request.user = user

        response = middleware(request)
        assert response.status_code == 200

    def test_rate_limit_429_includes_retry_after(self, user):
        middleware = self._make_middleware()
        request = self.factory.get('/api/translate/')
        request.user = user

        cache_key = f'{self.cache_key_prefix}user:{user.id}'
        cache.set(cache_key, [time.time()] * 31, 3600)

        response = middleware(request)
        assert response.status_code == 429
        assert 'Retry-After' in response

    def test_rate_limit_window_expiry(self, user):
        middleware = self._make_middleware()
        request = self.factory.get('/api/translate/')
        request.user = user

        cache_key = f'{self.cache_key_prefix}user:{user.id}'
        old_time = time.time() - 3601
        cache.set(cache_key, [old_time] * 31, 3600)

        response = middleware(request)
        assert response.status_code == 200

    def test_x_forwarded_for_ip(self):
        middleware = self._make_middleware()
        request = self.factory.get('/api/translate/',
                                   HTTP_X_FORWARDED_FOR='10.0.0.1, 192.168.1.1')
        request.META['REMOTE_ADDR'] = '127.0.0.1'

        identifier = middleware._get_identifier(request)
        assert identifier == 'ip:10.0.0.1'

    def test_separate_rate_limits_per_user(self, user, pro_user):
        middleware = self._make_middleware()

        request_free = self.factory.get('/api/translate/')
        request_free.user = user

        request_pro = self.factory.get('/api/translate/')
        request_pro.user = pro_user

        for _ in range(30):
            cache.delete(f'{self.cache_key_prefix}user:{user.id}')
            response = middleware(request_free)
            assert response.status_code == 200

        cache.delete(f'{self.cache_key_prefix}user:{user.id}')
        response = middleware(request_free)
        assert response.status_code == 429

        response = middleware(request_pro)
        assert response.status_code == 200

    def test_rate_limit_headers_present(self, user):
        middleware = self._make_middleware()
        request = self.factory.get('/api/translate/')
        request.user = user

        response = middleware(request)
        assert 'X-RateLimit-Limit' in response
        assert 'X-RateLimit-Remaining' in response
        assert 'X-RateLimit-Reset' in response

    def test_rate_limit_headers_correct_values(self, user):
        middleware = self._make_middleware()
        request = self.factory.get('/api/translate/')
        request.user = user

        response = middleware(request)
        assert response['X-RateLimit-Limit'] == '30'
        assert response['X-RateLimit-Remaining'] == '29'

    def test_rate_limit_headers_decrease(self, user):
        middleware = self._make_middleware()
        request = self.factory.get('/api/translate/')
        request.user = user

        cache.delete(f'{self.cache_key_prefix}user:{user.id}')
        response = middleware(request)
        assert response['X-RateLimit-Remaining'] == '29'

        cache.delete(f'{self.cache_key_prefix}user:{user.id}')
        response = middleware(request)
        assert response['X-RateLimit-Remaining'] == '28'

    def test_api_key_rate_limit_uses_custom_limit(self, user, api_key):
        api_key.rate_limit = 50
        api_key.save()

        middleware = self._make_middleware()
        request = self.factory.get('/api/translate/',
                                   HTTP_AUTHORIZATION=f'Bearer {api_key.key}')
        request.user = user

        response = middleware(request)
        assert response['X-RateLimit-Limit'] == '50'

    def test_api_key_fallback_rate_limit(self):
        middleware = self._make_middleware()
        request = self.factory.get('/api/translate/',
                                   HTTP_AUTHORIZATION='Bearer dt_invalidkey1234')

        response = middleware(request)
        assert response.status_code == 200
        assert response['X-RateLimit-Limit'] == '100'

    def test_non_api_no_headers(self, user):
        middleware = self._make_middleware()
        request = self.factory.get('/dashboard/')
        request.user = user

        response = middleware(request)
        assert 'X-RateLimit-Limit' not in response
