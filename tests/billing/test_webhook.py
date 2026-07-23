import json
from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.test import RequestFactory

from apps.billing.models import Plan, Subscription, Invoice
from apps.billing.views import (
    stripe_webhook,
    handle_checkout_completed,
    handle_subscription_updated,
    handle_subscription_deleted,
    handle_invoice_paid,
)
from apps.accounts.models import UserProfile


@pytest.mark.django_db
class TestCheckoutCompleted:
    def test_creates_subscription(self, user, plan_pro):
        session = {
            "metadata": {"user_id": str(user.pk), "plan_slug": "pro"},
            "subscription": "sub_test123",
            "customer": "cus_test123",
        }
        handle_checkout_completed(session)
        sub = Subscription.objects.get(user=user)
        assert sub.plan == plan_pro
        assert sub.stripe_subscription_id == "sub_test123"
        assert sub.status == "active"

    def test_updates_profile_plan(self, user, plan_pro):
        session = {
            "metadata": {"user_id": str(user.pk), "plan_slug": "pro"},
            "subscription": "sub_test123",
            "customer": "cus_test123",
        }
        handle_checkout_completed(session)
        user.profile.refresh_from_db()
        assert user.profile.plan == "pro"

    def test_missing_metadata_noop(self, user):
        handle_checkout_completed({})
        assert not Subscription.objects.filter(user=user).exists()

    def test_nonexistent_user_noop(self, plan_pro):
        session = {
            "metadata": {"user_id": "99999", "plan_slug": "pro"},
            "subscription": "sub_test",
            "customer": "cus_test",
        }
        handle_checkout_completed(session)


@pytest.mark.django_db
class TestSubscriptionUpdated:
    def test_updates_status(self, user, plan_free):
        sub = Subscription.objects.create(
            user=user, plan=plan_free, stripe_subscription_id="sub_update", status="active"
        )
        handle_subscription_updated({"id": "sub_update", "status": "past_due"})
        sub.refresh_from_db()
        assert sub.status == "past_due"

    def test_updates_profile_plan(self, user, plan_pro):
        sub = Subscription.objects.create(
            user=user, plan=plan_pro, stripe_subscription_id="sub_sync", status="active"
        )
        handle_subscription_updated({"id": "sub_sync", "status": "active"})
        user.profile.refresh_from_db()
        assert user.profile.plan == "pro"

    def test_nonexistent_subscription_noop(self):
        handle_subscription_updated({"id": "nonexistent", "status": "active"})


@pytest.mark.django_db
class TestSubscriptionDeleted:
    def test_sets_canceled(self, user, plan_pro):
        sub = Subscription.objects.create(
            user=user, plan=plan_pro, stripe_subscription_id="sub_del", status="active"
        )
        handle_subscription_deleted({"id": "sub_del"})
        sub.refresh_from_db()
        assert sub.status == "canceled"

    def test_resets_profile_to_free(self, user, plan_pro):
        sub = Subscription.objects.create(
            user=user, plan=plan_pro, stripe_subscription_id="sub_del2", status="active"
        )
        user.profile.plan = "pro"
        user.profile.save()
        handle_subscription_deleted({"id": "sub_del2"})
        user.profile.refresh_from_db()
        assert user.profile.plan == "free"


@pytest.mark.django_db
class TestInvoicePaid:
    def test_creates_invoice(self, user, plan_free):
        Subscription.objects.create(
            user=user, plan=plan_free, stripe_customer_id="cus_inv", status="active"
        )
        handle_invoice_paid({
            "id": "inv_new",
            "customer": "cus_inv",
            "amount_paid": 1900,
            "currency": "usd",
            "status": "paid",
            "hosted_invoice_url": "https://inv.stripe.com/test",
        })
        inv = Invoice.objects.get(stripe_invoice_id="inv_new")
        assert inv.amount == Decimal("19.00")
        assert inv.user == user

    def test_nonexistent_customer_noop(self):
        handle_invoice_paid({
            "id": "inv_orphan",
            "customer": "cus_nonexistent",
            "amount_paid": 1000,
            "status": "paid",
        })
        assert not Invoice.objects.filter(stripe_invoice_id="inv_orphan").exists()


@pytest.mark.django_db
class TestStripeWebhook:
    def test_webhook_no_config(self, client):
        resp = client.post(
            "/billing/webhook/stripe/",
            data=json.dumps({"type": "checkout.session.completed"}),
            content_type="application/json",
        )
        assert resp.status_code == 400
