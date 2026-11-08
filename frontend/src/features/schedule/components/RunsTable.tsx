import { Link } from "react-router";
import { Table } from "../../../components/ui/Table";
import { formatPercent } from "../../../lib/number";
import { isRepairRun } from "../../../lib/run-kind";
import { vi } from "../../../locales/vi";
import type { SolveRunRead } from "../../../types/models";

type RunsTableProps = {
  runs: SolveRunRead[];
};

function statusLabel(run: SolveRunRead): string {
  if (run.status !== "succeeded") {
    return vi.schedule.runStatus[run.status] ?? run.status;
  }
  if (run.solver === "manual") {
    return vi.schedule.runs.manualEdit;
  }
  const status = run.solve_status ?? run.status;
  return vi.schedule.solveStatus[status] ?? status;
}

export function RunsTable({ runs }: RunsTableProps) {
  return (
    <Table
      caption={vi.schedule.runs.caption}
      rows={runs}
      rowKey={(run) => run.id}
      columns={[
        {
          key: "run",
          label: vi.schedule.runs.run,
          render: (run) => (
            <Link to={`/schedule/${run.id}`}>{vi.schedule.runs.runLink(run.id)}</Link>
          ),
        },
        {
          key: "created",
          label: vi.schedule.runs.created,
          render: (run) => new Date(run.created_at).toLocaleString("vi-VN"),
        },
        {
          key: "status",
          label: vi.schedule.runs.result,
          render: (run) => (
            <span className={run.status === "failed" ? "tag tag-strong" : "tag tag-outline"}>
              {statusLabel(run)}
            </span>
          ),
        },
        {
          key: "gap",
          label: vi.schedule.runs.gap,
          align: "end",
          render: (run) => (run.gap === null ? "-" : formatPercent(run.gap, 2)),
        },
        {
          key: "short",
          label: vi.schedule.runs.short,
          align: "end",
          render: (run) => run.understaffed_hours ?? "-",
        },
        {
          key: "violations",
          label: vi.schedule.runs.violations,
          align: "end",
          render: (run) => run.hard_violations ?? "-",
        },
        {
          key: "parent",
          label: vi.schedule.runs.editedFrom,
          render: (run) =>
            run.parent_run_id === null ? (
              "-"
            ) : (
              <>
                <Link to={`/schedule/${run.parent_run_id}`}>
                  {vi.schedule.runs.runLink(run.parent_run_id)}
                </Link>{" "}
                <span className="tag tag-outline">
                  {isRepairRun(run) ? vi.schedule.runs.repairTag : vi.schedule.runs.manualEdit}
                </span>
              </>
            ),
        },
      ]}
    />
  );
}
