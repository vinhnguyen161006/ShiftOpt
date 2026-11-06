import { useSearchParams } from "react-router";
import { EmptyState, Loading, Notice } from "../../components/ui/Feedback";
import { Field } from "../../components/ui/Field";
import { PageHeader, Panel } from "../../components/ui/Layout";
import { useDemandProfiles } from "../../features/demand/api/demand";
import { useEmployees } from "../../features/employees/api/employees";
import { useScheduleKpi, useScheduleRuns } from "../../features/schedule/api/schedules";
import { useShiftTemplates } from "../../features/shift-templates/api/shift-templates";
import { useAnalysisRun } from "../../features/what-if/api/analysis";
import { AnalysisStatus } from "../../features/what-if/components/AnalysisStatus";
import { ScenarioCompare } from "../../features/what-if/components/ScenarioCompare";
import { SensitivityHeatmap } from "../../features/what-if/components/SensitivityHeatmap";
import { StaffingSweepView } from "../../features/what-if/components/StaffingSweepView";
import { SweepView } from "../../features/what-if/components/SweepView";
import { WhatIfSetup } from "../../features/what-if/components/WhatIfSetup";
import { errorMessage } from "../../lib/api-client";
import { useLaborRules } from "../../lib/labor-rules";
import { vi } from "../../locales/vi";
import type {
  AnalysisRunRead,
  DemandSweepResult,
  MarginalCostResult,
  SolveRunRead,
  StaffingSweepResult,
} from "../../types/models";

function numberParam(params: URLSearchParams, key: string): number | undefined {
  const value = Number(params.get(key));
  return Number.isInteger(value) && value > 0 ? value : undefined;
}

function isSweep(
  run: AnalysisRunRead | undefined,
): run is AnalysisRunRead & { result: DemandSweepResult } {
  return run?.kind === "demand_sweep" && run.result !== null && run.result !== undefined;
}

function isStaffing(
  run: AnalysisRunRead | undefined,
): run is AnalysisRunRead & { result: StaffingSweepResult } {
  return run?.kind === "staffing_sweep" && run.result !== null && run.result !== undefined;
}

function isMarginal(
  run: AnalysisRunRead | undefined,
): run is AnalysisRunRead & { result: MarginalCostResult } {
  return run?.result !== null && run?.result !== undefined && "marginal_cost_by_hour" in run.result;
}

function SetupPanel({
  onStarted,
}: {
  onStarted: (kind: "sweep" | "marginal" | "staffing", runId: number) => void;
}) {
  const profiles = useDemandProfiles();
  const templates = useShiftTemplates();
  const employees = useEmployees();
  const rules = useLaborRules();
  const failed = [profiles, templates, employees, rules].find((query) => query.isError);
  if (failed) {
    return (
      <Notice kind="error" title={vi.whatIf.inputsError}>
        {errorMessage(failed.error)}
      </Notice>
    );
  }
  if (!profiles.data || !templates.data || !employees.data || !rules.data) {
    return <Loading label={vi.whatIf.loadingInputs} />;
  }
  if (profiles.data.length === 0 || templates.data.length === 0 || employees.data.length === 0) {
    return <EmptyState title={vi.whatIf.addInputsTitle}>{vi.whatIf.addInputsBody}</EmptyState>;
  }
  return (
    <WhatIfSetup
      profiles={profiles.data}
      templates={templates.data}
      employeeCount={employees.data.length}
      rules={rules.data}
      onStarted={onStarted}
    />
  );
}

function runLabel(run: SolveRunRead): string {
  const status =
    run.solver === "manual"
      ? vi.whatIf.compare.manualEdit
      : (vi.schedule.solveStatus[run.solve_status ?? ""] ?? run.solve_status ?? run.status);
  return vi.whatIf.runLabel(run.id, status);
}

