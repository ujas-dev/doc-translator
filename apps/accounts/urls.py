from django.urls import path
from . import views

urlpatterns = [
    path('profile/', views.profile_view, name='profile'),
    path('api-keys/', views.api_keys_view, name='api-keys'),
    path('api-keys/<int:key_id>/delete/', views.delete_api_key_view, name='delete-api-key'),
]
