from django.urls import path

from . import views

urlpatterns = [
    path('', views.public_status, name='status-public'),
    path('detail/', views.detail_status, name='status-detail'),
    path('check/<str:service_name>/', views.check_service, name='status-check-service'),
    path('check-all/', views.check_all_services, name='status-check-all'),
]
