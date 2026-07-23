from django.urls import path
from . import views

urlpatterns = [
    path('translate/', views.MCPTranslateView.as_view(), name='mcp-translate'),
    path('translate/document/', views.MCPTranslateDocView.as_view(), name='mcp-translate-doc'),
    path('glossary/', views.MCPGlossaryView.as_view(), name='mcp-glossary'),
    path('tm/search/', views.MCPTMSearchView.as_view(), name='mcp-tm-search'),
]
