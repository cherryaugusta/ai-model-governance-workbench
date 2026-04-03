import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { vi } from "vitest";
import { ModelConfigDetailPage } from "../src/features/model-configs/ModelConfigDetailPage";

vi.mock("../src/api/client", () => ({
  fetchModelConfigById: vi.fn().mockResolvedValue({
    id: 37,
    ai_system: 21,
    ai_system_name: "Consumer Support Triage Assistant",
    version_label: "gpt-4.1-v1",
    provider_name: "openai",
    model_name: "gpt-4.1",
    temperature: "0.10",
    max_tokens: 640,
    top_p: "1.00",
    timeout_ms: 2900,
    routing_policy: {
      mode: "primary_only",
    },
    fallback_policy: {
      enabled: false,
    },
    cost_budget_per_run: "0.0300",
    status: "approved",
    created_by: 23,
    created_by_username: "admin",
    created_at: "2026-04-03T10:31:27Z",
  }),
  fetchAllReleaseCandidates: vi.fn().mockResolvedValue([
    {
      id: 31,
      ai_system: 21,
      ai_system_name: "Consumer Support Triage Assistant",
      prompt_version: 37,
      prompt_version_label: "triage-strict-v1",
      model_config: 37,
      model_config_version_label: "gpt-4.1-v1",
      name: "Current approved triage baseline",
      status: "active",
      eval_dataset_ids: [],
      config_snapshot: {},
      created_by_username: "admin",
      created_at: "2026-04-03T10:31:27Z",
      updated_at: "2026-04-03T10:31:27Z",
      can_submit: false,
      can_run_evals: false,
      can_request_approval: false,
      can_promote: false,
      can_rollback: true,
      blocking_reasons: [],
      required_approval_types: ["technical", "product", "risk"],
      approval_summary: {
        is_complete: true,
        missing_types: [],
      },
    },
  ]),
}));

function renderWithProviders() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/model-configs/37"]}>
        <Routes>
          <Route path="/model-configs/:id" element={<ModelConfigDetailPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("ModelConfigDetailPage", () => {
  it("renders model config metadata and linked release candidate", async () => {
    renderWithProviders();

    expect(await screen.findByText("openai gpt-4.1")).toBeInTheDocument();
    expect(screen.getByText("gpt-4.1-v1")).toBeInTheDocument();
    expect(screen.getByText("2900")).toBeInTheDocument();
    expect(screen.getByText("0.0300")).toBeInTheDocument();

    expect(
      screen.getByText("Current approved triage baseline"),
    ).toBeInTheDocument();

    expect(screen.getByText("Candidate ID: 31")).toBeInTheDocument();
    expect(screen.getByText("Prompt version: triage-strict-v1")).toBeInTheDocument();

    expect(
      screen.getByText((_, element) => {
        return element?.textContent === '{\n  "mode": "primary_only"\n}';
      }),
    ).toBeInTheDocument();
  });
});