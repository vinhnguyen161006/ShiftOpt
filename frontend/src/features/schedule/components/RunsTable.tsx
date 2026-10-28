import { Link } from "react-router";
import { Table } from "../../../components/ui/Table";
import type { SolveRunRead } from "../../../types/models";

type RunsTableProps = {
  runs: SolveRunRead[];
};

function statusLabel(run: SolveRunRead): string {
  if (run.status !== "succeeded") {
    return run.status;
  }
  return run.solver === "manual" ? "manual edit" : (run.solve_status ?? run.status);
}

export function RunsTable({ runs }: RunsTableProps) {
  return (
    <Table
      caption="Optimization runs"
      rows={runs}
      rowKey={(run) => run.id}
      columns={[
        {
          key: "run",
          label: "Run",
          render: (run) => <Link to={`/schedule/${run.id}`}>Run {run.id}</Link>,
        },
        {
          key: "created",
          label: "Created",
          render: (run) => new Date(run.created_at).toLocaleString("en-GB"),
        },
        {
          key: "status",
          label: "Result",
          render: (run) => (
            <span className={run.status === "failed" ? "tag tag-strong" : "tag tag-outline"}>
              {statusLabel(run)}
            </span>
          ),
        },
        {
          key: "gap",
          label: "Gap",
          align: "end",
          render: (run) => (run.gap === null ? "-" : `${(run.gap * 100).toFixed(2)}%`),
        },
        {
          key: "short",
          label: "Short hours",
          align: "end",
          render: (run) => run.understaffed_hours ?? "-",
        },
        {
          key: "violations",
          label: "Hard violations",
          align: "end",
          render: (run) => run.hard_violations ?? "-",
        },
        {
          key: "parent",
          label: "Edited from",
          render: (run) =>
            run.parent_run_id === null ? (
              "-"
            ) : (
              <Link to={`/schedule/${run.parent_run_id}`}>Run {run.parent_run_id}</Link>
            ),
        },
      ]}
    />
  );
}
