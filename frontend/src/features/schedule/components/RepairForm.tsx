import { type FormEvent, useState } from "react";
import { Button } from "../../../components/ui/Button";
import { Notice } from "../../../components/ui/Feedback";
import { Field } from "../../../components/ui/Field";
import { errorMessage } from "../../../lib/api-client";
import { generalError } from "../../../lib/form";
import { DAY_NAMES, DAYS } from "../../../lib/time";
import { vi } from "../../../locales/vi";
import type {
  AbsenceWrite,
  AssignmentRead,
  RepairRequest,
  SolveRunRead,
} from "../../../types/models";
import { useCreateRepair } from "../api/schedules";

type RepairFormProps = {
  run: SolveRunRead;
  onCreated: (runId: number) => void;
};

type AbsenceDraft = { key: number; employeeCode: string; days: number[] };

const REPAIR_GAP_LIMIT = 0.01;
const REPAIR_WORKERS = 8;
const REPAIR_SEED = 0;

function pinKey(item: AssignmentRead): string {
  return `${item.employee_code}|${item.day}|${item.shift_name}`;
}

function toBody(
  run: SolveRunRead,
  fromDay: number,
  absences: AbsenceDraft[],
  pinned: Set<string>,
  timeLimit: string,
): RepairRequest {
  const absenceRows: AbsenceWrite[] = absences
    .filter((item) => item.employeeCode !== "" && item.days.length > 0)
    .map((item) => ({ employee_code: item.employeeCode, days: item.days }));
  const pinnedRows = (run.assignments ?? [])
    .filter((item) => item.day >= fromDay && pinned.has(pinKey(item)))
    .map((item) => ({
      employee_code: item.employee_code,
      day: item.day,
      shift_name: item.shift_name,
    }));
  return {
    from_day: fromDay,
    absences: absenceRows,
    pinned: pinnedRows,
    demand_profile_id: null,
    time_limit_seconds: Number(timeLimit),
    relative_gap_limit: REPAIR_GAP_LIMIT,
    num_workers: REPAIR_WORKERS,
    random_seed: REPAIR_SEED,
    cost_tolerance_percent: run.params.cost_tolerance_percent ?? 0,
  };
}

export function RepairForm({ run, onCreated }: RepairFormProps) {
  const repair = useCreateRepair(run.id);
  const [fromDay, setFromDay] = useState(1);
  const [absences, setAbsences] = useState<AbsenceDraft[]>([]);
  const [nextKey, setNextKey] = useState(0);
  const [pinned, setPinned] = useState<Set<string>>(new Set());
  const [timeLimit, setTimeLimit] = useState("60");
  const general = generalError(repair.error);
  const laterShifts = (run.assignments ?? []).filter((item) => item.day >= fromDay);

  function changeFromDay(day: number) {
    setFromDay(day);
    setAbsences(
      absences.map((item) => ({ ...item, days: item.days.filter((value) => value >= day) })),
    );
  }

  function addAbsence() {
    setAbsences([
      ...absences,
      { key: nextKey, employeeCode: run.employee_codes[0] ?? "", days: [] },
    ]);
    setNextKey(nextKey + 1);
  }

  function updateAbsence(key: number, patch: Partial<AbsenceDraft>) {
    setAbsences(absences.map((item) => (item.key === key ? { ...item, ...patch } : item)));
  }

  function toggleDay(item: AbsenceDraft, day: number) {
    const days = item.days.includes(day)
      ? item.days.filter((value) => value !== day)
      : [...item.days, day];
    updateAbsence(item.key, { days });
  }

  function togglePin(key: string) {
    const next = new Set(pinned);
    if (next.has(key)) {
      next.delete(key);
    } else {
      next.add(key);
    }
    setPinned(next);
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    repair.mutate(toBody(run, fromDay, absences, pinned, timeLimit), {
      onSuccess: (job) => onCreated(job.job_id),
    });
  }

  return (
    <form className="form-stack" onSubmit={handleSubmit} noValidate>
      <p className="muted">{vi.schedule.repair.intro(run.id)}</p>
      <Field
        id="repair-from-day"
        label={vi.schedule.repair.fromDay}
        hint={vi.schedule.repair.fromDayHint}
      >
        {(control) => (
          <select
            {...control}
            className="input"
            value={fromDay}
            onChange={(event) => changeFromDay(Number(event.target.value))}
          >
            {DAY_NAMES.map((name, index) => (
              <option key={name} value={index}>
                {name}
              </option>
            ))}
          </select>
        )}
      </Field>

      <fieldset className="field">
        <legend>{vi.schedule.repair.absences}</legend>
        {absences.map((item, index) => (
          <fieldset key={item.key} className="field">
            <legend>{vi.schedule.repair.absenceRow(index + 1)}</legend>
            <select
              className="input"
              aria-label={vi.schedule.repair.absenceEmployee}
              value={item.employeeCode}
              onChange={(event) => updateAbsence(item.key, { employeeCode: event.target.value })}
            >
              {run.employee_codes.map((code) => (
                <option key={code} value={code}>
                  {code}
                </option>
              ))}
            </select>
            <div className="seg">
              {DAYS.map((label, day) => (
                <label key={label} className="seg-opt">
                  <input
                    type="checkbox"
                    disabled={day < fromDay}
                    checked={item.days.includes(day)}
                    onChange={() => toggleDay(item, day)}
                  />
                  {DAY_NAMES[day]}
                </label>
              ))}
            </div>
            <Button
              size="sm"
              onClick={() => setAbsences(absences.filter((row) => row.key !== item.key))}
            >
              {vi.schedule.repair.removeAbsence}
            </Button>
          </fieldset>
        ))}
        <div>
          <Button size="sm" onClick={addAbsence}>
            {vi.schedule.repair.addAbsence}
          </Button>
        </div>
      </fieldset>

      <fieldset className="field">
        <legend>{vi.schedule.repair.pinned}</legend>
        {laterShifts.length === 0 && <p className="muted">{vi.schedule.repair.pinnedEmpty}</p>}
        <div className="seg">
          {laterShifts.map((item) => (
            <label key={pinKey(item)} className="seg-opt">
              <input
                type="checkbox"
                checked={pinned.has(pinKey(item))}
                onChange={() => togglePin(pinKey(item))}
              />
              {vi.schedule.repair.pinnedItem(
                item.employee_code,
                DAY_NAMES[item.day] ?? "",
                item.shift_name,
              )}
            </label>
          ))}
        </div>
      </fieldset>

      <Field
        id="repair-time-limit"
        label={vi.schedule.repair.timeLimit}
        hint={vi.schedule.repair.timeLimitHint}
      >
        {(control) => (
          <input
            {...control}
            className="input"
            type="number"
            min={0}
            step="any"
            value={timeLimit}
            onChange={(event) => setTimeLimit(event.target.value)}
          />
        )}
      </Field>

      {repair.isError && !general && <Notice kind="error" title={errorMessage(repair.error)} />}
      {general && <Notice kind="error" title={general} />}
      <div className="form-actions">
        <Button type="submit" variant="primary" disabled={repair.isPending}>
          {repair.isPending ? vi.schedule.repair.submitting : vi.schedule.repair.submit}
        </Button>
      </div>
    </form>
  );
}
