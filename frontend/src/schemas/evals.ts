import { z } from "zod";

export const evalDatasetSchema = z.object({
  id: z.number(),
  ai_system: z.number(),
  ai_system_name: z.string(),
  name: z.string(),
  slug: z.string(),
  description: z.string(),
  scenario_type: z.string(),
  threshold_profile: z.record(z.string(), z.unknown()),
  is_active: z.boolean(),
  case_count: z.number(),
  created_at: z.string(),
  updated_at: z.string(),
});

export const evalRunCaseResultSchema = z.object({
  id: z.number(),
  case_id: z.string(),
  scenario_type: z.string(),
  execution_status: z.string(),
  expected_label: z.string(),
  predicted_label: z.string(),
  response_payload: z.record(z.string(), z.unknown()),
  metric_log: z.record(z.string(), z.unknown()),
  failure_reason: z.string(),
  created_at: z.string(),
  updated_at: z.string(),
});

export const evalRunSchema = z.object({
  id: z.number(),
  release_candidate: z.number(),
  release_candidate_name: z.string(),
  eval_dataset: z.number(),
  eval_dataset_name: z.string(),
  eval_dataset_slug: z.string(),
  run_label: z.string(),
  status: z.string(),
  summary_metrics: z.record(z.string(), z.unknown()),
  threshold_results: z.record(z.string(), z.unknown()),
  comparison_to_baseline: z.record(z.string(), z.unknown()),
  correlation_id: z.string(),
  started_at: z.string().nullable(),
  completed_at: z.string().nullable(),
  created_at: z.string(),
  updated_at: z.string(),
  case_results: z.array(evalRunCaseResultSchema),
});

export const paginatedEvalDatasetListSchema = z.object({
  count: z.number(),
  next: z.string().nullable(),
  previous: z.string().nullable(),
  results: z.array(evalDatasetSchema),
});

export const paginatedEvalRunListSchema = z.object({
  count: z.number(),
  next: z.string().nullable(),
  previous: z.string().nullable(),
  results: z.array(evalRunSchema),
});

export type EvalDataset = z.infer<typeof evalDatasetSchema>;
export type EvalRun = z.infer<typeof evalRunSchema>;
export type EvalRunCaseResult = z.infer<typeof evalRunCaseResultSchema>;
