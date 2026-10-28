import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch, jsonInit } from "../../../lib/api-client";
import type {
  CallCenterDemandRequest,
  CsvDemandRequest,
  DatasetDemandRequest,
  DemandProfileCreate,
  DemandProfileRead,
  DemandProfileUpdate,
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

export function useCreateDemandProfileFromDataset() {
  return useProfileMutation((body: DatasetDemandRequest) =>
    apiFetch<DemandProfileRead>("/demand-profiles/from-dataset", jsonInit("POST", body)),
  );
}

export function useCreateDemandProfileFromCsv() {
  return useProfileMutation((body: CsvDemandRequest) =>
    apiFetch<DemandProfileRead>("/demand-profiles/from-csv", jsonInit("POST", body)),
  );
}

export function useCreateDemandProfileFromCallCenter() {
  return useProfileMutation((body: CallCenterDemandRequest) =>
    apiFetch<DemandProfileRead>("/demand-profiles/from-call-center", jsonInit("POST", body)),
  );
}
