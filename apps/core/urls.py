from django.urls import path
from .views import home, dashboard, pricing, onboarding_wizard, onboarding_skip, help_page

urlpatterns = [
    path('', home, name='home'),
    path('dashboard/', dashboard, name='dashboard'),
    path('pricing/', pricing, name='pricing'),
    path('onboarding/', onboarding_wizard, name='onboarding_wizard'),
    path('onboarding/skip/', onboarding_skip, name='onboarding_skip'),
    path('help/', help_page, name='help_page'),
]
