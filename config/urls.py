from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from apps.accounts.views import register_view, login_view


def health(_request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path('health/', health, name='health'),
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('', include('apps.core.urls')),
    path('api/', include('apps.documents.urls')),
    path('', include('apps.accounts.urls')),
    path('billing/', include('apps.billing.urls')),
    path('glossaries/', include('apps.glossaries.urls')),
    path('tm/', include('apps.memory.urls')),
    path('status/', include('apps.status.urls')),
    path('qa/', include('apps.qa.urls')),
    path('batch/', include('apps.batch.urls')),
    path('teams/', include('apps.teams.urls')),
    path('api/mcp/', include('apps.mcp.urls')),
    path('audit/', include('apps.audit.urls')),
    path('login/', login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('register/', register_view, name='register'),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)