import { Loading } from "../../../components/ui/Feedback";
import { KpiStrip } from "../../../components/ui/Layout";
import { WorkspaceBlock, WorkspacePanel } from "../../../components/ui/Workspace";
import { formatDecimal, formatPercent } from "../../../lib/number";
import { HOURS_PER_WEEK } from "../../../lib/time";
import { vi } from "../../../locales/vi";
import type { KpiRead, SolveRunRead } from "../../../types/models";
import { CoverageChart } from "./CoverageChart";
import { ScheduleGrid } from "./ScheduleGrid";
import { solveVerdict } from "./SolveStatusPanel";

type RunWorkspaceProps = {
  run: SolveRunRead;
  kpi: KpiRead | undefined;
};

const COST_SCALE = 100;
const COVERAGE_TARGET = "98,0%";
const CP_SAT_SOLVER = "ortools-cp-sat";

function money(hundredths: number): string {
  return (hundredths / COST_SCALE).toLocaleString("vi-VN", {
    maximumFractionDigits: 0,
  });
}

function paidHours(run: SolveRunRead): number {
  const lengths = new Map(run.shift_types.map((shift) => [shift.name, shift.length]));
  return (run.assignments ?? []).reduce(
    (total, assignment) => total + (lengths.get(assignment.shift_name) ?? 0),
    0,
  );
}

function rosterCaption(run: SolveRunRead): string {
  const shifts = run.assignments?.length ?? 0;
  const hours = paidHours(run).toLocaleString("vi-VN");
  return vi.schedule.workspace.rosterCaption(run.employee_codes.length, shifts, hours);
}

function runTag(run: SolveRunRead): string | undefined {
  if (run.solver === "manual") {
    return vi.schedule.workspace.manualEdit;
  }
  return run.repair_from_day === null || run.repair_from_day === undefined
    ? undefined
    : vi.schedule.workspace.repairTag;
}

function runMeta(run: SolveRunRead): string {
  if (run.solver === "manual") {
    return vi.schedule.workspace.manualEdit;
  }
  const solver = run.solver === CP_SAT_SOLVER ? "CP-SAT" : run.solver;
  const time =
    run.wall_time_seconds === null
      ? "-"
      : vi.schedule.workspace.seconds(formatDecimal(run.wall_time_seconds, 1));
  return vi.schedule.workspace.runMeta(
    solver,
    time,
    String(run.params.random_seed ?? "-"),
    String(run.params.num_workers ?? "-"),
  );
}

export function RunWorkspace({ run, kpi }: RunWorkspaceProps) {
  const verdict = solveVerdict(run);
  return (
    <WorkspacePanel
      name={vi.schedule.workspace.run(run.id)}
      meta={new Date(run.created_at).toLocaleString("vi-VN")}
      tag={runTag(run)}
    >
      {kpi ? (
        <KpiStrip
          flush
          items={[
            {
              label: vi.schedule.workspace.coverage,
              value: formatPercent(kpi.coverage_ratio, 1),
              sub: vi.schedule.workspace.coverageSub(COVERAGE_TARGET),
            },
            {
              label: vi.schedule.workspace.laborCost,
              value: money(kpi.labor_cost),
              sub: vi.schedule.workspace.laborCostSub,
            },
            {
              label: vi.schedule.workspace.understaffed,
              value: vi.home.sample.hours(kpi.understaffed_hours),
              sub: vi.schedule.workspace.understaffedSub(HOURS_PER_WEEK),
            },
            {
              label: vi.schedule.workspace.solverStatus,
              value: verdict.value,
              sub: verdict.sub,
              accent: true,
            },
            ...(run.changes === null || run.changes === undefined
              ? []
              : [
                  {
                    label: vi.schedule.workspace.changes,
                    value: String(run.changes),
                    sub: vi.schedule.workspace.changesSub,
                  },
                ]),
          ]}
        />
      ) : (
        <div className="workspace-block">
          <Loading label={vi.schedule.workspace.computing} />
        </div>
      )}
      <WorkspaceBlock title={vi.schedule.workspace.roster} caption={rosterCaption(run)}>
        <ScheduleGrid run={run} />
      </WorkspaceBlock>
      {kpi && <CoverageChart kpi={kpi} meta={runMeta(run)} />}
    </WorkspacePanel>
  );
}
