import { useState } from "react";
import { PreSolveWarnings } from "../../../components/solve/PreSolveWarnings";
import {
  initialDraft,
  SOLVE_FIELD_IDS,
  SolveRequestForm,
  toSolveRequest,
} from "../../../components/solve/SolveRequestForm";
import { Button } from "../../../components/ui/Button";
import { ErrorSummary, Notice } from "../../../components/ui/Feedback";
import { Field } from "../../../components/ui/Field";
import { errorsByPath, generalError, summaryErrors, toNumber } from "../../../lib/form";
import type {
  DemandProfileRead,
  LaborRulesRead,
  ShiftTemplateRead,
  StaffingSweepRequest,
} from "../../../types/models";
import { useDemandSweep, useMarginalCost, useStaffingSweep } from "../api/analysis";
import "../what-if.css";
import { vi } from "../../../locales/vi";

export type AnalysisKind = "sweep" | "marginal" | "staffing";

type WhatIfSetupProps = {
  profiles: DemandProfileRead[];
  templates: ShiftTemplateRead[];
  employeeCount: number;
  rules: LaborRulesRead;
  onStarted: (kind: AnalysisKind, runId: number) => void;
};

type StaffingField = StaffingSweepRequest["assumption"];

const MULTIPLIERS = [0.8, 0.9, 1.0, 1.1, 1.2, 1.3];
const PREFIX = "whatif-";
const DEFAULT_HOURLY_WAGE = 35000;

function parseValues(text: string): number[] {
  return text
    .split(",")
    .map((part) => part.trim())
    .filter((part) => part !== "")
    .map(Number);
}

function fieldId(path: string): string | undefined {
  const [head, tail] = path.split(".");
  if (head === "hourly_wage") {
    return `${PREFIX}wage`;
  }
  if (head === "assumption" || head === "values") {
    return `${PREFIX}${head === "values" ? "staffing-values" : "assumption"}`;
  }
  const id = head === "solve" && tail ? SOLVE_FIELD_IDS[tail] : undefined;
  return id ? `${PREFIX}${id}` : undefined;
}

function solveErrors(error: unknown): Map<string, string> {
  const nested = new Map<string, string>();
  for (const [path, message] of errorsByPath(error)) {
    if (path.startsWith("solve.")) {
      nested.set(path.slice("solve.".length), message);
    }
  }
  return nested;
}

