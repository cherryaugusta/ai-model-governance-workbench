import { z } from "zod";

export const approvalSummarySchema = z
  .object({
    is_complete: z.boolean().optional(),
    missing_types: z.array(z.string()).optional(),
  })
  .passthrough();

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
  can_run_evals: z.boolean(),
  can_request_approval: z.boolean(),
  can_promote: z.boolean(),
  can_rollback: z.boolean(),
  required_approval_types: z.array(z.string()),
  approval_summary: approvalSummarySchema,
  blocking_reasons: z.array(z.string()),
});

export const promoteReleaseCandidatePayloadSchema = z.object({
  reason: z.string(),
});

export const rollbackReleaseCandidatePayloadSchema = z.object({
  reason_code: z.string().min(1),
  comment: z.string(),
});

export const rollbackReleaseCandidateResponseSchema = z.object({
  from_candidate: releaseCandidateSchema,
  to_candidate: releaseCandidateSchema,
  rollback_record_id: z.number(),
});

export type ReleaseCandidate = z.infer<typeof releaseCandidateSchema>;
export type PromoteReleaseCandidatePayload = z.infer<
  typeof promoteReleaseCandidatePayloadSchema
>;
export type RollbackReleaseCandidatePayload = z.infer<
  typeof rollbackReleaseCandidatePayloadSchema
>;
export type RollbackReleaseCandidateResponse = z.infer<
  typeof rollbackReleaseCandidateResponseSchema
>;
