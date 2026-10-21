import type { SolveRunRead } from "../../../types/models";

type SolveStatusPanelProps = {
  run: SolveRunRead;
};

export function SolveStatusPanel({ run }: SolveStatusPanelProps) {
  return (
    <p className="todo">
      TODO: job status, solver status, gap, best bound and wall time. Say "optimal" only for
      solve_status optimal; feasible shows the gap. Status {run.status}.
    </p>
  );
}