export function WhatIfSetup({
  profiles,
  templates,
  employeeCount,
  rules,
  onStarted,
}: WhatIfSetupProps) {
  const sweep = useDemandSweep();
  const marginal = useMarginalCost();
  const staffing = useStaffingSweep();
  const [draft, setDraft] = useState(() => ({
    ...initialDraft(rules),
    demandProfileId: profiles[0] ? String(profiles[0].id) : "",
    shiftTemplateIds: templates.map((template) => template.id),
    timeLimitSeconds: "20",
    numWorkers: "1",
  }));
  const [wage, setWage] = useState(String(DEFAULT_HOURLY_WAGE));
  const [assumption, setAssumption] = useState<StaffingField>("alpha");
  const [valuesText, setValuesText] = useState("0.8, 1.0, 1.2");
  const selectedProfile = profiles.find((profile) => String(profile.id) === draft.demandProfileId);
  const canSweepAssumption = selectedProfile?.has_sales_load === true;
  const error = sweep.error ?? marginal.error ?? staffing.error;
  const general = generalError(error);

  return (
    <div className="form-stack">
      <ErrorSummary errors={summaryErrors(error, fieldId)} />
      <SolveRequestForm
        draft={draft}
        onChange={setDraft}
        profiles={profiles}
        templates={templates}
        employeeCount={employeeCount}
        errors={solveErrors(error)}
        prefix={PREFIX}
      />
      <PreSolveWarnings
        body={
          draft.demandProfileId !== "" && draft.shiftTemplateIds.length > 0
            ? toSolveRequest(draft)
            : null
        }
      />
      {general && <Notice kind="error" title={general} />}
      <section className="whatif-group" aria-labelledby={`${PREFIX}sweep-group`}>
        <h3 id={`${PREFIX}sweep-group`} className="whatif-group-title">
          {vi.whatIf.form.sweepGroup}
        </h3>
        <p className="muted">{vi.whatIf.form.note(MULTIPLIERS.join("; "), MULTIPLIERS.length)}</p>
        <div className="whatif-actions">
          <Button
            variant="primary"
            disabled={sweep.isPending}
            onClick={() => {
              marginal.reset();
              staffing.reset();
              sweep.mutate(
                { solve: toSolveRequest(draft), multipliers: MULTIPLIERS },
                { onSuccess: (job) => onStarted("sweep", job.job_id) },
              );
            }}
          >
            {sweep.isPending ? vi.whatIf.form.submitting : vi.whatIf.form.runSweep}
          </Button>
        </div>
      </section>
      <section className="whatif-group" aria-labelledby={`${PREFIX}marginal-group`}>
        <h3 id={`${PREFIX}marginal-group`} className="whatif-group-title">
          {vi.whatIf.form.marginalGroup}
        </h3>
        <p className="muted">{vi.whatIf.form.marginalNote}</p>
        <Field
          id={`${PREFIX}wage`}
          label={vi.whatIf.form.wage}
          hint={vi.whatIf.form.wageHint}
          error={errorsByPath(error).get("hourly_wage")}
        >
          {(control) => (
            <input
              {...control}
              className="input"
              type="number"
              min={1}
              step={1}
              value={wage}
              onChange={(event) => setWage(event.target.value)}
            />
          )}
        </Field>
        <div className="whatif-actions">
          <Button
            disabled={marginal.isPending}
            onClick={() => {
              sweep.reset();
              staffing.reset();
              marginal.mutate(
                { solve: toSolveRequest(draft), hourly_wage: toNumber(wage) },
                { onSuccess: (job) => onStarted("marginal", job.job_id) },
              );
            }}
          >
            {marginal.isPending ? vi.whatIf.form.submitting : vi.whatIf.form.runMarginal}
          </Button>
        </div>
      </section>
      <section className="whatif-group" aria-labelledby={`${PREFIX}staffing-group`}>
        <h3 id={`${PREFIX}staffing-group`} className="whatif-group-title">
          {vi.whatIf.form.staffingGroup}
        </h3>
        <div className="form-grid">
          <Field
            id={`${PREFIX}assumption`}
            label={vi.whatIf.form.assumption}
            hint={vi.whatIf.form.assumptionHint}
          >
            {(control) => (
              <select
                {...control}
                className="input"
                value={assumption}
                onChange={(event) => setAssumption(event.target.value as StaffingField)}
              >
                <option value="alpha">{vi.whatIf.form.options.alpha}</option>
                <option value="productivity">{vi.whatIf.form.options.productivity}</option>
                <option value="min_staff">{vi.whatIf.form.options.min_staff}</option>
                <option value="night_min_staff">{vi.whatIf.form.options.night_min_staff}</option>
              </select>
            )}
          </Field>
          <Field
            id={`${PREFIX}staffing-values`}
            label={vi.whatIf.form.values}
            hint={vi.whatIf.form.valuesHint}
          >
            {(control) => (
              <input
                {...control}
                className="input"
                value={valuesText}
                onChange={(event) => setValuesText(event.target.value)}
              />
            )}
          </Field>
        </div>
        {!canSweepAssumption && <p className="muted">{vi.whatIf.form.onlySales}</p>}
        <div className="whatif-actions">
          <Button
            disabled={staffing.isPending || !canSweepAssumption}
            onClick={() => {
              sweep.reset();
              marginal.reset();
              staffing.mutate(
                {
                  solve: toSolveRequest(draft),
                  assumption,
                  values: parseValues(valuesText),
                },
                { onSuccess: (job) => onStarted("staffing", job.job_id) },
              );
            }}
          >
            {staffing.isPending ? vi.whatIf.form.submitting : vi.whatIf.form.runStaffing}
          </Button>
        </div>
      </section>
    </div>
  );
}
