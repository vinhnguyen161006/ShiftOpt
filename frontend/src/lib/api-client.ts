import { API_BASE_URL } from "../config/env";

export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly detail: string,
  ) {
    super(detail);
  }
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  throw new Error(
    `TODO: fetch ${API_BASE_URL}${path} with JSON headers, parse the body, throw ApiError with the FastAPI "detail" on non-2xx`,
  );
}
