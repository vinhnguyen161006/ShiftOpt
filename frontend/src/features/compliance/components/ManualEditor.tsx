import { type FormEvent, useState } from "react";
import { Button } from "../../../components/ui/Button";
import { Notice } from "../../../components/ui/Feedback";
import { errorMessage } from "../../../lib/api-client";
import { DAYS, formatHour } from "../../../lib/time";
import type { AssignmentWrite, ShiftTypeRead, SolveRunRead } from "../../../types/models";
import { useCreateManualEdit } from "../api/compliance";
import "../compliance.css";

type ManualEditorProps = {
  run: SolveRunRead;
  onCreated: (runId: number) => void;
};

type Row = AssignmentWrite & { key: number };

function toRows(run: SolveRunRead): Row[] {
  return (run.assignments ?? []).map((assignment, index) => ({
    key: index,
    employee_code: assignment.employee_code,
    day: assignment.day,
    shift_name: assignment.shift_name,
    break_offset: assignment.break_offset ?? null,
  }));
}

function breakOptions(shift: ShiftTypeRead | undefined): number[] {
  return shift ? Array.from({ length: shift.length }, (_, offset) => offset) : [];
}

export function ManualEditor({ run, onCreated }: ManualEditorProps) {
  const edit = useCreateManualEdit(run.id);
  const [rows, setRows] = useState(() => toRows(run));
  const [nextKey, setNextKey] = useState(rows.length);
  const shifts = new Map(run.shift_types.map((shift) => [shift.name, shift]));

  function update(key: number, patch: Partial<AssignmentWrite>) {
    setRows(rows.map((row) => (row.key === key ? { ...row, ...patch } : row)));
  }

  function addRow() {
    const shift = run.shift_types[0];
    setRows([
      ...rows,
      {
        key: nextKey,
        employee_code: run.employee_codes[0] ?? "",
        day: 0,
        shift_name: shift?.name ?? "",
        break_offset: null,
      },
    ]);
    setNextKey(nextKey + 1);
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    edit.mutate(
      { assignments: rows.map(({ key: _key, ...assignment }) => assignment) },
      { onSuccess: (created) => onCreated(created.id) },
    );
  }

  return (
    <form className="form-stack" onSubmit={handleSubmit}>
      <p className="muted manual-intro">
        Change, add or remove assignments, then re-check. Run {run.id} stays as it is: the edited
        schedule becomes a new run and the validator checks it again.
      </p>
      <div className="table-wrap manual-table">
        <table className="table">
          <caption className="visually-hidden">Assignments of run {run.id}</caption>
          <thead>
            <tr>
              <th scope="col">Employee</th>
              <th scope="col">Day</th>
              <th scope="col">Shift</th>
              <th scope="col">Break starts</th>
              <th scope="col" className="actions">
                <span className="visually-hidden">Remove</span>
              </th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row, index) => {
              const shift = shifts.get(row.shift_name);
              const label = `row ${index + 1}`;
              return (
                <tr key={row.key}>
                  <td>
                    <select
                      className="input"
                      aria-label={`Employee, ${label}`}
                      value={row.employee_code}
                      onChange={(event) => update(row.key, { employee_code: event.target.value })}
                    >
                      {run.employee_codes.map((code) => (
                        <option key={code} value={code}>
                          {code}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td>
                    <select
                      className="input"
                      aria-label={`Day, ${label}`}
                      value={row.day}
                      onChange={(event) => update(row.key, { day: Number(event.target.value) })}
                    >
                      {DAYS.map((day, dayIndex) => (
                        <option key={day} value={dayIndex}>
                          {day}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td>
                    <select
                      className="input"
                      aria-label={`Shift, ${label}`}
                      value={row.shift_name}
                      onChange={(event) =>
                        update(row.key, { shift_name: event.target.value, break_offset: null })
                      }
                    >
                      {run.shift_types.map((option) => (
                        <option key={option.name} value={option.name}>
                          {option.name}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td>
                    <select
                      className="input"
                      aria-label={`Break start, ${label}`}
                      value={row.break_offset ?? ""}
                      onChange={(event) =>
                        update(row.key, {
                          break_offset:
                            event.target.value === "" ? null : Number(event.target.value),
                        })
                      }
                    >
                      <option value="">No break</option>
                      {breakOptions(shift).map((offset) => (
                        <option key={offset} value={offset}>
                          {formatHour((shift?.start_hour ?? 0) + offset)}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td className="actions">
                    <Button
                      size="sm"
                      onClick={() => setRows(rows.filter((item) => item.key !== row.key))}
                    >
                      Remove<span className="visually-hidden"> {label}</span>
                    </Button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      {edit.isError && <Notice kind="error" title={errorMessage(edit.error)} />}
      <div className="form-actions">
        <Button onClick={addRow}>Add assignment</Button>
        <Button onClick={() => setRows(toRows(run))}>Reset to run {run.id}</Button>
        <Button type="submit" variant="primary" disabled={edit.isPending}>
          {edit.isPending ? "Checking..." : "Save as new run and re-check"}
        </Button>
      </div>
    </form>
  );
}
