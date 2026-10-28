import { Loading, Notice } from "../../../components/ui/Feedback";
import { KpiStrip } from "../../../components/ui/Layout";
import type { SolveRunRead } from "../../../types/models";
import { isActive } from "../api/schedules";
import "../schedule.css";

type SolveStatusPanelProps = {
  run: SolveRunRead;
};

function percent(value: number | null | undefined): string {
  return value === null || value === undefined ? "-" : `${(value * 100).toFixed(2)}%`;
}

function number(value: number | null | undefined): string {
  return value === null || value === undefined ? "-" : value.toLocaleString("en-US");
}

function verdict(run: SolveRunRead): { value: string; sub: string } {
  if (run.solver === "manual") {
    return { value: "MANUAL EDIT", sub: `edited from run ${run.parent_run_id ?? "-"}` };
  }
  if (run.solve_status === "optimal") {
    return { value: "OPTIMAL", sub: "proven optimal for this instance and time limit" };
  }
  if (run.solve_status === "feasible") {
    return { value: "FEASIBLE", sub: `not proven optimal, gap ${percent(run.gap)}` };
  }
  return { value: (run.solve_status ?? run.status).toUpperCase(), sub: "no proven result" };
}

export function SolveStatusPanel({ run }: SolveStatusPanelProps) {
  if (isActive(run.status)) {
    return (
      <Notice kind="info" title={run.status === "queued" ? "Queued" : "Solving"}>
        <Loading
          label={`The solver is working with a ${run.params.time_limit_seconds ?? "-"} s time limit. This page updates by itself.`}
        />
      </Notice>
    );
  }
  const result = verdict(run);
  const hardViolations = run.hard_violations ?? 0;
  return (
    <div className="form-stack">
      {run.status === "failed" && (
        <Notice kind="error" title="This run is not a valid schedule">
          {run.error ?? "The run failed."}
        </Notice>
      )}
      <KpiStrip
        items={[
          { label: "Solver status", value: result.value, sub: result.sub },
          { label: "Gap", value: percent(run.gap), sub: `best bound ${number(run.best_bound)}` },
          {
            label: "Objective",
            value: number(run.objective),
            sub: "last lexicographic tier",
          },
          {
            label: "Wall time",
            value: run.wall_time_seconds === null ? "-" : `${run.wall_time_seconds.toFixed(1)} s`,
            sub: `limit ${run.params.time_limit_seconds ?? "-"} s`,
          },
          {
            label: "Hard violations",
            value: run.hard_violations === null ? "-" : String(hardViolations),
            sub: hardViolations === 0 ? "checked by the validator" : "schedule not compliant",
          },
        ]}
      />
      <p className="muted run-meta">
        {run.solver}
        {run.solver_version ? ` ${run.solver_version}` : ""} &middot; seed{" "}
        {run.params.random_seed ?? "-"} &middot; {run.params.num_workers ?? "-"} worker(s) &middot;
        gap limit {percent(run.params.relative_gap_limit)}
      </p>
    </div>
  );
}
