import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { vi } from "vitest";
import { PromptVersionDetailPage } from "../src/features/prompts/PromptVersionDetailPage";

vi.mock("../src/api/client", () => ({
  fetchPromptById: vi.fn().mockResolvedValue({
    id: 37,
    ai_system: 21,
    ai_system_name: "Consumer Support Triage Assistant",
    name: "Strict Triage Prompt",
    purpose: "Stable governed complaint triage baseline.",
    version_label: "triage-strict-v1",
    status: "approved",
    template_text:
      "Strictly classify the complaint, preserve schema validity, and indicate whether human review is required.",
    schema_version: "1.0",
    input_contract: {
      type: "object",
      required: ["text"],
    },
    output_contract: {
      type: "object",
      required: ["label", "requires_review"],
    },
    created_by: 23,
    created_by_username: "admin",
    created_at: "2026-04-03T10:31:27Z",
  }),
  fetchAllPrompts: vi.fn().mockResolvedValue([
    {
      id: 37,
      ai_system: 21,
      ai_system_name: "Consumer Support Triage Assistant",
      name: "Strict Triage Prompt",
      purpose: "Stable governed complaint triage baseline.",
      version_label: "triage-strict-v1",
      status: "approved",
      template_text:
        "Strictly classify the complaint, preserve schema validity, and indicate whether human review is required.",
      schema_version: "1.0",
      input_contract: {
        type: "object",
        required: ["text"],
      },
      output_contract: {
        type: "object",
        required: ["label", "requires_review"],
      },
      created_by: 23,
      created_by_username: "admin",
      created_at: "2026-04-03T10:31:27Z",
    },
  ]),
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
      <MemoryRouter initialEntries={["/prompts/37"]}>
        <Routes>
          <Route path="/prompts/:id" element={<PromptVersionDetailPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("PromptVersionDetailPage", () => {
  it("renders prompt metadata and linked release candidate", async () => {
    renderWithProviders();

    expect(await screen.findByText("Strict Triage Prompt")).toBeInTheDocument();
    expect(screen.getByText("triage-strict-v1")).toBeInTheDocument();
    expect(
      screen.getByText("Stable governed complaint triage baseline."),
    ).toBeInTheDocument();

    expect(
      screen.getByText("Current approved triage baseline"),
    ).toBeInTheDocument();

    expect(screen.getByText("Candidate ID: 31")).toBeInTheDocument();
    expect(screen.getByText("Model config: gpt-4.1-v1")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Strictly classify the complaint, preserve schema validity, and indicate whether human review is required.",
      ),
    ).toBeInTheDocument();
  });
});