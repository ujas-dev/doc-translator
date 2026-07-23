from django.urls import path
from . import views

urlpatterns = [
    path('', views.team_list, name='team_list'),
    path('create/', views.team_create, name='team_create'),
    path('<int:team_id>/', views.team_detail, name='team_detail'),
    path('<int:team_id>/settings/', views.team_settings, name='team_settings'),
    path('<int:team_id>/usage/', views.team_usage, name='team_usage'),
    path('<int:team_id>/members/add/', views.team_add_member, name='team_add_member'),
    path('<int:team_id>/members/<int:member_id>/remove/', views.team_remove_member, name='team_remove_member'),
    path('<int:team_id>/leave/', views.team_leave, name='team_leave'),
]
