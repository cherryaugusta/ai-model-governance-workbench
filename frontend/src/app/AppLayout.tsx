import { NavLink, Outlet } from "react-router-dom";

const navigationItems = [
  { to: "/", label: "Systems", end: true },
  { to: "/evals", label: "Evals" },
  { to: "/approvals", label: "Approvals" },
  { to: "/incidents", label: "Incidents" },
  { to: "/audit-events", label: "Audit" },
];

export function AppLayout() {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-block">
          <p className="eyebrow">AI Model Governance Workbench</p>
          <h1>Governed AI release control plane</h1>
          <p className="muted">
            Versioned artefacts, deterministic gates, approvals, incidents, and
            rollback.
          </p>
        </div>

        <nav className="nav-list" aria-label="Primary">
          {navigationItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                isActive ? "nav-link nav-link-active" : "nav-link"
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>

      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}
