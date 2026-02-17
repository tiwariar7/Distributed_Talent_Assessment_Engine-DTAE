"""Root URL configuration."""

from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

from django.http import HttpResponse

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("", TemplateView.as_view(template_name="candidate.html"), name="candidate-ui"),
    path("admin/", admin.site.urls),
    path("metrics", lambda r: HttpResponse(), name="prometheus-metrics"),
    path("health/", include("apps.health.urls")),
    path("api/v1/auth/", include("apps.accounts.urls")),
    path("api/v1/assessments/", include("apps.assessments.urls")),
    path("api/v1/recruiter/", include("apps.recruiter.urls")),
    path("api/v1/executions/", include("apps.executions.urls")),
    path("api/v1/leaderboard/", include("apps.leaderboard.urls")),
    path("api/v1/dsa-intelligence/", include("apps.dsa_intelligence.urls")),
    path("api/v1/proctoring/", include("apps.proctoring.urls")),
] + static("/static/", document_root=settings.STATICFILES_DIRS[0])


# Refactor: Improve error handling and exception logging.
