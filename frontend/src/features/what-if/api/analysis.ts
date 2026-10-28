import { useMutation, useQuery } from "@tanstack/react-query";
import { apiFetch, jsonInit } from "../../../lib/api-client";
import type {
  AnalysisAccepted,
  AnalysisRunRead,
  DemandSweepRequest,
  MarginalCostRequest,
} from "../../../types/models";

const POLL_MS = 1500;

export function useDemandSweep() {
  return useMutation({
    mutationFn: (body: DemandSweepRequest) =>
      apiFetch<AnalysisAccepted>("/analysis/demand-sweep", jsonInit("POST", body)),
  });
}

export function useMarginalCost() {
  return useMutation({
    mutationFn: (body: MarginalCostRequest) =>
      apiFetch<AnalysisAccepted>("/analysis/marginal-cost", jsonInit("POST", body)),
  });
}

export function useAnalysisRun(runId: number | undefined) {
  return useQuery({
    queryKey: ["analysis", runId],
    queryFn: () => apiFetch<AnalysisRunRead>(`/analysis/${runId}`),
    enabled: runId !== undefined,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "queued" || status === "running" ? POLL_MS : false;
    },
  });
}
