import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch, jsonInit } from "../../../lib/api-client";
import type {
  CsvDemandRequest,
  DemandProfileCreate,
  DemandProfileRead,
  DemandProfileUpdate,
  SalesIngestQuery,
  SalesInspection,
} from "../../../types/models";

const PROFILES_KEY = ["demand-profiles"];

export function useDemandProfiles() {
  return useQuery({
    queryKey: PROFILES_KEY,
    queryFn: () => apiFetch<DemandProfileRead[]>("/demand-profiles"),
  });
}

function useProfileMutation<V, R = DemandProfileRead>(request: (variables: V) => Promise<R>) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: request,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: PROFILES_KEY }),
  });
}

export function useCreateDemandProfile() {
  return useProfileMutation((body: DemandProfileCreate) =>
    apiFetch<DemandProfileRead>("/demand-profiles", jsonInit("POST", body)),
  );
}

export function useUpdateDemandProfile() {
  return useProfileMutation(({ id, body }: { id: number; body: DemandProfileUpdate }) =>
    apiFetch<DemandProfileRead>(`/demand-profiles/${id}`, jsonInit("PUT", body)),
  );
}

export function useDeleteDemandProfile() {
  return useProfileMutation((id: number) =>
    apiFetch<void>(`/demand-profiles/${id}`, jsonInit("DELETE")),
  );
}

export function useCreateDemandProfileFromCsv() {
  return useProfileMutation((body: CsvDemandRequest) =>
    apiFetch<DemandProfileRead>("/demand-profiles/from-csv", jsonInit("POST", body)),
  );
}

export function useInspectSales() {
  return useMutation({
    mutationFn: (file: File) =>
      apiFetch<SalesInspection>("/demand-profiles/ingest/inspect", {
        method: "POST",
        body: file,
        headers: { "Content-Type": "application/octet-stream" },
      }),
  });
}

export function useIngestSales() {
  return useProfileMutation(({ file, query }: { file: File; query: SalesIngestQuery }) => {
    const search = new URLSearchParams();
    for (const [key, value] of Object.entries(query)) {
      if (value !== undefined && value !== null && value !== "") {
        search.set(key, String(value));
      }
    }
    return apiFetch<DemandProfileRead>(`/demand-profiles/ingest?${search}`, {
      method: "POST",
      body: file,
      headers: { "Content-Type": "application/octet-stream" },
    });
  });
}
