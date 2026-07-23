import pytest
from apps.billing.models import Plan


@pytest.mark.django_db
class TestBillingCheckoutView:
    def test_checkout_requires_login(self, client, plan_pro):
        resp = client.get(f'/billing/checkout/{plan_pro.slug}/')
        assert resp.status_code == 302

    def test_checkout_redirects_free_plan(self, authenticated_client, plan_free):
        resp = authenticated_client.get(f'/billing/checkout/{plan_free.slug}/')
        assert resp.status_code == 302

    def test_checkout_redirects_pricing_on_stripe_error(self, authenticated_client, plan_pro):
        resp = authenticated_client.get(f'/billing/checkout/{plan_pro.slug}/')
        assert resp.status_code == 302

    def test_checkout_nonexistent_plan(self, authenticated_client):
        resp = authenticated_client.get('/billing/checkout/nonexistent/')
        assert resp.status_code == 404


@pytest.mark.django_db
class TestBillingPortalView:
    def test_portal_requires_login(self, client):
        resp = client.get('/billing/portal/')
        assert resp.status_code == 302

    def test_portal_redirects_when_no_stripe_id(self, authenticated_client):
        resp = authenticated_client.get('/billing/portal/')
        assert resp.status_code == 302
