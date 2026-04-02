from django.db import models


class RiskTier(models.TextChoices):
    LOW = "low", "Low"
    MEDIUM = "medium", "Medium"
    HIGH = "high", "High"
    CRITICAL = "critical", "Critical"


class AISystemStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    ACTIVE = "active", "Active"
    PAUSED = "paused", "Paused"
    RETIRED = "retired", "Retired"


class ArtefactStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    CANDIDATE = "candidate", "Candidate"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"
    RETIRED = "retired", "Retired"


class ReleaseCandidateStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    PENDING_EVAL = "pending_eval", "Pending eval"
    EVAL_FAILED = "eval_failed", "Eval failed"
    PENDING_APPROVAL = "pending_approval", "Pending approval"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"
    ACTIVE = "active", "Active"
    ROLLED_BACK = "rolled_back", "Rolled back"
    RETIRED = "retired", "Retired"


class EvalRunStatus(models.TextChoices):
    QUEUED = "queued", "Queued"
    RUNNING = "running", "Running"
    PASSED = "passed", "Passed"
    FAILED = "failed", "Failed"
    CANCELLED = "cancelled", "Cancelled"


class IncidentStatus(models.TextChoices):
    OPEN = "open", "Open"
    INVESTIGATING = "investigating", "Investigating"
    MITIGATED = "mitigated", "Mitigated"
    RESOLVED = "resolved", "Resolved"
    CLOSED = "closed", "Closed"


class ApprovalType(models.TextChoices):
    TECHNICAL = "technical", "Technical"
    PRODUCT = "product", "Product"
    RISK = "risk", "Risk"
    GOVERNANCE = "governance", "Governance"


class ApprovalDecision(models.TextChoices):
    PENDING = "pending", "Pending"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"
    CHANGES_REQUESTED = "changes_requested", "Changes requested"


class IncidentSeverity(models.TextChoices):
    LOW = "low", "Low"
    MEDIUM = "medium", "Medium"
    HIGH = "high", "High"
    CRITICAL = "critical", "Critical"


class IncidentType(models.TextChoices):
    LATENCY_BREACH = "latency_breach", "Latency breach"
    COST_BREACH = "cost_breach", "Cost breach"
    QUALITY_REGRESSION = "quality_regression", "Quality regression"
    SCHEMA_FAILURE = "schema_failure", "Schema failure"
    MANUAL_REPORT = "manual_report", "Manual report"


class ActorType(models.TextChoices):
    USER = "user", "User"
    SYSTEM = "system", "System"
    TASK = "task", "Task"


class ExecutionStatus(models.TextChoices):
    SUCCESS = "success", "Success"
    FAILED = "failed", "Failed"
    FALLBACK_USED = "fallback_used", "Fallback used"
    TIMEOUT = "timeout", "Timeout"


class RollbackReasonCode(models.TextChoices):
    INCIDENT_RESPONSE = "incident_response", "Incident response"
    MANUAL_REVERT = "manual_revert", "Manual revert"
    BUDGET_BREACH = "budget_breach", "Budget breach"
    LATENCY_BREACH = "latency_breach", "Latency breach"
    QUALITY_REGRESSION = "quality_regression", "Quality regression"