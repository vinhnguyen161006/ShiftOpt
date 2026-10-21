import type { EmployeeRead } from "../../../types/models";

type EmployeeTableProps = {
  employees: EmployeeRead[];
  onEdit: (employee: EmployeeRead) => void;
  onDelete: (employeeId: number) => void;
};

export function EmployeeTable({ employees, onEdit, onDelete }: EmployeeTableProps) {
  return (
    <p className="todo">
      TODO: table of code, name and hourly wage with edit and delete actions. Rows:{" "}
      {employees.length}.
    </p>
  );
}
