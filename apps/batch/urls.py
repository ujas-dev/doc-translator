from django.urls import path
from . import views

urlpatterns = [
    path('', views.batch_list, name='batch_list'),
    path('upload/', views.batch_upload, name='batch_upload'),
    path('<int:batch_id>/', views.batch_detail, name='batch_detail'),
    path('<int:batch_id>/download/', views.batch_download, name='batch_download'),
    path('<int:batch_id>/status/', views.batch_status, name='batch_status'),

    path('api/', views.BatchJobListCreateView.as_view(), name='api-batch-list'),
    path('api/<int:pk>/', views.BatchJobStatusView.as_view(), name='api-batch-detail'),
]
