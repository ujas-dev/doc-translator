import structlog
from django.conf import settings

logger = structlog.get_logger(__name__)


class StripeService:
    @staticmethod
    def get_stripe_client():
        import stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY
        return stripe

    @classmethod
    def create_customer(cls, user):
        stripe = cls.get_stripe_client()
        customer = stripe.Customer.create(
            email=user.email,
            name=user.username,
            metadata={'user_id': user.id},
        )
        return customer.id

    @classmethod
    def create_checkout_session(cls, user, plan, success_url, cancel_url):
        stripe = cls.get_stripe_client()
        session = stripe.checkout.Session.create(
            customer=user.subscription.stripe_customer_id if hasattr(user, 'subscription') else None,
            payment_method_types=['card'],
            line_items=[{
                'price': plan.stripe_price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={'user_id': user.id, 'plan_slug': plan.slug},
        )
        return session.id

    @classmethod
    def create_portal_session(cls, customer_id, return_url):
        stripe = cls.get_stripe_client()
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url,
        )
        return session.url

    @classmethod
    def handle_webhook(cls, payload, sig_header):
        stripe = cls.get_stripe_client()
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except stripe.error.SignatureVerificationError:
            logger.error("Invalid Stripe webhook signature")
            return None
        return event
