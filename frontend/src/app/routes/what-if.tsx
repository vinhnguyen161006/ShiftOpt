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
import { SweepView } from "../../features/what-if/components/SweepView";
import { WhatIfSetup } from "../../features/what-if/components/WhatIfSetup";
import { errorMessage } from "../../lib/api-client";
import { useLaborRules } from "../../lib/labor-rules";
import type {
  AnalysisRunRead,
  DemandSweepResult,
  MarginalCostResult,
  SolveRunRead,
} from "../../types/models";

function numberParam(params: URLSearchParams, key: string): number | undefined {
  const value = Number(params.get(key));
  return Number.isInteger(value) && value > 0 ? value : undefined;
}

function isSweep(
  run: AnalysisRunRead | undefined,
): run is AnalysisRunRead & { result: DemandSweepResult } {
  return run?.result !== null && run?.result !== undefined && "points" in run.result;
}

function isMarginal(
  run: AnalysisRunRead | undefined,
): run is AnalysisRunRead & { result: MarginalCostResult } {
  return run?.result !== null && run?.result !== undefined && "marginal_cost_by_hour" in run.result;
}

function SetupPanel({
  onStarted,
}: {
  onStarted: (kind: "sweep" | "marginal", runId: number) => void;
}) {
  const profiles = useDemandProfiles();
  const templates = useShiftTemplates();
  const employees = useEmployees();
  const rules = useLaborRules();
  const failed = [profiles, templates, employees, rules].find((query) => query.isError);
  if (failed) {
    return (
      <Notice kind="error" title="Could not load the inputs">
        {errorMessage(failed.error)}
      </Notice>
    );
  }
  if (!profiles.data || !templates.data || !employees.data || !rules.data) {
    return <Loading label="Loading inputs" />;
  }
  if (profiles.data.length === 0 || templates.data.length === 0 || employees.data.length === 0) {
    return (
      <EmptyState title="Add inputs first">
        A what-if analysis re-solves the same instance as an optimization run, so it needs a demand
        profile, shift templates and employees.
      </EmptyState>
    );
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
  return `Run ${run.id} (${run.solver === "manual" ? "manual edit" : (run.solve_status ?? run.status)})`;
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
    return <Loading label="Loading runs" />;
  }
  if (finished.length < 2) {
    return (
      <EmptyState title="Two runs are needed">
        Optimize the same demand under two settings, for example 48 and 40 hours per week, then
        compare them here.
      </EmptyState>
    );
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
          <option value="">Choose a run</option>
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
        {picker("base", "Baseline", baselineId)}
        {picker("compare", "Scenario", scenarioId)}
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
  const sweep = useAnalysisRun(sweepId);
  const marginal = useAnalysisRun(marginalId);

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
      <PageHeader
        eyebrow="What-if"
        title="Sensitivity of cost and coverage"
        lead="Every number here comes from solving again: the demand sweep re-solves the roster at each multiplier, and the marginal cost of an hour is the cost difference after requiring one more person in it. LP duals are shown only as an approximation."
      />
      <Panel title="Set up an analysis" labelledBy="whatif-setup-title">
        <SetupPanel onStarted={(kind, runId) => setParam(kind, runId)} />
      </Panel>
      <Panel title="Demand sweep z(lambda)" labelledBy="sweep-title">
        {sweepId === undefined && (
          <EmptyState title="No sweep yet">
            Run a demand sweep above to draw the cost curve.
          </EmptyState>
        )}
        {sweep.isError && <Notice kind="error" title={errorMessage(sweep.error)} />}
        {sweep.data && (
          <AnalysisStatus
            run={sweep.data}
            activeLabel={`Re-solving at each multiplier (analysis ${sweep.data.id})`}
          >
            {isSweep(sweep.data) && <SweepView result={sweep.data.result} />}
          </AnalysisStatus>
        )}
      </Panel>
      <Panel title="Marginal cost by hour" labelledBy="marginal-title">
        {marginalId === undefined && (
          <EmptyState title="No marginal cost yet">
            Run the marginal cost analysis above to fill the 7 x 24 heatmap.
          </EmptyState>
        )}
        {marginal.isError && <Notice kind="error" title={errorMessage(marginal.error)} />}
        {marginal.data && (
          <AnalysisStatus
            run={marginal.data}
            activeLabel={`Re-solving 169 times (analysis ${marginal.data.id})`}
          >
            {isMarginal(marginal.data) && <SensitivityHeatmap result={marginal.data.result} />}
          </AnalysisStatus>
        )}
      </Panel>
      <Panel title="Compare two runs" labelledBy="compare-title">
        <ComparePanel
          baselineId={numberParam(params, "base")}
          scenarioId={numberParam(params, "compare")}
          onChange={setParam}
        />
      </Panel>
    </div>
  );
}
