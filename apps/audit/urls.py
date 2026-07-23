from django.urls import path
from . import views

urlpatterns = [
    path('', views.audit_list, name='audit_list'),
    path('<int:log_id>/', views.audit_detail, name='audit_detail'),
    path('export/', views.audit_export, name='audit_export'),
]
