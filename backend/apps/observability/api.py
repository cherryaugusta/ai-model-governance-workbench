from django.db.models import Avg, Count, Q
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.approvals.models import ApprovalRecord
from apps.core.choices import EvalRunStatus, IncidentSeverity, IncidentStatus
from apps.evals.models import EvalRun
from apps.incidents.models import Incident
from apps.observability.models import ModelExecutionLog
from apps.releases.models import ReleaseCandidate, RollbackRecord
from apps.systems.models import AISystem


class MetricsOverviewView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        active_systems = AISystem.objects.filter(status="active").count()
        pending_approvals = ApprovalRecord.objects.filter(decision="pending").count()
        blocked_promotions = ReleaseCandidate.objects.filter(
            status__in=["draft", "pending_eval", "eval_failed", "pending_approval"],
        ).count()
        failed_evals = EvalRun.objects.filter(status=EvalRunStatus.FAILED).count()
        rollback_count = RollbackRecord.objects.count()

        avg_eval_latency = (
            ModelExecutionLog.objects.aggregate(value=Avg("latency_ms"))["value"] or 0
        )

        open_incidents_by_severity = {
            "low": Incident.objects.filter(
                severity=IncidentSeverity.LOW,
                status__in=[
                    IncidentStatus.OPEN,
                    IncidentStatus.INVESTIGATING,
                    IncidentStatus.MITIGATED,
                ],
            ).count(),
            "medium": Incident.objects.filter(
                severity=IncidentSeverity.MEDIUM,
                status__in=[
                    IncidentStatus.OPEN,
                    IncidentStatus.INVESTIGATING,
                    IncidentStatus.MITIGATED,
                ],
            ).count(),
            "high": Incident.objects.filter(
                severity=IncidentSeverity.HIGH,
                status__in=[
                    IncidentStatus.OPEN,
                    IncidentStatus.INVESTIGATING,
                    IncidentStatus.MITIGATED,
                ],
            ).count(),
            "critical": Incident.objects.filter(
                severity=IncidentSeverity.CRITICAL,
                status__in=[
                    IncidentStatus.OPEN,
                    IncidentStatus.INVESTIGATING,
                    IncidentStatus.MITIGATED,
                ],
            ).count(),
        }

        incidents_by_release = list(
            Incident.objects.exclude(release_candidate=None)
            .values("release_candidate_id", "release_candidate__name")
            .annotate(count=Count("id"))
            .order_by("-count", "release_candidate_id")
        )

        release_blockers = {
            "latest_eval_failed": ReleaseCandidate.objects.filter(status="eval_failed").count(),
            "pending_approval": ReleaseCandidate.objects.filter(status="pending_approval").count(),
            "not_submitted": ReleaseCandidate.objects.filter(status="draft").count(),
            "awaiting_eval_results": ReleaseCandidate.objects.filter(status="pending_eval").count(),
        }

        response_payload = {
            "active_systems": active_systems,
            "pending_approvals": pending_approvals,
            "blocked_promotions": blocked_promotions,
            "failed_evals": failed_evals,
            "average_eval_latency_ms": round(float(avg_eval_latency), 2),
            "rollback_count": rollback_count,
            "open_incidents_by_severity": open_incidents_by_severity,
            "incidents_by_release": incidents_by_release,
            "release_blockers": release_blockers,
        }

        return Response(response_payload)