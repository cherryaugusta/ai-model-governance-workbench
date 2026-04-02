import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import {
  fetchAllModelConfigs,
  fetchAllPrompts,
  fetchSystemById,
} from "../../api/client";
import { ErrorState } from "../../components/ErrorState";
import { LoadingSpinner } from "../../components/LoadingSpinner";
import { StatusBadge } from "../../components/StatusBadge";

function formatTimestamp(value: string) {
  return new Date(value).toLocaleString();
}

export function SystemDetailPage() {
  const params = useParams();
  const systemId = Number(params.id);

  const systemQuery = useQuery({
    queryKey: ["system", systemId],
    queryFn: () => fetchSystemById(systemId),
    enabled: Number.isFinite(systemId),
  });

  const promptsQuery = useQuery({
    queryKey: ["prompts"],
    queryFn: fetchAllPrompts,
  });

  const modelConfigsQuery = useQuery({
    queryKey: ["model-configs"],
    queryFn: fetchAllModelConfigs,
  });

  const prompts = useMemo(() => {
    return (promptsQuery.data ?? []).filter((prompt) => prompt.ai_system === systemId);
  }, [promptsQuery.data, systemId]);

  const modelConfigs = useMemo(() => {
    return (modelConfigsQuery.data ?? []).filter(
      (modelConfig) => modelConfig.ai_system === systemId,
    );
  }, [modelConfigsQuery.data, systemId]);

  if (!Number.isFinite(systemId)) {
    return <ErrorState message="The system id in the route is invalid." />;
  }

  if (
    systemQuery.isLoading ||
    promptsQuery.isLoading ||
    modelConfigsQuery.isLoading
  ) {
    return <LoadingSpinner label="Loading system detail..." />;
  }

  if (systemQuery.isError) {
    return <ErrorState message="The system detail could not be loaded from the backend API." />;
  }

  if (promptsQuery.isError) {
    return <ErrorState message="Prompt versions could not be loaded from the backend API." />;
  }

  if (modelConfigsQuery.isError) {
    return <ErrorState message="Model configurations could not be loaded from the backend API." />;
  }

  const system = systemQuery.data;

  if (!system) {
    return <ErrorState message="The requested system was not returned by the backend API." />;
  }

  return (
    <section className="page-section">
      <div className="page-header">
        <div>
          <p className="eyebrow">System Detail</p>
          <h2>{system.name}</h2>
          <p className="muted">{system.description}</p>
        </div>
        <Link className="secondary-link" to="/">
          Back to systems
        </Link>
      </div>

      <div className="summary-grid">
        <div className="panel">
          <h3>Governance metadata</h3>
          <dl className="definition-list">
            <div>
              <dt>Slug</dt>
              <dd>{system.slug}</dd>
            </div>
            <div>
              <dt>Owner team</dt>
              <dd>{system.owner_team}</dd>
            </div>
            <div>
              <dt>Risk tier</dt>
              <dd>
                <StatusBadge value={system.risk_tier} />
              </dd>
            </div>
            <div>
              <dt>Status</dt>
              <dd>
                <StatusBadge value={system.status} />
              </dd>
            </div>
            <div>
              <dt>System type</dt>
              <dd>{system.system_type}</dd>
            </div>
            <div>
              <dt>Domain area</dt>
              <dd>{system.domain_area}</dd>
            </div>
            <div>
              <dt>Technical owner</dt>
              <dd>{system.technical_owner_username ?? "Unassigned"}</dd>
            </div>
            <div>
              <dt>Business owner</dt>
              <dd>{system.business_owner_username ?? "Unassigned"}</dd>
            </div>
            <div>
              <dt>Created</dt>
              <dd>{formatTimestamp(system.created_at)}</dd>
            </div>
            <div>
              <dt>Updated</dt>
              <dd>{formatTimestamp(system.updated_at)}</dd>
            </div>
          </dl>
        </div>

        <div className="panel">
          <h3>Active release</h3>
          {system.active_release_id ? (
            <p>Current active release id: {system.active_release_id}</p>
          ) : (
            <p className="muted">No active release yet.</p>
          )}
          <div className="spacer-sm" />
          <h3>Current governed artefacts</h3>
          <div className="stats-grid">
            <div className="stat-card">
              <span className="stat-label">Prompt versions</span>
              <strong className="stat-value">{prompts.length}</strong>
            </div>
            <div className="stat-card">
              <span className="stat-label">Model configs</span>
              <strong className="stat-value">{modelConfigs.length}</strong>
            </div>
            <div className="stat-card">
              <span className="stat-label">Eval summary</span>
              <strong className="stat-value">Pending</strong>
            </div>
            <div className="stat-card">
              <span className="stat-label">Incident summary</span>
              <strong className="stat-value">Pending</strong>
            </div>
          </div>
          <div className="spacer-sm" />
          <Link className="secondary-link" to="/release-candidates/1">
            Open release candidate 1
          </Link>
        </div>
      </div>

      <div className="panel">
        <h3>Prompt versions</h3>
        {prompts.length === 0 ? (
          <p className="muted">No prompt versions found for this system.</p>
        ) : (
          <div className="list-stack">
            {prompts.map((prompt) => (
              <div key={prompt.id} className="list-card">
                <div className="card-header">
                  <div>
                    <strong>{prompt.name}</strong>
                    <div className="table-subtext">
                      Version {prompt.version_label}
                    </div>
                  </div>
                  <StatusBadge value={prompt.status} />
                </div>
                <p className="muted">{prompt.purpose}</p>
                <div className="table-subtext">
                  Schema version: {prompt.schema_version}
                </div>
                <div className="table-subtext">
                  Created by: {prompt.created_by_username ?? "Unknown"}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="panel">
        <h3>Model configurations</h3>
        {modelConfigs.length === 0 ? (
          <p className="muted">No model configurations found for this system.</p>
        ) : (
          <div className="list-stack">
            {modelConfigs.map((modelConfig) => (
              <div key={modelConfig.id} className="list-card">
                <div className="card-header">
                  <div>
                    <strong>{modelConfig.provider_name}</strong>
                    <div className="table-subtext">
                      {modelConfig.model_name} | {modelConfig.version_label}
                    </div>
                  </div>
                  <StatusBadge value={modelConfig.status} />
                </div>
                <div className="table-subtext">
                  Max tokens: {modelConfig.max_tokens}
                </div>
                <div className="table-subtext">
                  Timeout: {modelConfig.timeout_ms} ms
                </div>
                <div className="table-subtext">
                  Created by: {modelConfig.created_by_username ?? "Unknown"}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
