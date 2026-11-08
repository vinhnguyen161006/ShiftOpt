import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch, jsonInit } from "../../../lib/api-client";
import type { JobAccepted, RerosterRequest, ScheduleChangesRead } from "../../../types/models";

export function useCreateReroster(runId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: RerosterRequest) =>
      apiFetch<JobAccepted>(`/schedules/${runId}/reroster`, jsonInit("POST", body)),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["schedules"] }),
  });
}

export function useScheduleChanges(runId: number, enabled: boolean) {
  return useQuery({
    queryKey: ["schedules", runId, "changes"],
    queryFn: () => apiFetch<ScheduleChangesRead>(`/schedules/${runId}/changes`),
    enabled,
  });
}
