import type { UseQueryResult } from "@tanstack/react-query";
import type { ComplianceRead } from "../../../types/models";

export function useCompliance(runId: number): UseQueryResult<ComplianceRead> {
  throw new Error("TODO: useQuery GET /schedules/{runId}/compliance");
}
