import { type FormEvent, useState } from "react";
import { Button } from "../../../components/ui/Button";
import { DayPicker } from "../../../components/ui/DayPicker";
import { ErrorSummary, Notice } from "../../../components/ui/Feedback";
import { Field } from "../../../components/ui/Field";
import { errorsByPath, generalError, summaryErrors, toNumber } from "../../../lib/form";
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
  unavailable_days: "employee-unavailable",
  preferred_days_off: "employee-preferred",
};

export function EmployeeForm({ employee, onDone }: EmployeeFormProps) {
  const save = useSaveEmployee();
  const [code, setCode] = useState(employee?.code ?? "");
  const [name, setName] = useState(employee?.name ?? "");
  const [wage, setWage] = useState(employee ? String(employee.hourly_wage) : "");
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
          label="Code"
          hint="Unique, shown on the roster."
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
        <Field id={FIELD_IDS.name} label="Name" error={errors.get("name")}>
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
          label="Hourly wage"
          hint="Whole units of your wage currency."
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
      </div>
      <DayPicker
        id={FIELD_IDS.unavailable_days}
        legend="Cannot work on"
        hint="Hard rule: the solver never assigns a shift on these days."
        error={errors.get("unavailable_days")}
        value={unavailable}
        onChange={setUnavailable}
      />
      <DayPicker
        id={FIELD_IDS.preferred_days_off}
        legend="Would like off"
        hint="Soft request: honored when it does not cost coverage, labor cost or fairness."
        error={errors.get("preferred_days_off")}
        value={preferred}
        onChange={setPreferred}
      />
      {general && <Notice kind="error" title={general} />}
      <div className="form-actions">
        <Button onClick={onDone}>Cancel</Button>
        <Button type="submit" variant="primary" disabled={save.isPending}>
          {save.isPending ? "Saving..." : employee ? "Save employee" : "Add employee"}
        </Button>
      </div>
    </form>
  );
}
