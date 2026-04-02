import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import axios from "axios";
import { useMemo, useState } from "react";
import type { FormEvent } from "react";
import { Link, useParams } from "react-router-dom";
import {
  fetchReleaseCandidateById,
  promoteReleaseCandidate,
  rollbackReleaseCandidate,
} from "../../api/client";
import { ErrorState } from "../../components/ErrorState";
import { LoadingSpinner } from "../../components/LoadingSpinner";
import { StatusBadge } from "../../components/StatusBadge";

function formatTimestamp(value: string) {
  return new Date(value).toLocaleString();
}

function formatReasonLabel(value: string) {
  return value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function extractApiMessage(error: unknown) {
  if (axios.isAxiosError(error)) {
    const responseData = error.response?.data;

    if (typeof responseData === "string") {
      return responseData;
    }

    if (responseData && typeof responseData === "object") {
      const message =
        "message" in responseData && typeof responseData.message === "string"
          ? responseData.message
          : "";

      const details =
        "details" in responseData &&
        responseData.details &&
        typeof responseData.details === "object"
          ? responseData.details
          : undefined;

      const rawBlockingReasons =
        details &&
        "blocking_reasons" in details &&
        Array.isArray(details.blocking_reasons)
          ? details.blocking_reasons
          : [];

      const blockingReasons = rawBlockingReasons.filter(
        (reason: unknown): reason is string => typeof reason === "string",
      );

      if (message && blockingReasons.length > 0) {
        return `${message} Blocking reasons: ${blockingReasons.join(", ")}`;
      }

      if (message) {
        return message;
      }
    }
  }

  return "The action could not be completed.";
}

export function ReleaseCandidatePage() {
  const params = useParams();
  const candidateId = Number(params.id);
  const queryClient = useQueryClient();

  const [promotionReason, setPromotionReason] = useState("");
  const [rollbackReasonCode, setRollbackReasonCode] = useState("manual_revert");
  const [rollbackComment, setRollbackComment] = useState("");
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const candidateQuery = useQuery({
    queryKey: ["release-candidate", candidateId],
    queryFn: () => fetchReleaseCandidateById(candidateId),
    enabled: Number.isFinite(candidateId),
  });

  const promoteMutation = useMutation({
    mutationFn: () =>
      promoteReleaseCandidate(candidateId, { reason: promotionReason }),
    onSuccess: async () => {
      setActionMessage("Release candidate promoted successfully.");
      await queryClient.invalidateQueries({
        queryKey: ["release-candidate", candidateId],
      });
    },
    onError: (error) => {
      setActionMessage(extractApiMessage(error));
    },
  });

  const rollbackMutation = useMutation({
    mutationFn: () =>
      rollbackReleaseCandidate(candidateId, {
        reason_code: rollbackReasonCode,
        comment: rollbackComment,
      }),
    onSuccess: async (result) => {
      setActionMessage(
        `Rollback completed successfully. Active release restored to ${result.to_candidate.name}.`,
      );
      await queryClient.invalidateQueries({
        queryKey: ["release-candidate", candidateId],
      });
    },
    onError: (error) => {
      setActionMessage(extractApiMessage(error));
    },
  });

  const approvalSummary = candidateQuery.data?.approval_summary;

  const missingApprovalTypes = useMemo(() => {
    return approvalSummary?.missing_types ?? [];
  }, [approvalSummary]);

  if (!Number.isFinite(candidateId)) {
    return <ErrorState message="The release candidate id in the route is invalid." />;
  }

  if (candidateQuery.isLoading) {
    return <LoadingSpinner label="Loading release candidate..." />;
  }

  if (candidateQuery.isError) {
    return <ErrorState message="The release candidate could not be loaded from the backend API." />;
  }

  const candidate = candidateQuery.data;

  if (!candidate) {
    return <ErrorState message="The requested release candidate was not returned by the backend API." />;
  }

  const isPromoteBlocked = !candidate.can_promote;
  const isRollbackBlocked = !candidate.can_rollback;
  const isMutating = promoteMutation.isPending || rollbackMutation.isPending;

  function handlePromoteSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setActionMessage(null);
    promoteMutation.mutate();
  }

  function handleRollbackSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setActionMessage(null);
    rollbackMutation.mutate();
  }

  return (
    <section className="page-section">
      <div className="page-header">
        <div>
          <p className="eyebrow">Release Candidate</p>
          <h2>{candidate.name}</h2>
          <p className="muted">
            Immutable release candidate snapshot for governed AI promotion flow.
          </p>
        </div>
        <Link className="secondary-link" to={`/systems/${candidate.ai_system}`}>
          Back to system
        </Link>
      </div>

      <div className="summary-grid">
        <div className="panel">
          <h3>Candidate summary</h3>
          <dl className="definition-list">
            <div>
              <dt>System</dt>
              <dd>{candidate.ai_system_name}</dd>
            </div>
            <div>
              <dt>Status</dt>
              <dd>
                <StatusBadge value={candidate.status} />
              </dd>
            </div>
            <div>
              <dt>Prompt version</dt>
              <dd>{candidate.prompt_version_label}</dd>
            </div>
            <div>
              <dt>Model config</dt>
              <dd>{candidate.model_config_version_label}</dd>
            </div>
            <div>
              <dt>Created by</dt>
              <dd>{candidate.created_by_username ?? "Unknown"}</dd>
            </div>
            <div>
              <dt>Created</dt>
              <dd>{formatTimestamp(candidate.created_at)}</dd>
            </div>
            <div>
              <dt>Updated</dt>
              <dd>{formatTimestamp(candidate.updated_at)}</dd>
            </div>
          </dl>
        </div>

        <div className="panel">
          <h3>Governance readiness</h3>
          <div className="stats-grid">
            <div className="stat-card">
              <span className="stat-label">Can submit</span>
              <strong className="stat-value">{candidate.can_submit ? "Yes" : "No"}</strong>
            </div>
            <div className="stat-card">
              <span className="stat-label">Can run evals</span>
              <strong className="stat-value">{candidate.can_run_evals ? "Yes" : "No"}</strong>
            </div>
            <div className="stat-card">
              <span className="stat-label">Can request approval</span>
              <strong className="stat-value">
                {candidate.can_request_approval ? "Yes" : "No"}
              </strong>
            </div>
            <div className="stat-card">
              <span className="stat-label">Can promote</span>
              <strong className="stat-value">{candidate.can_promote ? "Yes" : "No"}</strong>
            </div>
            <div className="stat-card">
              <span className="stat-label">Can rollback</span>
              <strong className="stat-value">{candidate.can_rollback ? "Yes" : "No"}</strong>
            </div>
            <div className="stat-card">
              <span className="stat-label">Blocking reasons</span>
              <strong className="stat-value">{candidate.blocking_reasons.length}</strong>
            </div>
          </div>
        </div>
      </div>

      {actionMessage ? (
        <div className="panel">
          <h3>Latest action result</h3>
          <p>{actionMessage}</p>
        </div>
      ) : null}

      <div className="panel">
        <h3>Promotion and rollback blockers</h3>
        {candidate.blocking_reasons.length === 0 ? (
          <p className="muted">No blocking reasons are currently reported.</p>
        ) : (
          <div className="list-stack">
            {candidate.blocking_reasons.map((reason) => (
              <div key={reason} className="list-card">
                <strong>{formatReasonLabel(reason)}</strong>
                <div className="table-subtext">{reason}</div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="summary-grid">
        <div className="panel">
          <h3>Approval state</h3>
          <dl className="definition-list">
            <div>
              <dt>Required approval types</dt>
              <dd>
                {candidate.required_approval_types.length > 0
                  ? candidate.required_approval_types.join(", ")
                  : "None"}
              </dd>
            </div>
            <div>
              <dt>Approval complete</dt>
              <dd>{approvalSummary?.is_complete ? "Yes" : "No"}</dd>
            </div>
            <div>
              <dt>Missing approval types</dt>
              <dd>
                {missingApprovalTypes.length > 0
                  ? missingApprovalTypes.join(", ")
                  : "None"}
              </dd>
            </div>
          </dl>
        </div>

        <div className="panel">
          <h3>Linked artefacts</h3>
          <div className="list-stack">
            <div className="list-card">
              <strong>Prompt version</strong>
              <div className="table-subtext">ID: {candidate.prompt_version}</div>
              <div className="table-subtext">
                Version: {candidate.prompt_version_label}
              </div>
            </div>
            <div className="list-card">
              <strong>Model config</strong>
              <div className="table-subtext">ID: {candidate.model_config}</div>
              <div className="table-subtext">
                Version: {candidate.model_config_version_label}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="summary-grid">
        <div className="panel">
          <h3>Promote release candidate</h3>
          {isPromoteBlocked ? (
            <div className="list-card">
              <strong>Promotion is blocked.</strong>
              <div className="table-subtext">
                Resolve the reported blocking reasons before promoting this candidate.
              </div>
            </div>
          ) : (
            <div className="list-card">
              <strong>Promotion is currently allowed.</strong>
              <div className="table-subtext">
                All deterministic governance gates currently pass for this candidate.
              </div>
            </div>
          )}

          <form className="list-stack" onSubmit={handlePromoteSubmit}>
            <label className="field-group">
              <span>Promotion reason</span>
              <textarea
                value={promotionReason}
                onChange={(event) => setPromotionReason(event.target.value)}
                rows={4}
                placeholder="Enter the release promotion rationale."
              />
            </label>
            <button type="submit" disabled={isPromoteBlocked || isMutating}>
              {promoteMutation.isPending ? "Promoting..." : "Promote candidate"}
            </button>
          </form>
        </div>

        <div className="panel">
          <h3>Rollback active release</h3>
          {isRollbackBlocked ? (
            <div className="list-card">
              <strong>Rollback is blocked.</strong>
              <div className="table-subtext">
                Rollback is available only when this candidate is active and a rollback target exists.
              </div>
            </div>
          ) : (
            <div className="list-card">
              <strong>Rollback is currently allowed.</strong>
              <div className="table-subtext">
                A previous compatible release is available as the rollback target.
              </div>
            </div>
          )}

          <form className="list-stack" onSubmit={handleRollbackSubmit}>
            <label className="field-group">
              <span>Rollback reason code</span>
              <select
                value={rollbackReasonCode}
                onChange={(event) => setRollbackReasonCode(event.target.value)}
              >
                <option value="manual_revert">manual_revert</option>
                <option value="incident_response">incident_response</option>
                <option value="latency_breach">latency_breach</option>
                <option value="budget_breach">budget_breach</option>
                <option value="quality_regression">quality_regression</option>
              </select>
            </label>

            <label className="field-group">
              <span>Rollback comment</span>
              <textarea
                value={rollbackComment}
                onChange={(event) => setRollbackComment(event.target.value)}
                rows={4}
                placeholder="Enter the rollback rationale and operational context."
              />
            </label>

            <button type="submit" disabled={isRollbackBlocked || isMutating}>
              {rollbackMutation.isPending ? "Rolling back..." : "Rollback candidate"}
            </button>
          </form>
        </div>
      </div>

      <div className="panel">
        <h3>Config snapshot</h3>
        {Object.keys(candidate.config_snapshot).length === 0 ? (
          <p className="muted">
            No immutable snapshot has been created yet. Submit the candidate first.
          </p>
        ) : (
          <pre className="code-block">
            {JSON.stringify(candidate.config_snapshot, null, 2)}
          </pre>
        )}
      </div>
    </section>
  );
}
