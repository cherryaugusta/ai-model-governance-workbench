import axios from "axios";
import { z } from "zod";
import {
  aiSystemSchema,
  paginatedAISystemListSchema,
  paginatedPromptVersionListSchema,
  paginatedModelConfigListSchema,
} from "../schemas/system";

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
