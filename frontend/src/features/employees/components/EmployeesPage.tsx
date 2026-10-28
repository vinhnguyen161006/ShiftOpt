import { useState } from "react";
import { Button } from "../../../components/ui/Button";
import { EmptyState, Loading, Notice } from "../../../components/ui/Feedback";
import { PageHeader } from "../../../components/ui/Layout";
import { Modal } from "../../../components/ui/Modal";
import { errorMessage } from "../../../lib/api-client";
import type { EmployeeRead } from "../../../types/models";
import { useDeleteEmployee, useEmployees } from "../api/employees";
import { EmployeeForm } from "./EmployeeForm";
import { EmployeeTable } from "./EmployeeTable";

type Editing = { employee?: EmployeeRead } | undefined;

export function EmployeesPage() {
  const employees = useEmployees();
  const remove = useDeleteEmployee();
  const [editing, setEditing] = useState<Editing>(undefined);
  const [deleting, setDeleting] = useState<EmployeeRead | undefined>(undefined);

  const addButton = (
    <Button variant="primary" onClick={() => setEditing({})}>
      Add employee
    </Button>
  );

  return (
    <div className="page">
      <PageHeader
        eyebrow="Workforce"
        title="Employees"
        lead="Each employee has an hourly wage, days they cannot work and days they would like off. Solved schedules keep a copy of the employees they used, so later edits here do not change past runs."
        actions={addButton}
      />
      {employees.isPending && <Loading label="Loading employees" />}
      {employees.isError && (
        <Notice kind="error" title="Could not load employees">
          {errorMessage(employees.error)}
        </Notice>
      )}
      {employees.data && employees.data.length > 0 && (
        <EmployeeTable
          employees={employees.data}
          onEdit={(employee) => setEditing({ employee })}
          onDelete={setDeleting}
        />
      )}
      {employees.data?.length === 0 && (
        <EmptyState title="Add the people you schedule" action={addButton}>
          The optimizer assigns shifts to these employees. Add at least as many people as your
          busiest hours need, plus enough to cover rest days.
        </EmptyState>
      )}
      <Modal
        title={editing?.employee ? `Edit ${editing.employee.code}` : "Add employee"}
        open={editing !== undefined}
        onClose={() => setEditing(undefined)}
      >
        <EmployeeForm employee={editing?.employee} onDone={() => setEditing(undefined)} />
      </Modal>
      <Modal
        title="Delete employee?"
        open={deleting !== undefined}
        onClose={() => setDeleting(undefined)}
      >
        <p>
          {deleting?.name} ({deleting?.code}) will be removed. Schedules already solved keep their
          own copy of this employee.
        </p>
        {remove.isError && <Notice kind="error" title={errorMessage(remove.error)} />}
        <div className="form-actions">
          <Button onClick={() => setDeleting(undefined)}>Cancel</Button>
          <Button
            variant="primary"
            disabled={remove.isPending}
            onClick={() =>
              deleting && remove.mutate(deleting.id, { onSuccess: () => setDeleting(undefined) })
            }
          >
            Delete
          </Button>
        </div>
      </Modal>
    </div>
  );
}
