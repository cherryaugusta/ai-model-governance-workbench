import { z } from "zod";

export const incidentSchema = z.object({
  id: z.number(),
  ai_system: z.number(),
  ai_system_name: z.string(),
  release_candidate: z.number().nullable(),
  release_candidate_name: z.string().nullable(),
  incident_type: z.string(),
  severity: z.string(),
  status: z.string(),
  summary: z.string(),
  description: z.string(),
  reported_by: z.number(),
  reported_by_username: z.string(),
  resolution_notes: z.string(),
  created_at: z.string(),
  updated_at: z.string(),
});

export const paginatedIncidentListSchema = z.object({
  count: z.number(),
  next: z.string().nullable(),
  previous: z.string().nullable(),
  results: z.array(incidentSchema),
});

export type Incident = z.infer<typeof incidentSchema>;