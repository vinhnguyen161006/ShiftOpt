import { type FormEvent, useState } from "react";
import {
  initialDraft,
  SOLVE_FIELD_IDS,
  SolveRequestForm,
  toSolveRequest,
} from "../../../components/solve/SolveRequestForm";
import { Button } from "../../../components/ui/Button";
import { ErrorSummary, Notice } from "../../../components/ui/Feedback";
import { errorsByPath, generalError, summaryErrors } from "../../../lib/form";
import type { DemandProfileRead, LaborRulesRead, ShiftTemplateRead } from "../../../types/models";
import { useCreateSchedule } from "../api/schedules";

type NewRunFormProps = {
  profiles: DemandProfileRead[];
  templates: ShiftTemplateRead[];
  employeeCount: number;
  rules: LaborRulesRead;
  onCreated: (runId: number) => void;
};

export function NewRunForm({
  profiles,
  templates,
  employeeCount,
  rules,
  onCreated,
}: NewRunFormProps) {
  const create = useCreateSchedule();
  const [draft, setDraft] = useState(() => ({
    ...initialDraft(rules),
    demandProfileId: profiles[0] ? String(profiles[0].id) : "",
    shiftTemplateIds: templates.map((template) => template.id),
  }));
  const general = generalError(create.error);

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    create.mutate(toSolveRequest(draft), { onSuccess: (job) => onCreated(job.job_id) });
  }

  return (
    <form className="form-stack" onSubmit={handleSubmit} noValidate>
      <ErrorSummary
        errors={summaryErrors(create.error, (path) => SOLVE_FIELD_IDS[path.split(".")[0] ?? ""])}
      />
      <SolveRequestForm
        draft={draft}
        onChange={setDraft}
        profiles={profiles}
        templates={templates}
        employeeCount={employeeCount}
        errors={errorsByPath(create.error)}
      />
      {general && <Notice kind="error" title={general} />}
      <div className="form-actions">
        <Button type="submit" variant="primary" disabled={create.isPending}>
          {create.isPending ? "Submitting..." : "Optimize"}
        </Button>
      </div>
    </form>
  );
}
