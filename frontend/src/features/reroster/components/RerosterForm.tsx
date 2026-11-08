import { type FormEvent, useState } from "react";
import { Button } from "../../../components/ui/Button";
import { DayPicker } from "../../../components/ui/DayPicker";
import { Notice } from "../../../components/ui/Feedback";
import { Field } from "../../../components/ui/Field";
import { errorMessage } from "../../../lib/api-client";
import { DAY_NAMES, DAYS } from "../../../lib/time";
import { vi } from "../../../locales/vi";
import type { SolveRunRead } from "../../../types/models";
import { useCreateReroster } from "../api/reroster";

type RerosterFormProps = {
  run: SolveRunRead;
  onCreated: (runId: number) => void;
};

export function RerosterForm({ run, onCreated }: RerosterFormProps) {
  const reroster = useCreateReroster(run.id);
  const [employee, setEmployee] = useState(run.employee_codes[0] ?? "");
  const [absentDays, setAbsentDays] = useState<number[]>([]);
  const [fromDay, setFromDay] = useState<number | null>(null);
  const [dayError, setDayError] = useState<string | undefined>();

  const fromLimit = absentDays[0] ?? DAYS.length - 1;
  const chosenFrom = fromDay !== null && fromDay <= fromLimit ? fromDay : null;

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (absentDays.length === 0) {
      setDayError(vi.schedule.reroster.needDay);
      return;
    }
    setDayError(undefined);
    reroster.mutate(
      { employee_code: employee, absent_days: absentDays, from_day: chosenFrom },
      { onSuccess: (accepted) => onCreated(accepted.job_id) },
    );
  }

  return (
    <form className="form-stack" onSubmit={handleSubmit}>
      <Field id="reroster-employee" label={vi.schedule.reroster.employee}>
        {(control) => (
          <select
            {...control}
            className="input"
            value={employee}
            onChange={(event) => setEmployee(event.target.value)}
          >
            {run.employee_codes.map((code) => (
              <option key={code} value={code}>
                {code}
              </option>
            ))}
          </select>
        )}
      </Field>
      <DayPicker
        id="reroster-days"
        legend={vi.schedule.reroster.absentDays}
        hint={vi.schedule.reroster.absentHint}
        error={dayError}
        value={absentDays}
        onChange={setAbsentDays}
      />
      <Field
        id="reroster-from"
        label={vi.schedule.reroster.fromDay}
        hint={vi.schedule.reroster.fromDayHint}
      >
        {(control) => (
          <select
            {...control}
            className="input"
            value={chosenFrom ?? ""}
            onChange={(event) =>
              setFromDay(event.target.value === "" ? null : Number(event.target.value))
            }
          >
            <option value="">{vi.schedule.reroster.fromDayDefault}</option>
            {DAY_NAMES.slice(0, fromLimit + 1).map((name, index) => (
              <option key={name} value={index}>
                {name}
              </option>
            ))}
          </select>
        )}
      </Field>
      {reroster.isError && <Notice kind="error" title={errorMessage(reroster.error)} />}
      <div className="form-actions">
        <Button type="submit" variant="primary" disabled={reroster.isPending}>
          {reroster.isPending ? vi.schedule.reroster.submitting : vi.schedule.reroster.submit}
        </Button>
      </div>
    </form>
  );
}
