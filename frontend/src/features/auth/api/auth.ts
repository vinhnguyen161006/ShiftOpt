import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch, jsonInit } from "../../../lib/api-client";
import type { UserRead } from "../../../types/models";

export const ME_KEY = ["auth", "me"];

export type Credentials = { email: string; password: string };
export type RegisterInput = Credentials & { display_name: string };

export function useMe() {
  return useQuery({
    queryKey: ME_KEY,
    queryFn: () => apiFetch<UserRead>("/auth/me"),
    retry: false,
    staleTime: 60_000,
  });
}

export function useLogin() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: Credentials) => apiFetch<UserRead>("/auth/login", jsonInit("POST", body)),
    onSuccess: (user) => queryClient.setQueryData(ME_KEY, user),
  });
}

export function useRegister() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: RegisterInput) =>
      apiFetch<UserRead>("/auth/register", jsonInit("POST", body)),
    onSuccess: (user) => queryClient.setQueryData(ME_KEY, user),
  });
}

export function useLogout() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => apiFetch<void>("/auth/logout", jsonInit("POST")),
    onSettled: () => queryClient.removeQueries({ queryKey: ME_KEY }),
  });
}
