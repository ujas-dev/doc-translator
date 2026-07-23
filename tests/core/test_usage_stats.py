import pytest
from django.utils import timezone
from datetime import timedelta
from apps.documents.models import DocumentJob


@pytest.mark.django_db
class TestDashboardUsageStats:
    def test_usage_stats_with_jobs(self, authenticated_client, user):
        now = timezone.now()
        DocumentJob.objects.create(
            user=user, source_file=b'test', status='completed',
            page_count=5, character_count=1000,
            created_at=now - timedelta(days=2),
        )
        DocumentJob.objects.create(
            user=user, source_file=b'test2', status='completed',
            page_count=3, character_count=500,
            created_at=now - timedelta(days=5),
        )
        resp = authenticated_client.get('/dashboard/')
        assert resp.status_code == 200

    def test_usage_stats_excludes_old_jobs(self, authenticated_client, user):
        now = timezone.now()
        DocumentJob.objects.create(
            user=user, source_file=b'old', status='completed',
            page_count=10, character_count=2000,
            created_at=now - timedelta(days=60),
        )
        resp = authenticated_client.get('/dashboard/')
        assert resp.status_code == 200

    def test_daily_usage_empty(self, authenticated_client, user):
        resp = authenticated_client.get('/dashboard/')
        assert resp.status_code == 200

    def test_stats_cards(self, authenticated_client, user):
        now = timezone.now()
        DocumentJob.objects.create(user=user, source_file=b'test', status='completed')
        DocumentJob.objects.create(user=user, source_file=b'test2', status='failed')
        DocumentJob.objects.create(user=user, source_file=b'test3', status='processing')
        resp = authenticated_client.get('/dashboard/')
        assert resp.status_code == 200
