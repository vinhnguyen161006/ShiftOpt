import { useState } from "react";
import { Button } from "../../../components/ui/Button";
import { EmptyState, Loading, Notice } from "../../../components/ui/Feedback";
import { PageHeader } from "../../../components/ui/Layout";
import { Modal } from "../../../components/ui/Modal";
import { errorMessage } from "../../../lib/api-client";
import { vi } from "../../../locales/vi";
import type { EmployeeRead } from "../../../types/models";
import { useDeleteEmployee, useEmployees } from "../api/employees";
import { EmployeeCsvForm } from "./EmployeeCsvForm";
import { EmployeeForm } from "./EmployeeForm";
import { EmployeeTable } from "./EmployeeTable";

type Editing = { employee?: EmployeeRead } | undefined;

export function EmployeesPage() {
  const employees = useEmployees();
  const remove = useDeleteEmployee();
  const [editing, setEditing] = useState<Editing>(undefined);
  const [deleting, setDeleting] = useState<EmployeeRead | undefined>(undefined);
  const [importing, setImporting] = useState(false);

  const addButton = (
    <Button variant="primary" onClick={() => setEditing({})}>
      {vi.employees.add}
    </Button>
  );

  return (
    <div className="page">
      <PageHeader
        eyebrow={vi.employees.eyebrow}
        title={vi.employees.title}
        lead={vi.employees.lead}
        actions={
          <>
            <Button onClick={() => setImporting(true)}>{vi.employees.importCsv}</Button>
            {addButton}
          </>
        }
      />
      {employees.isPending && <Loading label={vi.employees.loading} />}
      {employees.isError && (
        <Notice kind="error" title={vi.employees.loadError}>
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
        <EmptyState title={vi.employees.emptyTitle} action={addButton}>
          {vi.employees.emptyBody}
        </EmptyState>
      )}
      <Modal
        title={editing?.employee ? vi.employees.editTitle(editing.employee.code) : vi.employees.add}
        open={editing !== undefined}
        onClose={() => setEditing(undefined)}
      >
        <EmployeeForm employee={editing?.employee} onDone={() => setEditing(undefined)} />
      </Modal>
      <Modal title={vi.employees.importCsv} open={importing} onClose={() => setImporting(false)}>
        <EmployeeCsvForm onDone={() => setImporting(false)} />
      </Modal>
      <Modal
        title={vi.employees.deleteTitle}
        open={deleting !== undefined}
        onClose={() => setDeleting(undefined)}
      >
        <p>{vi.employees.deleteBody(deleting?.name ?? "", deleting?.code ?? "")}</p>
        {remove.isError && <Notice kind="error" title={errorMessage(remove.error)} />}
        <div className="form-actions">
          <Button onClick={() => setDeleting(undefined)}>{vi.common.cancel}</Button>
          <Button
            variant="primary"
            disabled={remove.isPending}
            onClick={() =>
              deleting && remove.mutate(deleting.id, { onSuccess: () => setDeleting(undefined) })
            }
          >
            {vi.common.delete}
          </Button>
        </div>
      </Modal>
    </div>
  );
}
