import time
import pytest
from unittest.mock import patch, MagicMock

from apps.status.services import check_celery_worker, check_celery_beat


@pytest.mark.django_db
class TestCheckCeleryWorker:
    @patch('apps.status.services.redis')
    def test_healthy_with_recent_heartbeat(self, mock_redis, settings):
        settings.CELERY_BROKER_URL = 'redis://localhost:6379/1'
        mock_instance = MagicMock()
        mock_instance.llen.return_value = 3
        mock_redis.from_url.return_value = mock_instance

        from django.core.cache import cache
        cache.set('celery_worker_heartbeat', time.time() - 30)

        result = check_celery_worker()
        assert result['status'] == 'healthy'
        assert 'latency_ms' in result
        assert 'Queue: 3 tasks' in result['detail']

    @patch('apps.status.services.redis')
    def test_degraded_stale_heartbeat(self, mock_redis, settings):
        settings.CELERY_BROKER_URL = 'redis://localhost:6379/1'
        mock_instance = MagicMock()
        mock_instance.llen.return_value = 0
        mock_redis.from_url.return_value = mock_instance

        from django.core.cache import cache
        cache.set('celery_worker_heartbeat', time.time() - 300)

        result = check_celery_worker()
        assert result['status'] == 'degraded'
        assert 'stale' in result['error']

    @patch('apps.status.services.redis')
    def test_unknown_no_heartbeat(self, mock_redis, settings):
        settings.CELERY_BROKER_URL = 'redis://localhost:6379/1'
        mock_instance = MagicMock()
        mock_instance.llen.return_value = 0
        mock_redis.from_url.return_value = mock_instance

        from django.core.cache import cache
        cache.delete('celery_worker_heartbeat')

        result = check_celery_worker()
        assert result['status'] == 'unknown'
        assert 'No heartbeat' in result['detail']

    @patch('apps.status.services.redis')
    def test_down_on_exception(self, mock_redis, settings):
        settings.CELERY_BROKER_URL = 'redis://localhost:6379/1'
        mock_redis.from_url.side_effect = Exception("Connection refused")

        result = check_celery_worker()
        assert result['status'] == 'down'
        assert 'Connection refused' in result['error']


@pytest.mark.django_db
class TestCheckCeleryBeat:
    def test_healthy_recent_tick(self):
        from django.core.cache import cache
        cache.set('celery_beat_last_tick', time.time() - 30)

        result = check_celery_beat()
        assert result['status'] == 'healthy'
        assert 'latency_ms' in result

    def test_degraded_stale_tick(self):
        from django.core.cache import cache
        cache.set('celery_beat_last_tick', time.time() - 300)

        result = check_celery_beat()
        assert result['status'] == 'degraded'
        assert 'Last tick' in result['error']

    def test_unknown_no_tick(self):
        from django.core.cache import cache
        cache.delete('celery_beat_last_tick')

        result = check_celery_beat()
        assert result['status'] == 'unknown'
        assert 'No beat tick' in result['detail']
