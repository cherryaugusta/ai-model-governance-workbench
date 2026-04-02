import { z } from "zod";

export const auditEventSchema = z.object({
  id: z.number(),
  entity_type: z.string(),
  entity_id: z.string(),
  event_type: z.string(),
  actor_type: z.string(),
  actor_id: z.string(),
  payload: z.record(z.string(), z.unknown()),
  correlation_id: z.string(),
  created_at: z.string(),
});

export const paginatedAuditEventListSchema = z.object({
  count: z.number(),
  next: z.string().nullable(),
  previous: z.string().nullable(),
  results: z.array(auditEventSchema),
});

export type AuditEvent = z.infer<typeof auditEventSchema>;