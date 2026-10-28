import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch, jsonInit } from "../../../lib/api-client";
import type { ShiftTemplateCreate, ShiftTemplateRead } from "../../../types/models";

const TEMPLATES_KEY = ["shift-templates"];

export function useShiftTemplates() {
  return useQuery({
    queryKey: TEMPLATES_KEY,
    queryFn: () => apiFetch<ShiftTemplateRead[]>("/shift-templates"),
  });
}

function useTemplateMutation<V, R>(request: (variables: V) => Promise<R>) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: request,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: TEMPLATES_KEY }),
  });
}

export function useSaveShiftTemplate() {
  return useTemplateMutation(({ id, body }: { id?: number; body: ShiftTemplateCreate }) =>
    id === undefined
      ? apiFetch<ShiftTemplateRead>("/shift-templates", jsonInit("POST", body))
      : apiFetch<ShiftTemplateRead>(`/shift-templates/${id}`, jsonInit("PUT", body)),
  );
}

export function useDeleteShiftTemplate() {
  return useTemplateMutation((id: number) =>
    apiFetch<void>(`/shift-templates/${id}`, jsonInit("DELETE")),
  );
}
