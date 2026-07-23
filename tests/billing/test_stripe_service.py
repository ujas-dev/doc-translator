import pytest
from unittest.mock import patch, MagicMock
from apps.billing.services import StripeService


class TestStripeServiceGetClient:
    @patch('apps.billing.services.stripe')
    def test_get_stripe_client(self, mock_stripe):
        result = StripeService.get_stripe_client()
        assert result is mock_stripe


class TestStripeServiceCreateCustomer:
    @patch('apps.billing.services.stripe')
    def test_create_customer(self, mock_stripe, user):
        mock_stripe.Customer.create.return_value = {'id': 'cus_test123'}
        result = StripeService.create_customer(user)
        assert result == {'id': 'cus_test123'}
        mock_stripe.Customer.create.assert_called_once()

    @patch('apps.billing.services.stripe')
    def test_create_customer_passes_metadata(self, mock_stripe, user):
        mock_stripe.Customer.create.return_value = {'id': 'cus_test'}
        StripeService.create_customer(user)
        call_kwargs = mock_stripe.Customer.create.call_args[1]
        assert call_kwargs['metadata']['user_id'] == str(user.pk)


class TestStripeServiceCreateCheckoutSession:
    @patch('apps.billing.services.stripe')
    def test_create_checkout_session(self, mock_stripe, user, plan_pro):
        mock_stripe.checkout.Session.create.return_value = {'id': 'cs_test123'}
        result = StripeService.create_checkout_session(
            user, plan_pro, 'http://success/', 'http://cancel/'
        )
        assert result == 'cs_test123'

    @patch('apps.billing.services.stripe')
    def test_create_checkout_session_metadata(self, mock_stripe, user, plan_pro):
        mock_stripe.checkout.Session.create.return_value = {'id': 'cs_test'}
        StripeService.create_checkout_session(
            user, plan_pro, 'http://success/', 'http://cancel/'
        )
        call_kwargs = mock_stripe.checkout.Session.create.call_args[1]
        assert call_kwargs['metadata']['user_id'] == str(user.pk)
        assert call_kwargs['metadata']['plan_slug'] == plan_pro.slug


class TestStripeServiceCreatePortalSession:
    @patch('apps.billing.services.stripe')
    def test_create_portal_session(self, mock_stripe):
        mock_stripe.billing_portal.Session.create.return_value = {'url': 'https://portal.stripe.com'}
        result = StripeService.create_portal_session('cus_test', 'http://return/')
        assert result == 'https://portal.stripe.com'


class TestStripeServiceHandleWebhook:
    @patch('apps.billing.services.stripe')
    def test_handle_webhook_valid(self, mock_stripe):
        mock_stripe.Webhook.construct_event.return_value = {'type': 'checkout.session.completed'}
        result = StripeService.handle_webhook(b'payload', 'sig')
        assert result == {'type': 'checkout.session.completed'}

    @patch('apps.billing.services.stripe')
    def test_handle_webhook_invalid_signature(self, mock_stripe):
        mock_stripe.Webhook.construct_event.side_effect = Exception("Invalid signature")
        result = StripeService.handle_webhook(b'payload', 'bad_sig')
        assert result is None
