from django.urls import path
from . import views

urlpatterns = [
    path('checkout/<str:plan_slug>/', views.checkout, name='billing-checkout'),
    path('portal/', views.customer_portal, name='billing-portal'),
    path('webhook/stripe/', views.stripe_webhook, name='stripe-webhook'),
]
