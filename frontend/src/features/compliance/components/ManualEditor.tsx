import { type FormEvent, useState } from "react";
import { Button } from "../../../components/ui/Button";
import { Notice } from "../../../components/ui/Feedback";
import { errorMessage } from "../../../lib/api-client";
import { DAYS, formatHour } from "../../../lib/time";
import type { AssignmentWrite, ShiftTypeRead, SolveRunRead } from "../../../types/models";
import { useCreateManualEdit } from "../api/compliance";
import "../compliance.css";
import { vi } from "../../../locales/vi";

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
      <p className="muted manual-intro">{vi.compliance.manual.intro(run.id)}</p>
      <div className="table-wrap manual-table">
        <table className="table">
          <caption className="visually-hidden">{vi.compliance.manual.caption(run.id)}</caption>
          <thead>
            <tr>
              <th scope="col">{vi.compliance.manual.employee}</th>
              <th scope="col">{vi.compliance.manual.day}</th>
              <th scope="col">{vi.compliance.manual.shift}</th>
              <th scope="col">{vi.compliance.manual.breakStarts}</th>
              <th scope="col" className="actions">
                <span className="visually-hidden">{vi.compliance.manual.remove}</span>
              </th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row, index) => {
              const shift = shifts.get(row.shift_name);
              const label = vi.compliance.manual.row(index + 1);
              return (
                <tr key={row.key}>
                  <td>
                    <select
                      className="input"
                      aria-label={vi.compliance.manual.employeeAria(label)}
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
                      aria-label={vi.compliance.manual.dayAria(label)}
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
                      aria-label={vi.compliance.manual.shiftAria(label)}
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
                      aria-label={vi.compliance.manual.breakAria(label)}
                      value={row.break_offset ?? ""}
                      onChange={(event) =>
                        update(row.key, {
                          break_offset:
                            event.target.value === "" ? null : Number(event.target.value),
                        })
                      }
                    >
                      <option value="">{vi.compliance.manual.noBreak}</option>
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
                      {vi.compliance.manual.remove}
                      <span className="visually-hidden"> {label}</span>
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
        <Button onClick={addRow}>{vi.compliance.manual.add}</Button>
        <Button onClick={() => setRows(toRows(run))}>{vi.compliance.manual.reset(run.id)}</Button>
        <Button type="submit" variant="primary" disabled={edit.isPending}>
          {edit.isPending ? vi.compliance.manual.checking : vi.compliance.manual.submit}
        </Button>
      </div>
    </form>
  );
}
