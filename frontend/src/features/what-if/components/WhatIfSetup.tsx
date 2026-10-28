import { useState } from "react";
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
import type { DemandProfileRead, LaborRulesRead, ShiftTemplateRead } from "../../../types/models";
import { useDemandSweep, useMarginalCost } from "../api/analysis";
import "../what-if.css";

type WhatIfSetupProps = {
  profiles: DemandProfileRead[];
  templates: ShiftTemplateRead[];
  employeeCount: number;
  rules: LaborRulesRead;
  onStarted: (kind: "sweep" | "marginal", runId: number) => void;
};

const MULTIPLIERS = [0.8, 0.9, 1.0, 1.1, 1.2, 1.3];
const PREFIX = "whatif-";

function fieldId(path: string): string | undefined {
  const [head, tail] = path.split(".");
  if (head === "hourly_wage") {
    return `${PREFIX}wage`;
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
  const [draft, setDraft] = useState(() => ({
    ...initialDraft(rules),
    demandProfileId: profiles[0] ? String(profiles[0].id) : "",
    shiftTemplateIds: templates.map((template) => template.id),
    timeLimitSeconds: "20",
    numWorkers: "1",
  }));
  const [wage, setWage] = useState("");
  const error = sweep.error ?? marginal.error;
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
      <Field
        id={`${PREFIX}wage`}
        label="Hourly wage for the marginal cost model (team assumption)"
        hint="The marginal cost and LP dual use the aggregate model, which prices every shift with one hourly wage."
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
      <p className="muted">
        The demand sweep re-solves the full roster at lambda {MULTIPLIERS.join(", ")}, each with the
        time limit above, so it takes up to {MULTIPLIERS.length} times that limit. The marginal cost
        re-solves the aggregate model 169 times.
      </p>
      {general && <Notice kind="error" title={general} />}
      <div className="whatif-actions">
        <Button
          disabled={marginal.isPending}
          onClick={() => {
            sweep.reset();
            marginal.mutate(
              { solve: toSolveRequest(draft), hourly_wage: toNumber(wage) },
              { onSuccess: (job) => onStarted("marginal", job.job_id) },
            );
          }}
        >
          {marginal.isPending ? "Submitting..." : "Run marginal cost by hour"}
        </Button>
        <Button
          variant="primary"
          disabled={sweep.isPending}
          onClick={() => {
            marginal.reset();
            sweep.mutate(
              { solve: toSolveRequest(draft), multipliers: MULTIPLIERS },
              { onSuccess: (job) => onStarted("sweep", job.job_id) },
            );
          }}
        >
          {sweep.isPending ? "Submitting..." : "Run demand sweep"}
        </Button>
      </div>
    </div>
  );
}
