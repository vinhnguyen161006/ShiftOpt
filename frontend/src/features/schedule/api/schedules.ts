import type { UseMutationResult, UseQueryResult } from "@tanstack/react-query";
import type { JobAccepted, KpiRead, SolveRequest, SolveRunRead } from "../../../types/models";

export function useCreateSchedule(): UseMutationResult<JobAccepted, Error, SolveRequest> {
  throw new Error("TODO: useMutation POST /schedules, returns job_id");
}

export function useScheduleRun(runId: number): UseQueryResult<SolveRunRead> {
  throw new Error(
    "TODO: useQuery GET /schedules/{runId}, refetchInterval while status is queued or running",
  );
}

export function useScheduleKpi(runId: number): UseQueryResult<KpiRead> {
  throw new Error("TODO: useQuery GET /schedules/{runId}/kpi, enabled once the run succeeded");
}
