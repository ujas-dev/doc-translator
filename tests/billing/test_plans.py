import pytest
from decimal import Decimal

from apps.billing.models import Plan, Subscription, Invoice
from apps.accounts.models import UserProfile


@pytest.mark.django_db
class TestPlanModel:
    def test_plan_creation(self, plan_free):
        assert plan_free.name == "Free"
        assert plan_free.slug == "free"
        assert plan_free.price_monthly == Decimal("0")

    def test_plan_str(self, plan_free):
        assert "Free" in str(plan_free)
        assert "$0" in str(plan_free)

    def test_plan_str_pro(self, plan_pro):
        assert "Pro" in str(plan_pro)
        assert "$19" in str(plan_pro)

    def test_plan_ordering(self, plan_free, plan_pro, plan_team, plan_enterprise):
        plans = list(Plan.objects.all())
        assert plans[0].slug == "free"
        assert plans[1].slug == "enterprise"
        assert plans[2].slug == "pro"
        assert plans[3].slug == "team"

    def test_plan_features(self, plan_pro):
        assert "pdf_layout" in plan_pro.features
        assert "glossary" in plan_pro.features

    def test_plan_defaults(self, db):
        p = Plan.objects.create(name="Custom", slug="custom")
        assert p.price_monthly == Decimal("0")
        assert p.is_active is True

    def test_plan_unique_slug(self, plan_free):
        with pytest.raises(Exception):
            Plan.objects.create(name="Free 2", slug="free")

    def test_plan_unique_name(self, plan_free):
        with pytest.raises(Exception):
            Plan.objects.create(name="Free", slug="free-2")


@pytest.mark.django_db
class TestSubscriptionModel:
    def test_subscription_creation(self, user, plan_free):
        sub = Subscription.objects.create(user=user, plan=plan_free, status="active")
        assert sub.pk is not None
        assert sub.plan == plan_free

    def test_subscription_str(self, user, plan_free):
        sub = Subscription.objects.create(user=user, plan=plan_free, status="active")
        s = str(sub)
        assert "testuser" in s
        assert "Free" in s
        assert "active" in s

    def test_subscription_status_choices(self, user, plan_free):
        for status in ("active", "canceled", "past_due", "trialing"):
            sub = Subscription.objects.create(user=user, plan=plan_free, status=status)
            assert sub.status == status
            sub.delete()

    def test_subscription_one_per_user(self, user, plan_free):
        Subscription.objects.create(user=user, plan=plan_free, status="active")
        with pytest.raises(Exception):
            Subscription.objects.create(user=user, plan=plan_free, status="canceled")

    def test_subscription_plan_nullable(self, user):
        sub = Subscription.objects.create(user=user, plan=None, status="active")
        assert sub.plan is None

    def test_subscription_cancel_at_period_end(self, user, plan_free):
        sub = Subscription.objects.create(
            user=user, plan=plan_free, cancel_at_period_end=True
        )
        assert sub.cancel_at_period_end is True


@pytest.mark.django_db
class TestInvoiceModel:
    def test_invoice_creation(self, user):
        inv = Invoice.objects.create(
            user=user, stripe_invoice_id="inv_test123",
            amount=Decimal("19.00"), currency="usd",
            status="paid", invoice_url="https://invoice.stripe.com/test",
        )
        assert inv.pk is not None

    def test_invoice_str(self, user):
        inv = Invoice.objects.create(
            user=user, stripe_invoice_id="inv_test123",
            amount=Decimal("19.00"), currency="usd",
            status="paid",
        )
        assert "inv_test123" in str(inv)
        assert "$19" in str(inv)

    def test_invoice_unique_stripe_id(self, user):
        Invoice.objects.create(
            user=user, stripe_invoice_id="inv_unique",
            amount=Decimal("19.00"), status="paid",
        )
        with pytest.raises(Exception):
            Invoice.objects.create(
                user=user, stripe_invoice_id="inv_unique",
                amount=Decimal("19.00"), status="paid",
            )

    def test_invoice_default_currency(self, user):
        inv = Invoice.objects.create(
            user=user, stripe_invoice_id="inv_curr",
            amount=Decimal("10.00"), status="paid",
        )
        assert inv.currency == "usd"
