import { Button } from "../../../components/ui/Button";
import { Table } from "../../../components/ui/Table";
import { dayList } from "../../../lib/time";
import { vi } from "../../../locales/vi";
import type { EmployeeRead } from "../../../types/models";

type EmployeeTableProps = {
  employees: EmployeeRead[];
  onEdit: (employee: EmployeeRead) => void;
  onDelete: (employee: EmployeeRead) => void;
};

export function EmployeeTable({ employees, onEdit, onDelete }: EmployeeTableProps) {
  return (
    <Table
      caption={vi.employees.table.caption}
      rows={employees}
      rowKey={(employee) => employee.id}
      columns={[
        { key: "code", label: vi.employees.table.code, render: (employee) => employee.code },
        { key: "name", label: vi.employees.table.name, render: (employee) => employee.name },
        {
          key: "wage",
          label: vi.employees.table.wage,
          align: "end",
          render: (employee) => employee.hourly_wage.toLocaleString("vi-VN"),
        },
        {
          key: "max_hours",
          label: vi.employees.table.maxHours,
          align: "end",
          render: (employee) => employee.max_weekly_hours ?? vi.employees.table.lawLimit,
        },
        {
          key: "unavailable",
          label: vi.employees.table.cannotWork,
          render: (employee) => dayList(employee.unavailable_days),
        },
        {
          key: "preferred",
          label: vi.employees.table.prefersOff,
          render: (employee) => dayList(employee.preferred_days_off),
        },
        {
          key: "actions",
          label: vi.common.actions,
          render: (employee) => (
            <span className="tag-row">
              <Button size="sm" onClick={() => onEdit(employee)}>
                {vi.common.edit}
                <span className="visually-hidden"> {employee.code}</span>
              </Button>
              <Button size="sm" onClick={() => onDelete(employee)}>
                {vi.common.delete}
                <span className="visually-hidden"> {employee.code}</span>
              </Button>
            </span>
          ),
        },
      ]}
    />
  );
}
