import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import {
  fetchAllReleaseCandidates,
  fetchModelConfigById,
} from "../../api/client";
import { ErrorState } from "../../components/ErrorState";
import { LoadingSpinner } from "../../components/LoadingSpinner";
import { StatusBadge } from "../../components/StatusBadge";

function formatTimestamp(value: string) {
  return new Date(value).toLocaleString();
}

export function ModelConfigDetailPage() {
  const params = useParams();
  const modelConfigId = Number(params.id);

  const modelConfigQuery = useQuery({
    queryKey: ["model-config", modelConfigId],
    queryFn: () => fetchModelConfigById(modelConfigId),
    enabled: Number.isFinite(modelConfigId),
  });

  const releaseCandidatesQuery = useQuery({
    queryKey: ["release-candidates"],
    queryFn: fetchAllReleaseCandidates,
  });

  const linkedCandidates = useMemo(() => {
    const modelConfig = modelConfigQuery.data;
    const releaseCandidates = releaseCandidatesQuery.data ?? [];

    if (!modelConfig) {
      return [];
    }

    return releaseCandidates
      .filter((candidate) => candidate.model_config === modelConfig.id)
      .sort((left, right) => right.id - left.id);
  }, [modelConfigQuery.data, releaseCandidatesQuery.data]);

  if (!Number.isFinite(modelConfigId)) {
    return <ErrorState message="The model configuration id in the route is invalid." />;
  }

  if (modelConfigQuery.isLoading || releaseCandidatesQuery.isLoading) {
    return <LoadingSpinner label="Loading model configuration detail..." />;
  }

  if (modelConfigQuery.isError) {
    return <ErrorState message="The model configuration detail could not be loaded from the backend API." />;
  }

  if (releaseCandidatesQuery.isError) {
    return <ErrorState message="Linked release candidates could not be loaded from the backend API." />;
  }

  const modelConfig = modelConfigQuery.data;

  if (!modelConfig) {
    return <ErrorState message="The requested model configuration was not returned by the backend API." />;
  }

  return (
    <section className="page-section">
      <div className="page-header">
        <div>
          <p className="eyebrow">Model Configuration</p>
          <h2>
            {modelConfig.provider_name} {modelConfig.model_name}
          </h2>
          <p className="muted">
            Governed runtime configuration for release-safe AI behavior.
          </p>
        </div>
        <Link className="secondary-link" to={`/systems/${modelConfig.ai_system}`}>
          Back to system
        </Link>
      </div>

      <div className="summary-grid">
        <div className="panel">
          <h3>Configuration metadata</h3>
          <dl className="definition-list">
            <div>
              <dt>System</dt>
              <dd>{modelConfig.ai_system_name}</dd>
            </div>
            <div>
              <dt>Version</dt>
              <dd>{modelConfig.version_label}</dd>
            </div>
            <div>
              <dt>Status</dt>
              <dd>
                <StatusBadge value={modelConfig.status} />
              </dd>
            </div>
            <div>
              <dt>Provider</dt>
              <dd>{modelConfig.provider_name}</dd>
            </div>
            <div>
              <dt>Model</dt>
              <dd>{modelConfig.model_name}</dd>
            </div>
            <div>
              <dt>Temperature</dt>
              <dd>{String(modelConfig.temperature)}</dd>
            </div>
            <div>
              <dt>Top p</dt>
              <dd>{String(modelConfig.top_p)}</dd>
            </div>
            <div>
              <dt>Max tokens</dt>
              <dd>{modelConfig.max_tokens}</dd>
            </div>
            <div>
              <dt>Timeout ms</dt>
              <dd>{modelConfig.timeout_ms}</dd>
            </div>
            <div>
              <dt>Cost budget per run</dt>
              <dd>{String(modelConfig.cost_budget_per_run)}</dd>
            </div>
            <div>
              <dt>Created by</dt>
              <dd>{modelConfig.created_by_username ?? "Unknown"}</dd>
            </div>
            <div>
              <dt>Created</dt>
              <dd>{formatTimestamp(modelConfig.created_at)}</dd>
            </div>
          </dl>
        </div>

        <div className="panel">
          <h3>Linked release candidates</h3>
          {linkedCandidates.length > 0 ? (
            <div className="list-stack">
              {linkedCandidates.map((candidate) => (
                <div key={candidate.id} className="list-card">
                  <strong>{candidate.name}</strong>
                  <div className="table-subtext">Candidate ID: {candidate.id}</div>
                  <div className="table-subtext">Status: {candidate.status}</div>
                  <div className="table-subtext">
                    Prompt version: {candidate.prompt_version_label}
                  </div>
                  <div className="spacer-sm" />
                  <Link
                    className="secondary-link"
                    to={`/release-candidates/${candidate.id}`}
                  >
                    Open linked candidate
                  </Link>
                </div>
              ))}
            </div>
          ) : (
            <p className="muted">
              No linked release candidates were found for this model configuration.
            </p>
          )}
        </div>
      </div>

      <div className="summary-grid">
        <div className="panel">
          <h3>Routing policy</h3>
          <pre className="code-block">
            {JSON.stringify(modelConfig.routing_policy, null, 2)}
          </pre>
        </div>

        <div className="panel">
          <h3>Fallback policy</h3>
          <pre className="code-block">
            {JSON.stringify(modelConfig.fallback_policy, null, 2)}
          </pre>
        </div>
      </div>
    </section>
  );
}