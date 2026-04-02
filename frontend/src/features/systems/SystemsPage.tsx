import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { fetchSystems } from "../../api/client";
import { DataTable, type DataTableColumn } from "../../components/DataTable";
import { ErrorState } from "../../components/ErrorState";
import { LoadingSpinner } from "../../components/LoadingSpinner";
import { StatusBadge } from "../../components/StatusBadge";
import type { AISystem } from "../../schemas/system";

export function SystemsPage() {
  const [ownerTeamFilter, setOwnerTeamFilter] = useState("");
  const [riskTierFilter, setRiskTierFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  const systemsQuery = useQuery({
    queryKey: ["systems"],
    queryFn: fetchSystems,
  });

  const systems = systemsQuery.data?.results ?? [];

  const ownerTeams = useMemo(() => {
    return [...new Set(systems.map((system) => system.owner_team))].sort();
  }, [systems]);

  const filteredSystems = useMemo(() => {
    return systems.filter((system) => {
      const matchesOwnerTeam =
        ownerTeamFilter === "" || system.owner_team === ownerTeamFilter;
      const matchesRiskTier =
        riskTierFilter === "" || system.risk_tier === riskTierFilter;
      const matchesStatus =
        statusFilter === "" || system.status === statusFilter;

      return matchesOwnerTeam && matchesRiskTier && matchesStatus;
    });
  }, [systems, ownerTeamFilter, riskTierFilter, statusFilter]);

  const columns: DataTableColumn<AISystem>[] = [
    {
      key: "name",
      header: "System",
      render: (system) => (
        <div>
          <Link className="table-link" to={`/systems/${system.id}`}>
            {system.name}
          </Link>
          <div className="table-subtext">{system.slug}</div>
        </div>
      ),
    },
    {
      key: "owner_team",
      header: "Owner team",
      render: (system) => system.owner_team,
    },
    {
      key: "risk_tier",
      header: "Risk tier",
      render: (system) => <StatusBadge value={system.risk_tier} />,
    },
    {
      key: "status",
      header: "Status",
      render: (system) => <StatusBadge value={system.status} />,
    },
    {
      key: "active_release",
      header: "Active release",
      render: (system) =>
        system.active_release_id ? (
          <StatusBadge value={`release ${system.active_release_id}`} />
        ) : (
          <span className="muted">None</span>
        ),
    },
    {
      key: "owners",
      header: "Owners",
      render: (system) => (
        <div>
          <div className="table-subtext">
            Technical: {system.technical_owner_username ?? "Unassigned"}
          </div>
          <div className="table-subtext">
            Business: {system.business_owner_username ?? "Unassigned"}
          </div>
        </div>
      ),
    },
  ];

  if (systemsQuery.isLoading) {
    return <LoadingSpinner label="Loading systems registry..." />;
  }

  if (systemsQuery.isError) {
    return (
      <ErrorState message="The systems registry could not be loaded from the backend API." />
    );
  }

  return (
    <section className="page-section">
      <div className="page-header">
        <div>
          <p className="eyebrow">Systems Registry</p>
          <h2>Governed AI systems inventory</h2>
          <p className="muted">
            Real backend data from the Django systems API.
          </p>
        </div>
        <div className="stat-card compact">
          <span className="stat-label">Systems</span>
          <strong className="stat-value">{systemsQuery.data?.count ?? 0}</strong>
        </div>
      </div>

      <div className="panel">
        <div className="filters-grid">
          <label className="field">
            <span>Owner team</span>
            <select
              value={ownerTeamFilter}
              onChange={(event) => setOwnerTeamFilter(event.target.value)}
            >
              <option value="">All</option>
              {ownerTeams.map((team) => (
                <option key={team} value={team}>
                  {team}
                </option>
              ))}
            </select>
          </label>

          <label className="field">
            <span>Risk tier</span>
            <select
              value={riskTierFilter}
              onChange={(event) => setRiskTierFilter(event.target.value)}
            >
              <option value="">All</option>
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
              <option value="">All</option>
              <option value="draft">Draft</option>
              <option value="active">Active</option>
              <option value="paused">Paused</option>
              <option value="retired">Retired</option>
            </select>
          </label>
        </div>
      </div>

      <DataTable
        columns={columns}
        rows={filteredSystems}
        emptyMessage="No systems matched the current filters."
      />
    </section>
  );
}
