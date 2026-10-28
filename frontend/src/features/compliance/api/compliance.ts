import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch, jsonInit } from "../../../lib/api-client";
import type { ComplianceRead, ManualEditRequest, SolveRunRead } from "../../../types/models";

export function useCompliance(runId: number, enabled: boolean) {
  return useQuery({
    queryKey: ["schedules", runId, "compliance"],
    queryFn: () => apiFetch<ComplianceRead>(`/schedules/${runId}/compliance`),
    enabled,
  });
}

export function useCreateManualEdit(runId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: ManualEditRequest) =>
      apiFetch<SolveRunRead>(`/schedules/${runId}/edits`, jsonInit("POST", body)),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["schedules"] }),
  });
}
