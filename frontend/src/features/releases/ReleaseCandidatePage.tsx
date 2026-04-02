import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { fetchReleaseCandidateById } from "../../api/client";
import { ErrorState } from "../../components/ErrorState";
import { LoadingSpinner } from "../../components/LoadingSpinner";
import { StatusBadge } from "../../components/StatusBadge";

function formatTimestamp(value: string) {
  return new Date(value).toLocaleString();
}

export function ReleaseCandidatePage() {
  const params = useParams();
  const candidateId = Number(params.id);

  const candidateQuery = useQuery({
    queryKey: ["release-candidate", candidateId],
    queryFn: () => fetchReleaseCandidateById(candidateId),
    enabled: Number.isFinite(candidateId),
  });

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
          <h3>Promotion readiness</h3>
          <div className="stats-grid">
            <div className="stat-card">
              <span className="stat-label">Can submit</span>
              <strong className="stat-value">{candidate.can_submit ? "Yes" : "No"}</strong>
            </div>
            <div className="stat-card">
              <span className="stat-label">Blocking reasons</span>
              <strong className="stat-value">{candidate.blocking_reasons.length}</strong>
            </div>
          </div>
          <div className="spacer-sm" />
          {candidate.blocking_reasons.length === 0 ? (
            <p className="muted">No blocking reasons currently reported.</p>
          ) : (
            <div className="list-stack">
              {candidate.blocking_reasons.map((reason) => (
                <div key={reason} className="list-card">
                  <StatusBadge value={reason} />
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="panel">
        <h3>Linked artefacts</h3>
        <div className="list-stack">
          <div className="list-card">
            <strong>Prompt version</strong>
            <div className="table-subtext">ID: {candidate.prompt_version}</div>
            <div className="table-subtext">Version: {candidate.prompt_version_label}</div>
          </div>
          <div className="list-card">
            <strong>Model config</strong>
            <div className="table-subtext">ID: {candidate.model_config}</div>
            <div className="table-subtext">Version: {candidate.model_config_version_label}</div>
          </div>
        </div>
      </div>

      <div className="panel">
        <h3>Config snapshot</h3>
        {Object.keys(candidate.config_snapshot).length === 0 ? (
          <p className="muted">No immutable snapshot has been created yet. Submit the candidate first.</p>
        ) : (
          <pre className="code-block">{JSON.stringify(candidate.config_snapshot, null, 2)}</pre>
        )}
      </div>
    </section>
  );
}
