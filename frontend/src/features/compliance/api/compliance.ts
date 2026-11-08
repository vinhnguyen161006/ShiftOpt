import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch, jsonInit } from "../../../lib/api-client";
import type {
  ComplianceRead,
  ManualEditRequest,
  ReplacementRead,
  SolveRunRead,
} from "../../../types/models";

export function useReplacements(runId: number, employeeCode: string, day: number | null) {
  return useQuery({
    queryKey: ["schedules", runId, "replacements", employeeCode, day],
    queryFn: () => {
      const query = new URLSearchParams({
        employee_code: employeeCode,
        day: String(day),
        limit: "5",
      });
      return apiFetch<ReplacementRead[]>(`/schedules/${runId}/replacements?${query}`);
    },
    enabled: employeeCode !== "" && day !== null,
  });
}

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