function ComparePanel({
  baselineId,
  scenarioId,
  onChange,
}: {
  baselineId: number | undefined;
  scenarioId: number | undefined;
  onChange: (key: "base" | "compare", runId: number | undefined) => void;
}) {
  const runs = useScheduleRuns();
  const finished = (runs.data ?? []).filter((run) => run.assignments !== null);
  const baseline = finished.find((run) => run.id === baselineId);
  const scenario = finished.find((run) => run.id === scenarioId);
  const baselineKpi = useScheduleKpi(baseline?.id, baseline !== undefined);
  const scenarioKpi = useScheduleKpi(scenario?.id, scenario !== undefined);

  if (runs.isPending) {
    return <Loading label={vi.whatIf.loadingRuns} />;
  }
  if (finished.length < 2) {
    return <EmptyState title={vi.whatIf.twoRunsTitle}>{vi.whatIf.twoRunsBody}</EmptyState>;
  }
  const picker = (key: "base" | "compare", label: string, value: number | undefined) => (
    <Field id={`compare-${key}`} label={label}>
      {(control) => (
        <select
          {...control}
          className="input"
          value={value ?? ""}
          onChange={(event) => onChange(key, Number(event.target.value) || undefined)}
        >
          <option value="">{vi.whatIf.chooseRun}</option>
          {finished.map((run) => (
            <option key={run.id} value={run.id}>
              {runLabel(run)}
            </option>
          ))}
        </select>
      )}
    </Field>
  );
  return (
    <div>
      <div className="compare-pickers">
        {picker("base", vi.whatIf.baseline, baselineId)}
        {picker("compare", vi.whatIf.scenario, scenarioId)}
      </div>
      {baseline && scenario && (
        <ScenarioCompare
          baseline={{ run: baseline, kpi: baselineKpi.data }}
          scenario={{ run: scenario, kpi: scenarioKpi.data }}
        />
      )}
    </div>
  );
}

export function WhatIfRoute() {
  const [params, setParams] = useSearchParams();
  const sweepId = numberParam(params, "sweep");
  const marginalId = numberParam(params, "marginal");
  const staffingId = numberParam(params, "staffing");
  const sweep = useAnalysisRun(sweepId);
  const marginal = useAnalysisRun(marginalId);
  const staffing = useAnalysisRun(staffingId);
  const sweepResult =
    sweep.data?.status === "succeeded" && isSweep(sweep.data) ? sweep.data.result : undefined;

  function setParam(key: string, value: number | undefined) {
    const next = new URLSearchParams(params);
    if (value === undefined) {
      next.delete(key);
    } else {
      next.set(key, String(value));
    }
    setParams(next);
  }

  return (
    <div className="page">
      <PageHeader eyebrow={vi.whatIf.eyebrow} title={vi.whatIf.title} lead={vi.whatIf.lead} />
      <Panel title={vi.whatIf.setup} labelledBy="whatif-setup-title">
        <SetupPanel onStarted={(kind, runId) => setParam(kind, runId)} />
      </Panel>
      {sweepResult ? (
        <SweepView key={sweep.data?.id} result={sweepResult} />
      ) : (
        <Panel title={vi.whatIf.sweepPanel} labelledBy="sweep-title">
          {sweepId === undefined && (
            <EmptyState title={vi.whatIf.noSweepTitle}>{vi.whatIf.noSweepBody}</EmptyState>
          )}
          {sweep.isError && <Notice kind="error" title={errorMessage(sweep.error)} />}
          {sweep.data && (
            <AnalysisStatus run={sweep.data} activeLabel={vi.whatIf.sweepActive(sweep.data.id)}>
              {null}
            </AnalysisStatus>
          )}
        </Panel>
      )}
      <Panel title={vi.whatIf.staffingPanel} labelledBy="staffing-title">
        {staffingId === undefined && (
          <EmptyState title={vi.whatIf.noStaffingTitle}>{vi.whatIf.noStaffingBody}</EmptyState>
        )}
        {staffing.isError && <Notice kind="error" title={errorMessage(staffing.error)} />}
        {staffing.data && (
          <AnalysisStatus
            run={staffing.data}
            activeLabel={vi.whatIf.staffingActive(staffing.data.id)}
          >
            {isStaffing(staffing.data) && <StaffingSweepView result={staffing.data.result} />}
          </AnalysisStatus>
        )}
      </Panel>
      <Panel title={vi.whatIf.marginalPanel} labelledBy="marginal-title">
        {marginalId === undefined && (
          <EmptyState title={vi.whatIf.noMarginalTitle}>{vi.whatIf.noMarginalBody}</EmptyState>
        )}
        {marginal.isError && <Notice kind="error" title={errorMessage(marginal.error)} />}
        {marginal.data && (
          <AnalysisStatus
            run={marginal.data}
            activeLabel={vi.whatIf.marginalActive(marginal.data.id)}
          >
            {isMarginal(marginal.data) && <SensitivityHeatmap result={marginal.data.result} />}
          </AnalysisStatus>
        )}
      </Panel>
      <Panel title={vi.whatIf.comparePanel} labelledBy="compare-title">
        <ComparePanel
          baselineId={numberParam(params, "base")}
          scenarioId={numberParam(params, "compare")}
          onChange={setParam}
        />
      </Panel>
    </div>
  );
}
