import { createBrowserRouter } from "react-router-dom";
import { AppLayout } from "./AppLayout";
import { SystemsPage } from "../features/systems/SystemsPage";
import { SystemDetailPage } from "../features/systems/SystemDetailPage";
import { ReleaseCandidatePage } from "../features/releases/ReleaseCandidatePage";
import { ReleasesPlaceholderPage } from "../features/releases/ReleasesPlaceholderPage";
import { EvalDashboardPage } from "../features/evals/EvalDashboardPage";
import { ApprovalQueuePage } from "../features/approvals/ApprovalQueuePage";
import { IncidentsPlaceholderPage } from "../features/incidents/IncidentsPlaceholderPage";
import { MetricsPlaceholderPage } from "../features/metrics/MetricsPlaceholderPage";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppLayout />,
    children: [
      { index: true, element: <SystemsPage /> },
      { path: "systems/:id", element: <SystemDetailPage /> },
      { path: "release-candidates/:id", element: <ReleaseCandidatePage /> },
      { path: "releases", element: <ReleasesPlaceholderPage /> },
      { path: "evals", element: <EvalDashboardPage /> },
      { path: "approvals", element: <ApprovalQueuePage /> },
      { path: "incidents", element: <IncidentsPlaceholderPage /> },
      { path: "audit-events", element: <MetricsPlaceholderPage /> },
    ],
  },
]);