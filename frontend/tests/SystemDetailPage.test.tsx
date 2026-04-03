import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { vi } from "vitest";
import { SystemDetailPage } from "../src/features/systems/SystemDetailPage";

vi.mock("../src/api/client", () => ({
  fetchSystemById: vi.fn().mockResolvedValue({
    id: 21,
    name: "Consumer Support Triage Assistant",
    slug: "consumer-support-triage-assistant",
    description: "Test system description",
    owner_team: "Consumer Operations AI",
    technical_owner: 25,
    technical_owner_username: "tech_reviewer",
    business_owner: 26,
    business_owner_username: "product_reviewer",
    risk_tier: "high",
    system_type: "classification",
    domain_area: "customer-support",
    status: "active",
    active_release_id: 31,
    created_at: "2026-04-03T10:31:27Z",
    updated_at: "2026-04-03T10:31:27Z",
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
      template_text: "Prompt text",
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
  fetchAllModelConfigs: vi.fn().mockResolvedValue([
    {
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
      <MemoryRouter initialEntries={["/systems/21"]}>
        <Routes>
          <Route path="/systems/:id" element={<SystemDetailPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("SystemDetailPage", () => {
  it("renders system metadata correctly", async () => {
    renderWithProviders();

    expect(
      await screen.findByText("Consumer Support Triage Assistant"),
    ).toBeInTheDocument();

    expect(
      screen.getByText("consumer-support-triage-assistant"),
    ).toBeInTheDocument();

    expect(
      screen.getByText("Consumer Operations AI"),
    ).toBeInTheDocument();

    expect(screen.getAllByText("high").length).toBeGreaterThan(0);
    expect(screen.getByText("classification")).toBeInTheDocument();
    expect(screen.getByText("customer-support")).toBeInTheDocument();
    expect(screen.getByText("tech_reviewer")).toBeInTheDocument();
    expect(screen.getByText("product_reviewer")).toBeInTheDocument();
    expect(screen.getByText("Strict Triage Prompt")).toBeInTheDocument();

    expect(
      screen.getByText((_, element) => {
        return element?.textContent === "gpt-4.1 | gpt-4.1-v1";
      }),
    ).toBeInTheDocument();
  });
});