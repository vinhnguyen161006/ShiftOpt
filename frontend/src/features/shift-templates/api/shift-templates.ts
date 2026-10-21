import type { UseMutationResult, UseQueryResult } from "@tanstack/react-query";
import type { ShiftTemplateCreate, ShiftTemplateRead } from "../../../types/models";

export function useShiftTemplates(): UseQueryResult<ShiftTemplateRead[]> {
  throw new Error("TODO: useQuery GET /shift-templates");
}

export function useCreateShiftTemplate(): UseMutationResult<
  ShiftTemplateRead,
  Error,
  ShiftTemplateCreate
> {
  throw new Error("TODO: useMutation POST /shift-templates, invalidate the list");
}

export function useDeleteShiftTemplate(): UseMutationResult<void, Error, number> {
  throw new Error("TODO: useMutation DELETE /shift-templates/{templateId}");
}
