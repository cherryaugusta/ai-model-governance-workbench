import { z } from "zod";

export const incidentSeverityCountsSchema = z.object({
  low: z.number(),
  medium: z.number(),
  high: z.number(),
  critical: z.number(),
});

export const incidentByReleaseSchema = z.object({
  release_candidate_id: z.number(),
  release_candidate__name: z.string(),
  count: z.number(),
});

export const releaseBlockersSchema = z.object({
  latest_eval_failed: z.number(),
  pending_approval: z.number(),
  not_submitted: z.number(),
  awaiting_eval_results: z.number(),
});

export const metricsOverviewSchema = z.object({
  active_systems: z.number(),
  pending_approvals: z.number(),
  blocked_promotions: z.number(),
  failed_evals: z.number(),
  average_eval_latency_ms: z.number(),
  rollback_count: z.number(),
  open_incidents_by_severity: incidentSeverityCountsSchema,
  incidents_by_release: z.array(incidentByReleaseSchema),
  release_blockers: releaseBlockersSchema,
});

export type MetricsOverview = z.infer<typeof metricsOverviewSchema>;