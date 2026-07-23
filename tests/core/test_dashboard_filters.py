import pytest
from django.utils import timezone
from datetime import timedelta
from apps.documents.models import DocumentJob


@pytest.mark.django_db
class TestDashboardFilters:
    def _create_job(self, user, status='completed', source_language='en', target_language='hi', days_ago=0):
        return DocumentJob.objects.create(
            user=user,
            source_file=b'test content',
            source_language=source_language,
            target_language=target_language,
            status=status,
            created_at=timezone.now() - timedelta(days=days_ago),
        )

    def test_dashboard_status_filter(self, authenticated_client, user):
        self._create_job(user, status='completed')
        self._create_job(user, status='failed')
        resp = authenticated_client.get('/dashboard/?status=completed')
        assert resp.status_code == 200

    def test_dashboard_source_lang_filter(self, authenticated_client, user):
        self._create_job(user, source_language='en')
        self._create_job(user, source_language='fr')
        resp = authenticated_client.get('/dashboard/?source_lang=en')
        assert resp.status_code == 200

    def test_dashboard_target_lang_filter(self, authenticated_client, user):
        self._create_job(user, target_language='hi')
        self._create_job(user, target_language='es')
        resp = authenticated_client.get('/dashboard/?target_lang=hi')
        assert resp.status_code == 200

    def test_dashboard_date_range_week(self, authenticated_client, user):
        self._create_job(user, days_ago=2)
        self._create_job(user, days_ago=30)
        resp = authenticated_client.get('/dashboard/?date_range=week')
        assert resp.status_code == 200

    def test_dashboard_date_range_month(self, authenticated_client, user):
        self._create_job(user, days_ago=10)
        self._create_job(user, days_ago=60)
        resp = authenticated_client.get('/dashboard/?date_range=month')
        assert resp.status_code == 200

    def test_dashboard_combined_filters(self, authenticated_client, user):
        self._create_job(user, status='completed', source_language='en', days_ago=1)
        self._create_job(user, status='failed', source_language='fr', days_ago=30)
        resp = authenticated_client.get('/dashboard/?status=completed&source_lang=en&date_range=week')
        assert resp.status_code == 200
