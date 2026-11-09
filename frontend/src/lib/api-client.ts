import { API_BASE_URL } from "../config/env";
import { vi } from "../locales/vi";

export type FieldError = {
  path: (string | number)[];
  message: string;
};

export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly detail: string,
    readonly fieldErrors: FieldError[] = [],
  ) {
    super(detail);
  }
}

const UNREACHABLE = vi.common.unreachable;
const FIELD_ERRORS = vi.common.fieldErrors;

type ValidationItem = { loc?: (string | number)[]; msg?: string };

export function apiUrl(path: string): string {
  return `${API_BASE_URL}${path}`;
}

export function jsonInit(method: string, body?: unknown): RequestInit {
  return body === undefined ? { method } : { method, body: JSON.stringify(body) };
}

export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");
  if (init.body !== undefined && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  let response: Response;
  try {
    response = await fetch(apiUrl(path), { ...init, headers });
  } catch {
    throw new ApiError(0, UNREACHABLE);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  const body = await readBody(response);
  if (response.status === 401 && !path.startsWith("/auth/")) {
    redirectToLogin();
  }
  if (!response.ok) {
    throw toApiError(response.status, body);
  }
  return body as T;
}

function redirectToLogin() {
  if (window.location.pathname !== "/login") {
    window.location.assign("/login");
  }
}

async function readBody(response: Response): Promise<unknown> {
  const text = await response.text();
  if (!text) {
    return undefined;
  }
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

function toApiError(status: number, body: unknown): ApiError {
  const detail = typeof body === "object" && body !== null ? Reflect.get(body, "detail") : body;
  if (typeof detail === "string") {
    return new ApiError(status, detail);
  }
  if (Array.isArray(detail)) {
    const fieldErrors = detail.map((item: ValidationItem) => ({
      path: (item.loc ?? []).filter(
        (part, index) => !(index === 0 && (part === "body" || part === "query")),
      ),
      message: item.msg ?? vi.common.invalidValue,
    }));
    return new ApiError(status, FIELD_ERRORS, fieldErrors);
  }
  return new ApiError(status, vi.common.requestFailed(status));
}

export function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : vi.common.somethingWrong;
}

export function fieldErrorsOf(error: unknown): FieldError[] {
  return error instanceof ApiError ? error.fieldErrors : [];
}
