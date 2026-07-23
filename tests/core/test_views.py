import pytest


@pytest.mark.django_db
class TestHomeView:
    def test_home_loads(self, client):
        resp = client.get("/")
        assert resp.status_code == 200

    def test_home_authenticated(self, authenticated_client):
        resp = authenticated_client.get("/")
        assert resp.status_code == 200


@pytest.mark.django_db
class TestDashboardView:
    def test_dashboard_loads(self, authenticated_client):
        resp = authenticated_client.get("/dashboard/")
        assert resp.status_code == 200

    def test_dashboard_requires_login(self, client):
        resp = client.get("/dashboard/")
        assert resp.status_code == 302

    def test_dashboard_shows_stats(self, authenticated_client):
        resp = authenticated_client.get("/dashboard/")
        assert b"Total Jobs" in resp.content

    def test_dashboard_empty(self, authenticated_client):
        resp = authenticated_client.get("/dashboard/")
        assert b"No translations yet" in resp.content


@pytest.mark.django_db
class TestPricingView:
    def test_pricing_loads(self, client):
        resp = client.get("/pricing/")
        assert resp.status_code == 200

    def test_pricing_shows_plans(self, client):
        resp = client.get("/pricing/")
        assert b"Free" in resp.content
        assert b"Pro" in resp.content
        assert b"Team" in resp.content
        assert b"Enterprise" in resp.content

    def test_pricing_current_plan(self, authenticated_client, user):
        resp = authenticated_client.get("/pricing/")
        assert b"CURRENT PLAN" in resp.content


@pytest.mark.django_db
class TestHealthCheck:
    def test_health_endpoint(self, client):
        resp = client.get("/health/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"


@pytest.mark.django_db
class TestOnboardingWizard:
    def test_onboarding_loads(self, authenticated_client):
        resp = authenticated_client.get("/onboarding/")
        assert resp.status_code == 200

    def test_onboarding_step_language(self, authenticated_client):
        resp = authenticated_client.post("/onboarding/", {'step': 'welcome'})
        assert resp.status_code == 200

    def test_onboarding_step_glossary(self, authenticated_client):
        resp = authenticated_client.post("/onboarding/", {'step': 'language'})
        assert resp.status_code == 200

    def test_onboarding_finish(self, authenticated_client, user):
        resp = authenticated_client.post("/onboarding/", {'step': 'finish'})
        assert resp.status_code == 302
        user.profile.refresh_from_db()
        assert user.profile.onboarding_completed is True

    def test_onboarding_skips_when_completed(self, authenticated_client, user):
        user.profile.onboarding_completed = True
        user.profile.save()
        resp = authenticated_client.get("/onboarding/")
        assert resp.status_code == 302

    def test_home_redirects_to_onboarding(self, authenticated_client, user):
        resp = authenticated_client.get("/")
        assert resp.status_code == 302


@pytest.mark.django_db
class TestHelpPage:
    def test_help_loads(self, client):
        resp = client.get("/help/")
        assert resp.status_code == 200

    def test_help_shows_faq(self, client):
        resp = client.get("/help/")
        assert b"Frequently Asked Questions" in resp.content

    def test_help_shows_support_email(self, client):
        resp = client.get("/help/")
        assert b"Contact Support" in resp.content
