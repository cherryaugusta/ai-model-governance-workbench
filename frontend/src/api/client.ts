import axios from "axios";
import { z } from "zod";
import {
  aiSystemSchema,
  paginatedAISystemListSchema,
  paginatedPromptVersionListSchema,
  paginatedModelConfigListSchema,
} from "../schemas/system";
import { releaseCandidateSchema } from "../schemas/releaseCandidate";
import {
  paginatedEvalDatasetListSchema,
  paginatedEvalRunListSchema,
} from "../schemas/evals";
import {
  approvalDecisionPayloadSchema,
  approvalRecordSchema,
  paginatedApprovalRecordListSchema,
} from "../schemas/approvals";

const API_BASE_URL =
  (import.meta.env.VITE_API_BASE_URL as string | undefined) ??
  "http://127.0.0.1:8000/api/";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

apiClient.interceptors.request.use((config) => {
  const token = window.localStorage.getItem("authToken");

  if (token) {
    config.headers.Authorization = `Token ${token}`;
  }

  return config;
});

function parseWithSchema<T>(schema: z.ZodSchema<T>, data: unknown): T {
  return schema.parse(data);
}

export async function fetchSystems() {
  const response = await apiClient.get("systems/");
  return parseWithSchema(paginatedAISystemListSchema, response.data);
}

export async function fetchSystemById(id: number) {
  const response = await apiClient.get(`systems/${id}/`);
  return parseWithSchema(aiSystemSchema, response.data);
}

export async function fetchAllPrompts() {
  const response = await apiClient.get("prompts/");
  const parsed = parseWithSchema(paginatedPromptVersionListSchema, response.data);
  return parsed.results;
}

export async function fetchAllModelConfigs() {
  const response = await apiClient.get("model-configs/");
  const parsed = parseWithSchema(paginatedModelConfigListSchema, response.data);
  return parsed.results;
}

export async function fetchReleaseCandidateById(id: number) {
  const response = await apiClient.get(`release-candidates/${id}/`);
  return parseWithSchema(releaseCandidateSchema, response.data);
}

export async function fetchEvalDatasets() {
  const response = await apiClient.get("eval-datasets/");
  const parsed = parseWithSchema(paginatedEvalDatasetListSchema, response.data);
  return parsed.results;
}

export async function fetchEvalRuns() {
  const response = await apiClient.get("eval-runs/");
  const parsed = parseWithSchema(paginatedEvalRunListSchema, response.data);
  return parsed.results;
}

export async function fetchApprovals(params?: {
  release_candidate?: number;
  approval_type?: string;
  decision?: string;
}) {
  const response = await apiClient.get("approvals/", { params });
  const parsed = parseWithSchema(paginatedApprovalRecordListSchema, response.data);
  return parsed.results;
}

export async function approveApproval(
  id: number,
  payload: { comment: string },
) {
  const parsedPayload = parseWithSchema(approvalDecisionPayloadSchema, payload);
  const response = await apiClient.post(`approvals/${id}/approve/`, parsedPayload);
  return parseWithSchema(approvalRecordSchema, response.data);
}

export async function rejectApproval(
  id: number,
  payload: { comment: string },
) {
  const parsedPayload = parseWithSchema(approvalDecisionPayloadSchema, payload);
  const response = await apiClient.post(`approvals/${id}/reject/`, parsedPayload);
  return parseWithSchema(approvalRecordSchema, response.data);
}

export async function requestApprovalChanges(
  id: number,
  payload: { comment: string },
) {
  const parsedPayload = parseWithSchema(approvalDecisionPayloadSchema, payload);
  const response = await apiClient.post(
    `approvals/${id}/request-changes/`,
    parsedPayload,
  );
  return parseWithSchema(approvalRecordSchema, response.data);
}