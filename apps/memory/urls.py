from django.urls import path
from . import views

urlpatterns = [
    path('', views.tm_list, name='tm_list'),
    path('add/', views.tm_add, name='tm_add'),
    path('leverage/', views.tm_leverage, name='tm_leverage'),
    path('<int:pk>/delete/', views.tm_delete, name='tm_delete'),
    path('export/<str:source_lang>/<str:target_lang>/', views.tm_export, name='tm_export'),
]
