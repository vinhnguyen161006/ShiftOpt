import type { UseMutationResult, UseQueryResult } from "@tanstack/react-query";
import type { EmployeeCreate, EmployeeRead } from "../../../types/models";

export function useEmployees(): UseQueryResult<EmployeeRead[]> {
  throw new Error("TODO: useQuery GET /employees");
}

export function useCreateEmployee(): UseMutationResult<EmployeeRead, Error, EmployeeCreate> {
  throw new Error("TODO: useMutation POST /employees, invalidate the list");
}

export function useUpdateEmployee(
  employeeId: number,
): UseMutationResult<EmployeeRead, Error, EmployeeCreate> {
  throw new Error("TODO: useMutation PUT /employees/{employeeId}");
}

export function useDeleteEmployee(): UseMutationResult<void, Error, number> {
  throw new Error("TODO: useMutation DELETE /employees/{employeeId}");
}
