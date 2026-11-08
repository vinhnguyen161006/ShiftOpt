import { Loading, Notice } from "../../../components/ui/Feedback";
import { Table } from "../../../components/ui/Table";
import { errorMessage } from "../../../lib/api-client";
import { DAY_NAMES } from "../../../lib/time";
import { vi } from "../../../locales/vi";
import type { AssignmentRead } from "../../../types/models";
import { useScheduleChanges } from "../api/reroster";

type ChangesSummaryProps = {
  runId: number;
  parentId: number;
};

type Change = AssignmentRead & { change: "added" | "removed" };

export function ChangesSummary({ runId, parentId }: ChangesSummaryProps) {
  const changes = useScheduleChanges(runId, true);
  if (changes.isPending) {
    return <Loading label={vi.schedule.reroster.loadingChanges} />;
  }
  if (changes.isError) {
    return <Notice kind="error" title={errorMessage(changes.error)} />;
  }
  const { kept, added, removed } = changes.data;
  const rows: Change[] = [
    ...added.map((assignment) => ({ ...assignment, change: "added" as const })),
    ...removed.map((assignment) => ({ ...assignment, change: "removed" as const })),
  ].sort((a, b) => a.day - b.day || a.employee_code.localeCompare(b.employee_code));

  return (
    <div className="form-stack">
      <p>{vi.schedule.reroster.summary(kept.length, added.length, removed.length)}</p>
      <Table
        caption={vi.schedule.reroster.caption(parentId)}
        rows={rows}
        rowKey={(row) => `${row.change}-${row.employee_code}-${row.day}-${row.shift_name}`}
        empty={<p className="muted">{vi.schedule.reroster.noChanges}</p>}
        columns={[
          {
            key: "change",
            label: vi.schedule.reroster.columnChange,
            render: (row) => (
              <span className="tag tag-outline">
                {row.change === "added"
                  ? vi.schedule.reroster.changeAdded
                  : vi.schedule.reroster.changeRemoved}
              </span>
            ),
          },
          {
            key: "employee",
            label: vi.schedule.reroster.columnEmployee,
            render: (row) => row.employee_code,
          },
          {
            key: "day",
            label: vi.schedule.reroster.columnDay,
            render: (row) => DAY_NAMES[row.day],
          },
          {
            key: "shift",
            label: vi.schedule.reroster.columnShift,
            render: (row) => row.shift_name,
          },
        ]}
      />
    </div>
  );
}
