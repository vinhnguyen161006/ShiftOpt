import type { SolveRunRead } from "../../../types/models";

type ScheduleGridProps = {
  run: SolveRunRead;
};

export function ScheduleGrid({ run }: ScheduleGridProps) {
  return (
    <p className="todo">
      TODO: rows = employees, columns = Monday to Sunday, cells colored by shift type, off days
      blank. Run {run.id}.
    </p>
  );
}
