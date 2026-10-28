import type { SummaryError } from "../components/ui/Feedback";
import { ApiError, fieldErrorsOf } from "./api-client";

export function errorsByPath(error: unknown): Map<string, string> {
  return new Map(fieldErrorsOf(error).map((item) => [item.path.join("."), item.message]));
}

export function summaryErrors(
  error: unknown,
  fieldId: (path: string) => string | undefined,
): SummaryError[] {
  const errors: SummaryError[] = [];
  for (const [path, message] of errorsByPath(error)) {
    const id = fieldId(path);
    if (id) {
      errors.push({ fieldId: id, message: `${path.replaceAll(".", " ")}: ${message}` });
    }
  }
  return errors;
}

export function generalError(error: unknown): string | undefined {
  if (!error) {
    return undefined;
  }
  if (error instanceof ApiError && error.fieldErrors.length > 0) {
    return undefined;
  }
  return error instanceof Error ? error.message : "Something went wrong.";
}

export function toNumber(value: string): number {
  return value.trim() === "" ? Number.NaN : Number(value);
}
