import { z } from "zod";

export const approvalDecisionSchema = z.enum([
  "pending",
  "approved",
  "rejected",
  "changes_requested",
]);

export const approvalTypeSchema = z.enum([
  "technical",
  "product",
  "risk",
  "governance",
]);

export const approvalRecordSchema = z.object({
  id: z.number(),
  release_candidate: z.number(),
  release_candidate_name: z.string(),
  approval_type: approvalTypeSchema,
  reviewer: z.number().nullable(),
  reviewer_username: z.string().nullable().optional(),
  decision: approvalDecisionSchema,
  comment: z.string(),
  decided_at: z.string().nullable(),
  created_at: z.string(),
  updated_at: z.string(),
});

export const paginatedApprovalRecordListSchema = z.object({
  count: z.number(),
  next: z.string().nullable(),
  previous: z.string().nullable(),
  results: z.array(approvalRecordSchema),
});

export const approvalDecisionPayloadSchema = z.object({
  comment: z.string(),
});

export type ApprovalRecord = z.infer<typeof approvalRecordSchema>;
export type ApprovalDecision = z.infer<typeof approvalDecisionSchema>;
export type ApprovalType = z.infer<typeof approvalTypeSchema>;
export type ApprovalDecisionPayload = z.infer<
  typeof approvalDecisionPayloadSchema
>;