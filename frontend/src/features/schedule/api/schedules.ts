import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch, apiUrl, jsonInit } from "../../../lib/api-client";
import type {
  JobAccepted,
  KpiRead,
  RunStatus,
  SolveRequest,
  SolveRunRead,
} from "../../../types/models";

const RUNS_KEY = ["schedules"];
const POLL_MS = 1000;

export function isActive(status: RunStatus | undefined): boolean {
  return status === "queued" || status === "running";
}

export function useScheduleRuns() {
  return useQuery({
    queryKey: RUNS_KEY,
    queryFn: () => apiFetch<SolveRunRead[]>("/schedules"),
    refetchInterval: (query) =>
      query.state.data?.some((run) => isActive(run.status)) ? POLL_MS : false,
  });
}

export function useCreateSchedule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: SolveRequest) => apiFetch<JobAccepted>("/schedules", jsonInit("POST", body)),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: RUNS_KEY }),
  });
}

export function useScheduleRun(runId: number | undefined) {
  return useQuery({
    queryKey: [...RUNS_KEY, runId],
    queryFn: () => apiFetch<SolveRunRead>(`/schedules/${runId}`),
    enabled: runId !== undefined,
    refetchInterval: (query) => (isActive(query.state.data?.status) ? POLL_MS : false),
  });
}

export function useScheduleKpi(runId: number | undefined, enabled: boolean) {
  return useQuery({
    queryKey: [...RUNS_KEY, runId, "kpi"],
    queryFn: () => apiFetch<KpiRead>(`/schedules/${runId}/kpi`),
    enabled: enabled && runId !== undefined,
  });
}

export function exportUrl(runId: number, kind: "assignments" | "coverage" | "kpi"): string {
  return apiUrl(`/schedules/${runId}/${kind}.csv`);
}
