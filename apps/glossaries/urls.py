from django.urls import path
from . import views

urlpatterns = [
    path('', views.glossary_list, name='glossary_list'),
    path('create/', views.glossary_create, name='glossary_create'),
    path('suggest/', views.glossary_suggest, name='glossary_suggest'),
    path('<int:pk>/', views.glossary_detail, name='glossary_detail'),
    path('<int:pk>/delete/', views.glossary_delete, name='glossary_delete'),
    path('<int:pk>/export/', views.glossary_export, name='glossary_export'),
    path('<int:glossary_pk>/entry/<int:entry_pk>/delete/', views.entry_delete, name='entry_delete'),
]
