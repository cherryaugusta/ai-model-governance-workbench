import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchIncidents } from "../../api/client";
import { ErrorState } from "../../components/ErrorState";
import { LoadingSpinner } from "../../components/LoadingSpinner";
import { StatusBadge } from "../../components/StatusBadge";

function formatTimestamp(value: string) {
  return new Date(value).toLocaleString();
}

export function IncidentDashboardPage() {
  const [severityFilter, setSeverityFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");

  const incidentsQuery = useQuery({
    queryKey: ["incidents", severityFilter, statusFilter],
    queryFn: () =>
      fetchIncidents({
        severity: severityFilter === "all" ? undefined : severityFilter,
        status: statusFilter === "all" ? undefined : statusFilter,
      }),
  });

  const incidents = incidentsQuery.data ?? [];

  const summary = useMemo(() => {
    return incidents.reduce(
      (accumulator, incident) => {
        accumulator.total += 1;

        if (incident.status === "open") {
          accumulator.open += 1;
        }

        if (incident.severity === "high" || incident.severity === "critical") {
          accumulator.highOrCritical += 1;
        }

        return accumulator;
      },
      {
        total: 0,
        open: 0,
        highOrCritical: 0,
      },
    );
  }, [incidents]);

  if (incidentsQuery.isLoading) {
    return <LoadingSpinner label="Loading incidents" />;
  }

  if (incidentsQuery.isError) {
    return (
      <ErrorState message="The incidents dashboard could not be loaded from the backend API." />
    );
  }

  return (
    <section className="page-section">
      <div className="page-header">
        <p className="eyebrow">Incidents</p>
        <h2>Incident dashboard</h2>
        <p>
          Operational incidents can block governed promotion decisions and later
          drive rollback workflows.
        </p>
      </div>

      <div className="stats-grid">
        <div className="panel">
          <p className="eyebrow">Total incidents</p>
          <h3>{summary.total}</h3>
        </div>
        <div className="panel">
          <p className="eyebrow">Open incidents</p>
          <h3>{summary.open}</h3>
        </div>
        <div className="panel">
          <p className="eyebrow">High or critical</p>
          <h3>{summary.highOrCritical}</h3>
        </div>
      </div>

      <div className="panel">
        <div className="field-grid">
          <label className="field">
            <span>Severity</span>
            <select
              value={severityFilter}
              onChange={(event) => setSeverityFilter(event.target.value)}
            >
              <option value="all">All severities</option>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="critical">Critical</option>
            </select>
          </label>

          <label className="field">
            <span>Status</span>
            <select
              value={statusFilter}
              onChange={(event) => setStatusFilter(event.target.value)}
            >
              <option value="all">All statuses</option>
              <option value="open">Open</option>
              <option value="investigating">Investigating</option>
              <option value="mitigated">Mitigated</option>
              <option value="resolved">Resolved</option>
              <option value="closed">Closed</option>
            </select>
          </label>
        </div>
      </div>

      {incidents.length === 0 ? (
        <div className="panel">
          <p>No incidents match the current filters.</p>
        </div>
      ) : (
        <div className="stack-lg">
          {incidents.map((incident) => (
            <article key={incident.id} className="panel">
              <div className="page-header" style={{ marginBottom: "1rem" }}>
                <div>
                  <p className="eyebrow">Incident</p>
                  <h3>{incident.summary}</h3>
                </div>
              </div>

              <div className="detail-grid">
                <div>
                  <strong>System</strong>
                  <p>{incident.ai_system_name}</p>
                </div>
                <div>
                  <strong>Linked release</strong>
                  <p>{incident.release_candidate_name ?? "Not linked"}</p>
                </div>
                <div>
                  <strong>Type</strong>
                  <p>
                    <StatusBadge value={incident.incident_type} />
                  </p>
                </div>
                <div>
                  <strong>Severity</strong>
                  <p>
                    <StatusBadge value={incident.severity} />
                  </p>
                </div>
                <div>
                  <strong>Status</strong>
                  <p>
                    <StatusBadge value={incident.status} />
                  </p>
                </div>
                <div>
                  <strong>Reported by</strong>
                  <p>{incident.reported_by_username}</p>
                </div>
                <div>
                  <strong>Created</strong>
                  <p>{formatTimestamp(incident.created_at)}</p>
                </div>
                <div>
                  <strong>Updated</strong>
                  <p>{formatTimestamp(incident.updated_at)}</p>
                </div>
              </div>

              <div style={{ marginTop: "1rem" }}>
                <strong>Description</strong>
                <p>{incident.description}</p>
              </div>

              <div style={{ marginTop: "1rem" }}>
                <strong>Resolution notes</strong>
                <p>{incident.resolution_notes || "No resolution notes recorded."}</p>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}