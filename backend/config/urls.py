from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

from apps.approvals.api import ApprovalRecordViewSet
from apps.audits.api import AuditEventViewSet
from apps.evals.api import EvalDatasetViewSet, EvalRunViewSet
from apps.health.views import deps, live, ready
from apps.incidents.api import IncidentViewSet
from apps.model_configs.api import ModelConfigViewSet
from apps.observability.api import MetricsOverviewView
from apps.prompts.api import PromptVersionViewSet
from apps.releases.api import ReleaseCandidateViewSet
from apps.systems.api import AISystemViewSet

router = DefaultRouter()
router.register("systems", AISystemViewSet, basename="systems")
router.register("prompts", PromptVersionViewSet, basename="prompts")
router.register("model-configs", ModelConfigViewSet, basename="model-configs")
router.register("release-candidates", ReleaseCandidateViewSet, basename="release-candidates")
router.register("eval-datasets", EvalDatasetViewSet, basename="eval-datasets")
router.register("eval-runs", EvalRunViewSet, basename="eval-runs")
router.register("approvals", ApprovalRecordViewSet, basename="approvals")
router.register("incidents", IncidentViewSet, basename="incidents")
router.register("audit-events", AuditEventViewSet, basename="audit-events")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/metrics/overview/", MetricsOverviewView.as_view(), name="metrics-overview"),
    path("api/", include(router.urls)),
    path("health/live", live),
    path("health/ready", ready),
    path("health/deps", deps),
]