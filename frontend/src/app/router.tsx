import { createBrowserRouter } from "react-router-dom";
import { AppLayout } from "./AppLayout";
import { SystemsPage } from "../features/systems/SystemsPage";
import { SystemDetailPage } from "../features/systems/SystemDetailPage";
import { ReleasesPlaceholderPage } from "../features/releases/ReleasesPlaceholderPage";
import { EvalsPlaceholderPage } from "../features/evals/EvalsPlaceholderPage";
import { ApprovalsPlaceholderPage } from "../features/approvals/ApprovalsPlaceholderPage";
import { IncidentsPlaceholderPage } from "../features/incidents/IncidentsPlaceholderPage";
import { MetricsPlaceholderPage } from "../features/metrics/MetricsPlaceholderPage";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppLayout />,
    children: [
      { index: true, element: <SystemsPage /> },
      { path: "systems/:id", element: <SystemDetailPage /> },
      { path: "releases", element: <ReleasesPlaceholderPage /> },
      { path: "evals", element: <EvalsPlaceholderPage /> },
      { path: "approvals", element: <ApprovalsPlaceholderPage /> },
      { path: "incidents", element: <IncidentsPlaceholderPage /> },
      { path: "audit-events", element: <MetricsPlaceholderPage /> },
    ],
  },
]);
