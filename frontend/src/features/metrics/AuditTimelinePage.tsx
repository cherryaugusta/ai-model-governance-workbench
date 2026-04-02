import { useQuery } from "@tanstack/react-query";
import { fetchAuditEvents, fetchMetricsOverview } from "../../api/client";
import { ErrorState } from "../../components/ErrorState";
import { LoadingSpinner } from "../../components/LoadingSpinner";
import { StatusBadge } from "../../components/StatusBadge";

function formatTimestamp(value: string) {
  return new Date(value).toLocaleString();
}

export function AuditTimelinePage() {
  const metricsQuery = useQuery({
    queryKey: ["metrics-overview"],
    queryFn: fetchMetricsOverview,
  });

  const auditEventsQuery = useQuery({
    queryKey: ["audit-events", "recent"],
    queryFn: () => fetchAuditEvents(),
  });

  if (metricsQuery.isLoading || auditEventsQuery.isLoading) {
    return <LoadingSpinner label="Loading audit and metrics overview" />;
  }

  if (metricsQuery.isError || auditEventsQuery.isError) {
    return (
      <ErrorState message="The audit and metrics overview could not be loaded from the backend API." />
    );
  }

  if (!metricsQuery.data) {
    return (
      <ErrorState message="The metrics overview response was empty." />
    );
  }

  const metrics = metricsQuery.data;
  const auditEvents = (auditEventsQuery.data ?? []).slice(0, 10);

  return (
    <section className="page-section">
      <div className="page-header">
        <p className="eyebrow">Audit and Metrics</p>
        <h2>Audit timeline and governance metrics</h2>
        <p>
          Release safety depends on visible operational evidence, immutable audit
          history, and clear blocker counts.
        </p>
      </div>

      <div className="stats-grid">
        <div className="panel">
          <p className="eyebrow">Active systems</p>
          <h3>{metrics.active_systems}</h3>
        </div>
        <div className="panel">
          <p className="eyebrow">Pending approvals</p>
          <h3>{metrics.pending_approvals}</h3>
        </div>
        <div className="panel">
          <p className="eyebrow">Blocked promotions</p>
          <h3>{metrics.blocked_promotions}</h3>
        </div>
        <div className="panel">
          <p className="eyebrow">Failed evals</p>
          <h3>{metrics.failed_evals}</h3>
        </div>
        <div className="panel">
          <p className="eyebrow">Average eval latency ms</p>
          <h3>{metrics.average_eval_latency_ms}</h3>
        </div>
        <div className="panel">
          <p className="eyebrow">Rollback count</p>
          <h3>{metrics.rollback_count}</h3>
        </div>
      </div>

      <div className="summary-grid">
        <div className="panel">
          <h3>Open incidents by severity</h3>
          <div className="list-stack">
            <div className="list-card">
              <strong>Low</strong>
              <div className="table-subtext">
                {metrics.open_incidents_by_severity.low}
              </div>
            </div>
            <div className="list-card">
              <strong>Medium</strong>
              <div className="table-subtext">
                {metrics.open_incidents_by_severity.medium}
              </div>
            </div>
            <div className="list-card">
              <strong>High</strong>
              <div className="table-subtext">
                {metrics.open_incidents_by_severity.high}
              </div>
            </div>
            <div className="list-card">
              <strong>Critical</strong>
              <div className="table-subtext">
                {metrics.open_incidents_by_severity.critical}
              </div>
            </div>
          </div>
        </div>

        <div className="panel">
          <h3>Release blockers</h3>
          <div className="list-stack">
            <div className="list-card">
              <strong>Latest eval failed</strong>
              <div className="table-subtext">
                {metrics.release_blockers.latest_eval_failed}
              </div>
            </div>
            <div className="list-card">
              <strong>Pending approval</strong>
              <div className="table-subtext">
                {metrics.release_blockers.pending_approval}
              </div>
            </div>
            <div className="list-card">
              <strong>Not submitted</strong>
              <div className="table-subtext">
                {metrics.release_blockers.not_submitted}
              </div>
            </div>
            <div className="list-card">
              <strong>Awaiting eval results</strong>
              <div className="table-subtext">
                {metrics.release_blockers.awaiting_eval_results}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="panel">
        <h3>Incidents by linked release</h3>
        {metrics.incidents_by_release.length === 0 ? (
          <p>No linked incidents recorded yet.</p>
        ) : (
          <div className="list-stack">
            {metrics.incidents_by_release.map((entry) => (
              <div key={entry.release_candidate_id} className="list-card">
                <strong>{entry.release_candidate__name}</strong>
                <div className="table-subtext">Count: {entry.count}</div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="panel">
        <h3>Recent audit events</h3>
        {auditEvents.length === 0 ? (
          <p>No audit events available.</p>
        ) : (
          <div className="list-stack">
            {auditEvents.map((event) => (
              <div key={event.id} className="list-card">
                <strong>
                  {event.entity_type} #{event.entity_id}
                </strong>
                <div className="table-subtext">
                  <StatusBadge value={event.event_type} />
                </div>
                <div className="table-subtext">
                  Actor: {event.actor_type} {event.actor_id ? `| ${event.actor_id}` : ""}
                </div>
                <div className="table-subtext">
                  Correlation: {event.correlation_id || "n/a"}
                </div>
                <div className="table-subtext">
                  Created: {formatTimestamp(event.created_at)}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}