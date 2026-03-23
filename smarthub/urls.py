from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

urlpatterns = [
    path("", lambda request: redirect("/dashboard/")),
    path("admin/", admin.site.urls),

    path("accounts/", include("accounts.urls")),
    path("dashboard/", include("dashboard.urls")),
    path("api/", include("smarthub.api_urls")),
]

# Optional Swagger (only if drf-spectacular is installed & enabled)
try:
    from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

    urlpatterns += [
        path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
        path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    ]
except Exception:
    pass

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)