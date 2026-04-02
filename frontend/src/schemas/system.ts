import { z } from "zod";

export const aiSystemSchema = z.object({
  id: z.number(),
  name: z.string(),
  slug: z.string(),
  description: z.string(),
  owner_team: z.string(),
  technical_owner: z.number().nullable(),
  technical_owner_username: z.string().nullable().optional(),
  business_owner: z.number().nullable(),
  business_owner_username: z.string().nullable().optional(),
  risk_tier: z.enum(["low", "medium", "high", "critical"]),
  system_type: z.string(),
  domain_area: z.string(),
  status: z.string(),
  active_release_id: z.number().nullable(),
  created_at: z.string(),
  updated_at: z.string(),
});

export const promptVersionSchema = z.object({
  id: z.number(),
  ai_system: z.number(),
  ai_system_name: z.string(),
  name: z.string(),
  purpose: z.string(),
  version_label: z.string(),
  status: z.string(),
  template_text: z.string(),
  schema_version: z.string(),
  input_contract: z.record(z.string(), z.unknown()),
  output_contract: z.record(z.string(), z.unknown()),
  created_by: z.number().nullable().optional(),
  created_by_username: z.string().nullable().optional(),
  created_at: z.string(),
});

export const modelConfigSchema = z.object({
  id: z.number(),
  ai_system: z.number(),
  ai_system_name: z.string(),
  version_label: z.string(),
  provider_name: z.string(),
  model_name: z.string(),
  temperature: z.union([z.number(), z.string()]),
  max_tokens: z.number(),
  top_p: z.union([z.number(), z.string()]),
  timeout_ms: z.number(),
  routing_policy: z.record(z.string(), z.unknown()),
  fallback_policy: z.record(z.string(), z.unknown()),
  cost_budget_per_run: z.union([z.number(), z.string()]),
  status: z.string(),
  created_by: z.number().nullable().optional(),
  created_by_username: z.string().nullable().optional(),
  created_at: z.string(),
});

export const paginatedAISystemListSchema = z.object({
  count: z.number(),
  next: z.string().nullable(),
  previous: z.string().nullable(),
  results: z.array(aiSystemSchema),
});

export const paginatedPromptVersionListSchema = z.object({
  count: z.number(),
  next: z.string().nullable(),
  previous: z.string().nullable(),
  results: z.array(promptVersionSchema),
});

export const paginatedModelConfigListSchema = z.object({
  count: z.number(),
  next: z.string().nullable(),
  previous: z.string().nullable(),
  results: z.array(modelConfigSchema),
});

export type AISystem = z.infer<typeof aiSystemSchema>;
export type PromptVersion = z.infer<typeof promptVersionSchema>;
export type ModelConfig = z.infer<typeof modelConfigSchema>;
export type PaginatedAISystemList = z.infer<typeof paginatedAISystemListSchema>;
export type PaginatedPromptVersionList = z.infer<typeof paginatedPromptVersionListSchema>;
export type PaginatedModelConfigList = z.infer<typeof paginatedModelConfigListSchema>;
