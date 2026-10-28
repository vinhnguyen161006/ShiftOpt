import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch, jsonInit } from "../../../lib/api-client";
import type { EmployeeCreate, EmployeeRead } from "../../../types/models";

const EMPLOYEES_KEY = ["employees"];

export function useEmployees() {
  return useQuery({
    queryKey: EMPLOYEES_KEY,
    queryFn: () => apiFetch<EmployeeRead[]>("/employees"),
  });
}

function useEmployeeMutation<V, R>(request: (variables: V) => Promise<R>) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: request,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: EMPLOYEES_KEY }),
  });
}

export function useSaveEmployee() {
  return useEmployeeMutation(({ id, body }: { id?: number; body: EmployeeCreate }) =>
    id === undefined
      ? apiFetch<EmployeeRead>("/employees", jsonInit("POST", body))
      : apiFetch<EmployeeRead>(`/employees/${id}`, jsonInit("PUT", body)),
  );
}

export function useDeleteEmployee() {
  return useEmployeeMutation((id: number) =>
    apiFetch<void>(`/employees/${id}`, jsonInit("DELETE")),
  );
}
