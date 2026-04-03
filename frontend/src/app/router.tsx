import { createBrowserRouter } from "react-router-dom";
import { AppLayout } from "./AppLayout";
import { SystemsPage } from "../features/systems/SystemsPage";
import { SystemDetailPage } from "../features/systems/SystemDetailPage";
import { PromptVersionDetailPage } from "../features/prompts/PromptVersionDetailPage";
import { ModelConfigDetailPage } from "../features/model-configs/ModelConfigDetailPage";
import { ReleaseCandidatePage } from "../features/releases/ReleaseCandidatePage";
import { ReleasesPlaceholderPage } from "../features/releases/ReleasesPlaceholderPage";
import { EvalDashboardPage } from "../features/evals/EvalDashboardPage";
import { ApprovalQueuePage } from "../features/approvals/ApprovalQueuePage";
import { IncidentDashboardPage } from "../features/incidents/IncidentDashboardPage";
import { AuditTimelinePage } from "../features/metrics/AuditTimelinePage";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppLayout />,
    children: [
      { index: true, element: <SystemsPage /> },
      { path: "systems/:id", element: <SystemDetailPage /> },
      { path: "prompts/:id", element: <PromptVersionDetailPage /> },
      { path: "model-configs/:id", element: <ModelConfigDetailPage /> },
      { path: "release-candidates/:id", element: <ReleaseCandidatePage /> },
      { path: "releases", element: <ReleasesPlaceholderPage /> },
      { path: "evals", element: <EvalDashboardPage /> },
      { path: "approvals", element: <ApprovalQueuePage /> },
      { path: "incidents", element: <IncidentDashboardPage /> },
      { path: "audit-events", element: <AuditTimelinePage /> },
    ],
  },
]);