import { Loading, Notice } from "../../../components/ui/Feedback";
import { KpiStrip } from "../../../components/ui/Layout";
import type { SolveRunRead } from "../../../types/models";
import { isActive } from "../api/schedules";
import "../schedule.css";
import { formatDecimal, formatPercent } from "../../../lib/number";
import { vi } from "../../../locales/vi";

type SolveRunProps = {
  run: SolveRunRead;
};

function percent(value: number | null | undefined): string {
  return value === null || value === undefined ? "-" : formatPercent(value, 2);
}

function number(value: number | null | undefined): string {
  return value === null || value === undefined ? "-" : value.toLocaleString("vi-VN");
}

export function solveVerdict(run: SolveRunRead): { value: string; sub: string } {
  if (run.solver === "manual") {
    return {
      value: vi.schedule.verdict.manualValue,
      sub: vi.schedule.verdict.manualSub(String(run.parent_run_id ?? "-")),
    };
  }
  if (run.solve_status === "optimal") {
    return { value: "OPTIMAL", sub: vi.schedule.verdict.optimalSub };
  }
  if (run.solve_status === "feasible") {
    return { value: "FEASIBLE", sub: vi.schedule.verdict.feasibleSub(percent(run.gap)) };
  }
  return {
    value: (run.solve_status ?? run.status).toUpperCase(),
    sub: vi.schedule.verdict.noProven,
  };
}

export function SolveNotice({ run }: SolveRunProps) {
  if (isActive(run.status)) {
    return (
      <Notice
        kind="info"
        title={run.status === "queued" ? vi.schedule.notice.queued : vi.schedule.notice.solving}
      >
        <Loading label={vi.schedule.notice.working(String(run.params.time_limit_seconds ?? "-"))} />
      </Notice>
    );
  }
  if (run.status === "failed") {
    return (
      <Notice kind="error" title={vi.schedule.notice.failedTitle}>
        {run.error ?? vi.schedule.notice.failedBody}
      </Notice>
    );
  }
  return null;
}

export function SolveDetails({ run }: SolveRunProps) {
  const hardViolations = run.hard_violations ?? 0;
  return (
    <div className="form-stack">
      <KpiStrip
        items={[
          {
            label: vi.schedule.details.gap,
            value: percent(run.gap),
            sub: vi.schedule.details.bestBound(number(run.best_bound)),
          },
          {
            label: vi.schedule.details.objective,
            value: number(run.objective),
            sub: vi.schedule.details.lastTier,
          },
          {
            label: vi.schedule.details.wallTime,
            value:
              run.wall_time_seconds === null
                ? "-"
                : vi.schedule.workspace.seconds(formatDecimal(run.wall_time_seconds, 1)),
            sub: vi.schedule.details.limit(String(run.params.time_limit_seconds ?? "-")),
          },
          {
            label: vi.schedule.details.hard,
            value: run.hard_violations === null ? "-" : String(hardViolations),
            sub:
              hardViolations === 0 ? vi.schedule.details.checked : vi.schedule.details.notCompliant,
          },
        ]}
      />
      <p className="muted run-meta">
        {vi.schedule.details.meta(
          `${run.solver}${run.solver_version ? ` ${run.solver_version}` : ""}`,
          String(run.params.random_seed ?? "-"),
          String(run.params.num_workers ?? "-"),
          percent(run.params.relative_gap_limit),
        )}
      </p>
    </div>
  );
}
