import { type FormEvent, useState } from "react";
import { Button } from "../../../components/ui/Button";
import { ErrorSummary, Notice } from "../../../components/ui/Feedback";
import { Field } from "../../../components/ui/Field";
import { errorsByPath, generalError, summaryErrors, toNumber } from "../../../lib/form";
import { formatHour, HOURS, shiftSpan } from "../../../lib/time";
import type { LaborRulesRead, ShiftTemplateRead } from "../../../types/models";
import { useSaveShiftTemplate } from "../api/shift-templates";
import { ShiftStrip } from "./ShiftStrip";

type ShiftTemplateFormProps = {
  template?: ShiftTemplateRead;
  rules: LaborRulesRead | undefined;
  onDone: () => void;
};

const FIELD_IDS: Record<string, string> = {
  name: "template-name",
  start_hour: "template-start",
  length_hours: "template-length",
};

export function ShiftTemplateForm({ template, rules, onDone }: ShiftTemplateFormProps) {
  const save = useSaveShiftTemplate();
  const [name, setName] = useState(template?.name ?? "");
  const [startHour, setStartHour] = useState(template?.start_hour ?? 8);
  const [length, setLength] = useState(String(template?.length_hours ?? 8));
  const lengthHours = toNumber(length);
  const tooLong = rules !== undefined && lengthHours > rules.max_daily_hours;
  const errors = errorsByPath(save.error);
  const general = generalError(save.error);

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    save.mutate(
      { id: template?.id, body: { name, start_hour: startHour, length_hours: lengthHours } },
      { onSuccess: onDone },
    );
  }

  return (
    <form className="form-stack" onSubmit={handleSubmit} noValidate>
      <ErrorSummary errors={summaryErrors(save.error, (path) => FIELD_IDS[path])} />
      <div className="form-grid">
        <Field
          id={FIELD_IDS.name}
          label="Name"
          hint="For example Early, Late or Night."
          error={errors.get("name")}
        >
          {(control) => (
            <input
              {...control}
              className="input"
              value={name}
              maxLength={64}
              onChange={(event) => setName(event.target.value)}
            />
          )}
        </Field>
        <Field id={FIELD_IDS.start_hour} label="Starts at" error={errors.get("start_hour")}>
          {(control) => (
            <select
              {...control}
              className="input"
              value={startHour}
              onChange={(event) => setStartHour(Number(event.target.value))}
            >
              {HOURS.map((hour) => (
                <option key={hour} value={hour}>
                  {formatHour(hour)}
                </option>
              ))}
            </select>
          )}
        </Field>
        <Field
          id={FIELD_IDS.length_hours}
          label="Length (hours)"
          hint={
            rules ? `Normal working time is at most ${rules.max_daily_hours} h a day.` : undefined
          }
          error={errors.get("length_hours")}
        >
          {(control) => (
            <input
              {...control}
              className="input"
              type="number"
              min={1}
              max={24}
              step={1}
              value={length}
              onChange={(event) => setLength(event.target.value)}
            />
          )}
        </Field>
      </div>
      {!Number.isNaN(lengthHours) && lengthHours > 0 && (
        <p className="muted template-preview">
          {shiftSpan(startHour, lengthHours)}
          {rules && (
            <ShiftStrip
              startHour={startHour}
              length={lengthHours}
              nightStart={rules.night_start}
              nightEnd={rules.night_end}
            />
          )}
        </p>
      )}
      {tooLong && rules && (
        <Notice kind="warning" title={`Longer than ${rules.max_daily_hours} hours`}>
          Article 105 limits normal working time to {rules.max_daily_hours} hours a day, so this
          template will be rejected. Split it into two shifts instead.
        </Notice>
      )}
      {general && <Notice kind="error" title={general} />}
      <div className="form-actions">
        <Button onClick={onDone}>Cancel</Button>
        <Button type="submit" variant="primary" disabled={save.isPending || tooLong}>
          {save.isPending ? "Saving..." : template ? "Save template" : "Add template"}
        </Button>
      </div>
    </form>
  );
}
