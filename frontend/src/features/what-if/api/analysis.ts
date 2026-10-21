import type { UseMutationResult, UseQueryResult } from "@tanstack/react-query";
import type {
  AnalysisAccepted,
  AnalysisRunRead,
  DemandSweepRequest,
  SolveRequest,
} from "../../../types/models";

export function useDemandSweep(): UseMutationResult<AnalysisAccepted, Error, DemandSweepRequest> {
  throw new Error("TODO: useMutation POST /analysis/demand-sweep");
}

export function useMarginalCost(): UseMutationResult<
  AnalysisAccepted,
  Error,
  { solve: SolveRequest }
> {
  throw new Error("TODO: useMutation POST /analysis/marginal-cost");
}

export function useAnalysisRun(runId: number): UseQueryResult<AnalysisRunRead> {
  throw new Error("TODO: useQuery GET /analysis/{runId}, poll while queued or running");
}
