import json
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import Subscription, Plan, Invoice
from .services import StripeService


@login_required
def checkout(request, plan_slug):
    plan = get_object_or_404(Plan, slug=plan_slug)
    if plan.price_monthly == 0:
        return redirect('pricing')

    if not settings.STRIPE_SECRET_KEY:
        profile = getattr(request.user, 'profile', None)
        if profile:
            plan_order = {'free': 0, 'pro': 1, 'team': 2, 'enterprise': 3}
            current_level = plan_order.get(profile.plan or 'free', 0)
            new_level = plan_order.get(plan.slug, 0)
            if new_level > current_level:
                profile.plan = plan.slug
                profile.save(update_fields=['plan'])
        return redirect('dashboard')

    success_url = request.build_absolute_uri('/dashboard/') + '?upgraded=1'
    cancel_url = request.build_absolute_uri('/pricing/')

    try:
        session_id = StripeService.create_checkout_session(
            request.user, plan, success_url, cancel_url
        )
        stripe = StripeService.get_stripe_client()
        session = stripe.checkout.Session.retrieve(session_id)
        return redirect(session.url)
    except Exception:
        return redirect('pricing')


@login_required
def customer_portal(request):
    profile = getattr(request.user, 'profile', None)
    if not profile or not profile.stripe_customer_id:
        return redirect('pricing')

    return_url = request.build_absolute_uri('/dashboard/')

    try:
        portal_url = StripeService.create_portal_session(
            profile.stripe_customer_id, return_url
        )
        return redirect(portal_url)
    except Exception:
        return redirect('dashboard')


@csrf_exempt
@require_POST
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

    if not settings.STRIPE_WEBHOOK_SECRET:
        return HttpResponseBadRequest("Stripe not configured")

    event = StripeService.handle_webhook(payload, sig_header)
    if event is None:
        return HttpResponseBadRequest("Invalid signature")

    if event['type'] == 'checkout.session.completed':
        handle_checkout_completed(event['data']['object'])
    elif event['type'] == 'customer.subscription.updated':
        handle_subscription_updated(event['data']['object'])
    elif event['type'] == 'customer.subscription.deleted':
        handle_subscription_deleted(event['data']['object'])
    elif event['type'] == 'invoice.paid':
        handle_invoice_paid(event['data']['object'])

    return HttpResponse(status=200)


def handle_checkout_completed(session):
    from django.contrib.auth.models import User
    user_id = session.get('metadata', {}).get('user_id')
    plan_slug = session.get('metadata', {}).get('plan_slug')

    if not user_id or not plan_slug:
        return

    try:
        user = User.objects.get(pk=user_id)
        plan = Plan.objects.get(slug=plan_slug)
        subscription, _ = Subscription.objects.get_or_create(user=user)
        subscription.plan = plan
        subscription.stripe_subscription_id = session.get('subscription')
        subscription.stripe_customer_id = session.get('customer')
        subscription.status = 'active'
        subscription.save()

        profile = getattr(user, 'profile', None)
        if profile:
            profile.plan = plan.slug
            profile.stripe_customer_id = session.get('customer')
            profile.save()
    except Exception:
        pass


def handle_subscription_updated(subscription):
    from apps.accounts.models import UserProfile
    stripe_sub_id = subscription.get('id')
    status = subscription.get('status')

    try:
        sub = Subscription.objects.get(stripe_subscription_id=stripe_sub_id)
        sub.status = status
        sub.save()

        profile = UserProfile.objects.filter(user=sub.user).first()
        if profile:
            profile.plan = sub.plan.slug if sub.plan else 'free'
            profile.save()
    except Subscription.DoesNotExist:
        pass


def handle_subscription_deleted(subscription):
    from apps.accounts.models import UserProfile
    stripe_sub_id = subscription.get('id')

    try:
        sub = Subscription.objects.get(stripe_subscription_id=stripe_sub_id)
        sub.status = 'canceled'
        sub.save()

        profile = UserProfile.objects.filter(user=sub.user).first()
        if profile:
            profile.plan = 'free'
            profile.save()
    except Subscription.DoesNotExist:
        pass


def handle_invoice_paid(invoice):
    try:
        customer_id = invoice.get('customer')
        sub = Subscription.objects.get(stripe_customer_id=customer_id)
        Invoice.objects.create(
            user=sub.user,
            stripe_invoice_id=invoice.get('id'),
            amount=invoice.get('amount_paid', 0) / 100,
            currency=invoice.get('currency', 'usd'),
            status=invoice.get('status'),
            invoice_url=invoice.get('hosted_invoice_url', ''),
        )
    except Exception:
        pass
