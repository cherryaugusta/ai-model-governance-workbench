import { z } from "zod";

export const releaseCandidateSchema = z.object({
  id: z.number(),
  ai_system: z.number(),
  ai_system_name: z.string(),
  prompt_version: z.number(),
  prompt_version_label: z.string(),
  model_config: z.number(),
  model_config_version_label: z.string(),
  name: z.string(),
  status: z.string(),
  eval_dataset_ids: z.array(z.unknown()),
  config_snapshot: z.record(z.string(), z.unknown()),
  created_by: z.number().nullable().optional(),
  created_by_username: z.string().nullable().optional(),
  created_at: z.string(),
  updated_at: z.string(),
  can_submit: z.boolean(),
  blocking_reasons: z.array(z.string()),
});

export type ReleaseCandidate = z.infer<typeof releaseCandidateSchema>;
