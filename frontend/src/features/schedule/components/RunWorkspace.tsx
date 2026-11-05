import { Loading } from "../../../components/ui/Feedback";
import { KpiStrip } from "../../../components/ui/Layout";
import { WorkspaceBlock, WorkspacePanel } from "../../../components/ui/Workspace";
import { HOURS_PER_WEEK } from "../../../lib/time";
import type { KpiRead, SolveRunRead } from "../../../types/models";
import { CoverageChart } from "./CoverageChart";
import { ScheduleGrid } from "./ScheduleGrid";
import { solveVerdict } from "./SolveStatusPanel";

type RunWorkspaceProps = {
  run: SolveRunRead;
  kpi: KpiRead | undefined;
};

const COST_SCALE = 100;
const COVERAGE_TARGET = "98.0%";
const CP_SAT_SOLVER = "ortools-cp-sat";
const SEPARATOR = ` ${String.fromCharCode(0xb7)} `;

function money(hundredths: number): string {
  return (hundredths / COST_SCALE).toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
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
  const hours = paidHours(run).toLocaleString("en-US");
  return [`${run.employee_codes.length} employees`, `${shifts} assigned shifts`, `${hours} h`].join(
    SEPARATOR,
  );
}

function runMeta(run: SolveRunRead): string {
  if (run.solver === "manual") {
    return "Manual edit";
  }
  const solver = run.solver === CP_SAT_SOLVER ? "CP-SAT" : run.solver;
  const time = run.wall_time_seconds === null ? "-" : `${run.wall_time_seconds.toFixed(1)} s`;
  const workers = run.params.num_workers ?? "-";
  const unit = workers === 1 ? "worker" : "workers";
  return [solver, time, `seed ${run.params.random_seed ?? "-"}`, `${workers} ${unit}`].join(
    SEPARATOR,
  );
}

export function RunWorkspace({ run, kpi }: RunWorkspaceProps) {
  const verdict = solveVerdict(run);
  return (
    <WorkspacePanel
      name={`Run ${run.id}`}
      meta={new Date(run.created_at).toLocaleString("en-GB")}
      tag={run.solver === "manual" ? "Manual edit" : undefined}
    >
      {kpi ? (
        <KpiStrip
          flush
          items={[
            {
              label: "Coverage ratio",
              value: `${(kpi.coverage_ratio * 100).toFixed(1)}%`,
              sub: `target ${COVERAGE_TARGET}`,
            },
            {
              label: "Labor cost",
              value: money(kpi.labor_cost),
              sub: "incl. night allowance",
            },
            {
              label: "Understaffed hours",
              value: `${kpi.understaffed_hours} h`,
              sub: `of ${HOURS_PER_WEEK} week hours`,
            },
            { label: "Solver status", value: verdict.value, sub: verdict.sub, accent: true },
          ]}
        />
      ) : (
        <div className="workspace-block">
          <Loading label="Computing KPIs" />
        </div>
      )}
      <WorkspaceBlock title="Weekly roster" caption={rosterCaption(run)}>
        <ScheduleGrid run={run} />
      </WorkspaceBlock>
      {kpi && <CoverageChart kpi={kpi} meta={runMeta(run)} />}
    </WorkspacePanel>
  );
}
