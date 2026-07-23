import pytest
from apps.qa.models import QAScore, QARule
from apps.documents.models import DocumentJob


@pytest.mark.django_db
class TestQADashboardView:
    def test_qa_dashboard_loads(self, authenticated_client):
        resp = authenticated_client.get('/qa/')
        assert resp.status_code == 200

    def test_qa_dashboard_requires_login(self, client):
        resp = client.get('/qa/')
        assert resp.status_code == 302

    def test_qa_dashboard_shows_completed_jobs(self, authenticated_client, user):
        DocumentJob.objects.create(
            source_file=b'test content',
            source_language='en',
            target_language='hi',
            status='completed',
            user=user,
        )
        resp = authenticated_client.get('/qa/')
        assert resp.status_code == 200


@pytest.mark.django_db
class TestQAReviewView:
    def test_qa_review_loads(self, authenticated_client, document_job):
        resp = authenticated_client.get(f'/qa/{document_job.pk}/')
        assert resp.status_code == 200

    def test_qa_review_not_found(self, authenticated_client):
        resp = authenticated_client.get('/qa/99999/')
        assert resp.status_code == 404

    def test_qa_review_other_users_job(self, authenticated_client, pro_user):
        job = DocumentJob.objects.create(
            source_file=b'test content',
            source_language='en',
            target_language='hi',
            status='completed',
            user=pro_user,
        )
        resp = authenticated_client.get(f'/qa/{job.pk}/')
        assert resp.status_code == 404


@pytest.mark.django_db
class TestQARunCheckView:
    def test_qa_run_check_requires_post(self, authenticated_client, document_job):
        resp = authenticated_client.get(f'/qa/{document_job.pk}/check/')
        assert resp.status_code == 405

    def test_qa_run_check_not_found(self, authenticated_client):
        resp = authenticated_client.post('/qa/99999/check/')
        assert resp.status_code == 404

    def test_qa_run_check_returns_results(self, authenticated_client, document_job):
        resp = authenticated_client.post(f'/qa/{document_job.pk}/check/')
        assert resp.status_code == 200
        data = resp.json()
        assert 'results' in data
