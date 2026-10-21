import type { UseMutationResult, UseQueryResult } from "@tanstack/react-query";
import type {
  DatasetDemandRequest,
  DemandProfileCreate,
  DemandProfileRead,
  DemandProfileUpdate,
} from "../../../types/models";

export function useDemandProfiles(): UseQueryResult<DemandProfileRead[]> {
  throw new Error("TODO: useQuery GET /demand-profiles");
}

export function useDemandProfile(profileId: number): UseQueryResult<DemandProfileRead> {
  throw new Error("TODO: useQuery GET /demand-profiles/{profileId}");
}

export function useCreateDemandProfile(): UseMutationResult<
  DemandProfileRead,
  Error,
  DemandProfileCreate
> {
  throw new Error("TODO: useMutation POST /demand-profiles, invalidate the list");
}

export function useUpdateDemandProfile(
  profileId: number,
): UseMutationResult<DemandProfileRead, Error, DemandProfileUpdate> {
  throw new Error("TODO: useMutation PUT /demand-profiles/{profileId}");
}

export function useCreateDemandProfileFromDataset(): UseMutationResult<
  DemandProfileRead,
  Error,
  DatasetDemandRequest
> {
  throw new Error("TODO: useMutation POST /demand-profiles/from-dataset");
}
