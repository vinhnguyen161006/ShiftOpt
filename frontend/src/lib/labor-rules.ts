import { useQuery } from "@tanstack/react-query";
import type { LaborRulesRead } from "../types/models";
import { apiFetch } from "./api-client";

export function useLaborRules() {
  return useQuery({
    queryKey: ["labor-rules"],
    queryFn: () => apiFetch<LaborRulesRead>("/labor-rules"),
    staleTime: Number.POSITIVE_INFINITY,
  });
}
