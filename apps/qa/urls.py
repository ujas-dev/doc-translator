from django.urls import path
from . import views

urlpatterns = [
    path('', views.qa_dashboard, name='qa_dashboard'),
    path('<int:job_id>/', views.qa_review, name='qa_review'),
    path('<int:job_id>/check/', views.qa_run_check, name='qa_run_check'),
]
