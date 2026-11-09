import { type FormEvent, useState } from "react";
import { Button } from "../../../components/ui/Button";
import { DayPicker } from "../../../components/ui/DayPicker";
import { ErrorSummary, Notice } from "../../../components/ui/Feedback";
import { Field } from "../../../components/ui/Field";
import { errorsByPath, generalError, summaryErrors, toNumber } from "../../../lib/form";
import { vi } from "../../../locales/vi";
import type { EmployeeRead } from "../../../types/models";
import { useSaveEmployee } from "../api/employees";

type EmployeeFormProps = {
  employee?: EmployeeRead;
  onDone: () => void;
};

const FIELD_IDS: Record<string, string> = {
  code: "employee-code",
  name: "employee-name",
  hourly_wage: "employee-wage",
  max_weekly_hours: "employee-max-hours",
  min_weekly_hours: "employee-min-hours",
  unavailable_days: "employee-unavailable",
  preferred_days_off: "employee-preferred",
};

export function EmployeeForm({ employee, onDone }: EmployeeFormProps) {
  const save = useSaveEmployee();
  const [code, setCode] = useState(employee?.code ?? "");
  const [name, setName] = useState(employee?.name ?? "");
  const [wage, setWage] = useState(employee ? String(employee.hourly_wage) : "");
  const [maxHours, setMaxHours] = useState(
    employee?.max_weekly_hours == null ? "" : String(employee.max_weekly_hours),
  );
  const [minHours, setMinHours] = useState(
    employee?.min_weekly_hours == null ? "" : String(employee.min_weekly_hours),
  );
  const [unavailable, setUnavailable] = useState(employee?.unavailable_days ?? []);
  const [preferred, setPreferred] = useState(employee?.preferred_days_off ?? []);
  const errors = errorsByPath(save.error);
  const general = generalError(save.error);

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    save.mutate(
      {
        id: employee?.id,
        body: {
          code,
          name,
          hourly_wage: toNumber(wage),
          max_weekly_hours: maxHours.trim() === "" ? null : toNumber(maxHours),
          min_weekly_hours: minHours.trim() === "" ? null : toNumber(minHours),
          unavailable_days: unavailable,
          preferred_days_off: preferred,
        },
      },
      { onSuccess: onDone },
    );
  }

  return (
    <form className="form-stack" onSubmit={handleSubmit} noValidate>
      <ErrorSummary
        errors={summaryErrors(save.error, (path) => FIELD_IDS[path.split(".")[0] ?? ""])}
      />
      <div className="form-grid">
        <Field
          id={FIELD_IDS.code}
          label={vi.employees.form.code}
          hint={vi.employees.form.codeHint}
          error={errors.get("code")}
        >
          {(control) => (
            <input
              {...control}
              className="input"
              value={code}
              maxLength={32}
              autoComplete="off"
              onChange={(event) => setCode(event.target.value)}
            />
          )}
        </Field>
        <Field id={FIELD_IDS.name} label={vi.employees.form.name} error={errors.get("name")}>
          {(control) => (
            <input
              {...control}
              className="input"
              value={name}
              maxLength={120}
              onChange={(event) => setName(event.target.value)}
            />
          )}
        </Field>
        <Field
          id={FIELD_IDS.hourly_wage}
          label={vi.employees.form.wage}
          hint={vi.employees.form.wageHint}
          error={errors.get("hourly_wage")}
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
        <Field
          id={FIELD_IDS.max_weekly_hours}
          label={vi.employees.form.maxHours}
          hint={vi.employees.form.maxHoursHint}
          error={errors.get("max_weekly_hours")}
        >
          {(control) => (
            <input
              {...control}
              className="input"
              type="number"
              min={1}
              max={48}
              step={1}
              value={maxHours}
              onChange={(event) => setMaxHours(event.target.value)}
            />
          )}
        </Field>
        <Field
          id={FIELD_IDS.min_weekly_hours}
          label={vi.employees.form.minHours}
          hint={vi.employees.form.minHoursHint}
          error={errors.get("min_weekly_hours")}
        >
          {(control) => (
            <input
              {...control}
              className="input"
              type="number"
              min={1}
              max={48}
              step={1}
              value={minHours}
              onChange={(event) => setMinHours(event.target.value)}
            />
          )}
        </Field>
      </div>
      <DayPicker
        id={FIELD_IDS.unavailable_days}
        legend={vi.employees.form.cannotWork}
        hint={vi.employees.form.cannotWorkHint}
        error={errors.get("unavailable_days")}
        value={unavailable}
        onChange={setUnavailable}
      />
      <DayPicker
        id={FIELD_IDS.preferred_days_off}
        legend={vi.employees.form.wouldLikeOff}
        hint={vi.employees.form.wouldLikeOffHint}
        error={errors.get("preferred_days_off")}
        value={preferred}
        onChange={setPreferred}
      />
      {general && <Notice kind="error" title={general} />}
      <div className="form-actions">
        <Button onClick={onDone}>{vi.common.cancel}</Button>
        <Button type="submit" variant="primary" disabled={save.isPending}>
          {save.isPending
            ? vi.common.saving
            : employee
              ? vi.employees.form.save
              : vi.employees.form.add}
        </Button>
      </div>
    </form>
  );
}
