import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import {
  fetchAllPrompts,
  fetchPromptById,
  fetchReleaseCandidateById,
} from "../../api/client";
import { ErrorState } from "../../components/ErrorState";
import { LoadingSpinner } from "../../components/LoadingSpinner";
import { StatusBadge } from "../../components/StatusBadge";

function formatTimestamp(value: string) {
  return new Date(value).toLocaleString();
}

export function PromptVersionDetailPage() {
  const params = useParams();
  const promptId = Number(params.id);

  const promptQuery = useQuery({
    queryKey: ["prompt", promptId],
    queryFn: () => fetchPromptById(promptId),
    enabled: Number.isFinite(promptId),
  });

  const allPromptsQuery = useQuery({
    queryKey: ["prompts"],
    queryFn: fetchAllPrompts,
  });

  const linkedCandidateQuery = useQuery({
    queryKey: ["release-candidate", 1],
    queryFn: () => fetchReleaseCandidateById(1),
    retry: false,
  });

  const previousPrompt = useMemo(() => {
    const prompt = promptQuery.data;
    const allPrompts = allPromptsQuery.data ?? [];

    if (!prompt) {
      return null;
    }

    const candidates = allPrompts
      .filter((item) => item.ai_system === prompt.ai_system && item.id !== prompt.id)
      .sort((left, right) => left.id - right.id);

    const previous = candidates.filter((item) => item.id < prompt.id);
    return previous.length > 0 ? previous[previous.length - 1] : null;
  }, [allPromptsQuery.data, promptQuery.data]);

  if (!Number.isFinite(promptId)) {
    return <ErrorState message="The prompt id in the route is invalid." />;
  }

  if (promptQuery.isLoading || allPromptsQuery.isLoading) {
    return <LoadingSpinner label="Loading prompt detail..." />;
  }

  if (promptQuery.isError) {
    return <ErrorState message="The prompt detail could not be loaded from the backend API." />;
  }

  if (allPromptsQuery.isError) {
    return <ErrorState message="Prompt inventory could not be loaded from the backend API." />;
  }

  const prompt = promptQuery.data;

  if (!prompt) {
    return <ErrorState message="The requested prompt version was not returned by the backend API." />;
  }

  const linkedCandidate =
    linkedCandidateQuery.data &&
    linkedCandidateQuery.data.prompt_version === prompt.id
      ? linkedCandidateQuery.data
      : null;

  return (
    <section className="page-section">
      <div className="page-header">
        <div>
          <p className="eyebrow">Prompt Version</p>
          <h2>{prompt.name}</h2>
          <p className="muted">
            Governed prompt artefact with contracts and revision context.
          </p>
        </div>
        <Link className="secondary-link" to={`/systems/${prompt.ai_system}`}>
          Back to system
        </Link>
      </div>

      <div className="summary-grid">
        <div className="panel">
          <h3>Prompt metadata</h3>
          <dl className="definition-list">
            <div>
              <dt>System</dt>
              <dd>{prompt.ai_system_name}</dd>
            </div>
            <div>
              <dt>Version</dt>
              <dd>{prompt.version_label}</dd>
            </div>
            <div>
              <dt>Status</dt>
              <dd>
                <StatusBadge value={prompt.status} />
              </dd>
            </div>
            <div>
              <dt>Purpose</dt>
              <dd>{prompt.purpose}</dd>
            </div>
            <div>
              <dt>Schema version</dt>
              <dd>{prompt.schema_version}</dd>
            </div>
            <div>
              <dt>Created by</dt>
              <dd>{prompt.created_by_username ?? "Unknown"}</dd>
            </div>
            <div>
              <dt>Created</dt>
              <dd>{formatTimestamp(prompt.created_at)}</dd>
            </div>
          </dl>
        </div>

        <div className="panel">
          <h3>Linked release candidates</h3>
          {linkedCandidate ? (
            <div className="list-card">
              <strong>{linkedCandidate.name}</strong>
              <div className="table-subtext">Candidate ID: {linkedCandidate.id}</div>
              <div className="table-subtext">
                Status: {linkedCandidate.status}
              </div>
              <div className="spacer-sm" />
              <Link
                className="secondary-link"
                to={`/release-candidates/${linkedCandidate.id}`}
              >
                Open linked candidate
              </Link>
            </div>
          ) : (
            <p className="muted">
              No linked release candidate is currently surfaced by this frontend view.
            </p>
          )}
        </div>
      </div>

      <div className="panel">
        <h3>Prompt text excerpt</h3>
        <pre className="code-block">{prompt.template_text}</pre>
      </div>

      <div className="summary-grid">
        <div className="panel">
          <h3>Input contract</h3>
          <pre className="code-block">
            {JSON.stringify(prompt.input_contract, null, 2)}
          </pre>
        </div>

        <div className="panel">
          <h3>Output contract</h3>
          <pre className="code-block">
            {JSON.stringify(prompt.output_contract, null, 2)}
          </pre>
        </div>
      </div>

      <div className="panel">
        <h3>Diff against prior revision</h3>
        {previousPrompt ? (
          <div className="list-stack">
            <div className="list-card">
              <strong>Previous version</strong>
              <div className="table-subtext">
                {previousPrompt.version_label}
              </div>
            </div>
            <div className="list-card">
              <strong>Current version</strong>
              <div className="table-subtext">{prompt.version_label}</div>
            </div>
            <pre className="code-block">
{`--- previous
${previousPrompt.template_text}

+++ current
${prompt.template_text}`}
            </pre>
          </div>
        ) : (
          <p className="muted">No prior prompt revision was found for this system.</p>
        )}
      </div>
    </section>
  );
}