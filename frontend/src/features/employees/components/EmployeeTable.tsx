import { Button } from "../../../components/ui/Button";
import { Table } from "../../../components/ui/Table";
import { dayList } from "../../../lib/time";
import type { EmployeeRead } from "../../../types/models";

type EmployeeTableProps = {
  employees: EmployeeRead[];
  onEdit: (employee: EmployeeRead) => void;
  onDelete: (employee: EmployeeRead) => void;
};

export function EmployeeTable({ employees, onEdit, onDelete }: EmployeeTableProps) {
  return (
    <Table
      caption="Employees"
      rows={employees}
      rowKey={(employee) => employee.id}
      columns={[
        { key: "code", label: "Code", render: (employee) => employee.code },
        { key: "name", label: "Name", render: (employee) => employee.name },
        {
          key: "wage",
          label: "Hourly wage",
          align: "end",
          render: (employee) => employee.hourly_wage.toLocaleString("en-US"),
        },
        {
          key: "unavailable",
          label: "Cannot work",
          render: (employee) => dayList(employee.unavailable_days),
        },
        {
          key: "preferred",
          label: "Prefers off",
          render: (employee) => dayList(employee.preferred_days_off),
        },
        {
          key: "actions",
          label: "Actions",
          render: (employee) => (
            <span className="tag-row">
              <Button size="sm" onClick={() => onEdit(employee)}>
                Edit<span className="visually-hidden"> {employee.code}</span>
              </Button>
              <Button size="sm" onClick={() => onDelete(employee)}>
                Delete<span className="visually-hidden"> {employee.code}</span>
              </Button>
            </span>
          ),
        },
      ]}
    />
  );
}
