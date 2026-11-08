import { useState } from "react";
import { Button } from "../../../components/ui/Button";
import { Notice } from "../../../components/ui/Feedback";
import { Field } from "../../../components/ui/Field";
import { errorMessage } from "../../../lib/api-client";
import { formatDecimal } from "../../../lib/number";
import { DAY_NAMES } from "../../../lib/time";
import { vi } from "../../../locales/vi";
import type { AssignmentRead, ReplacementRead, SolveRunRead } from "../../../types/models";
import { useCreateManualEdit, useReplacements } from "../api/compliance";

type ReplacementListProps = {
  run: SolveRunRead;
  onCreated: (runId: number) => void;
};

const COST_SCALE = 100;

function cellKey(item: AssignmentRead): string {
  return `${item.employee_code}|${item.day}`;
}

function applied(
  assignments: AssignmentRead[],
  absent: AssignmentRead,
  candidate: ReplacementRead,
): { employee_code: string; day: number; shift_name: string; break_offset: number | null }[] {
  const kept = assignments.filter((item) => cellKey(item) !== cellKey(absent));
  return [
    ...kept,
    {
      ...absent,
      employee_code: candidate.employee_code,
      shift_name: candidate.shift_name,
      break_offset: candidate.break_offset,
    },
  ].map((item) => ({
    employee_code: item.employee_code,
    day: item.day,
    shift_name: item.shift_name,
    break_offset: item.break_offset ?? null,
  }));
}

export function ReplacementList({ run, onCreated }: ReplacementListProps) {
  const assignments = run.assignments ?? [];
  const [selected, setSelected] = useState(assignments[0] ? cellKey(assignments[0]) : "");
  const absent = assignments.find((item) => cellKey(item) === selected);
  const candidates = useReplacements(run.id, absent?.employee_code ?? "", absent?.day ?? null);
  const edit = useCreateManualEdit(run.id);

  function apply(candidate: ReplacementRead) {
    if (!absent) {
      return;
    }
    edit.mutate(
      { assignments: applied(assignments, absent, candidate) },
      { onSuccess: (created) => onCreated(created.id) },
    );
  }

  return (
    <div className="form-stack">
      <p className="muted">{vi.compliance.replacement.intro}</p>
      {assignments.length === 0 ? (
        <p className="muted">{vi.compliance.replacement.noShift}</p>
      ) : (
        <Field id="replacement-cell" label={vi.compliance.replacement.employee}>
          {(control) => (
            <select
              {...control}
              className="input"
              value={selected}
              onChange={(event) => setSelected(event.target.value)}
            >
              {assignments.map((item) => (
                <option key={cellKey(item)} value={cellKey(item)}>
                  {vi.compliance.replacement.option(
                    item.employee_code,
                    DAY_NAMES[item.day] ?? "",
                    item.shift_name,
                  )}
                </option>
              ))}
            </select>
          )}
        </Field>
      )}
      {absent && candidates.isPending && (
        <Notice kind="info" title={vi.compliance.replacement.loading} />
      )}
      {candidates.isError && <Notice kind="error" title={errorMessage(candidates.error)} />}
      {edit.isError && <Notice kind="error" title={errorMessage(edit.error)} />}
      {candidates.data && candidates.data.length === 0 && (
        <p className="muted">{vi.compliance.replacement.empty}</p>
      )}
      {candidates.data && candidates.data.length > 0 && absent && (
        <div className="table-wrap">
          <table className="table">
            <caption className="visually-hidden">
              {vi.compliance.replacement.caption(absent.employee_code, DAY_NAMES[absent.day] ?? "")}
            </caption>
            <thead>
              <tr>
                <th scope="col">{vi.compliance.replacement.candidate}</th>
                <th scope="col">{vi.compliance.replacement.shift}</th>
                <th scope="col">{vi.compliance.replacement.extraCost}</th>
                <th scope="col">{vi.compliance.replacement.weeklyHours}</th>
                <th scope="col" className="actions">
                  <span className="visually-hidden">{vi.compliance.replacement.apply}</span>
                </th>
              </tr>
            </thead>
            <tbody>
              {candidates.data.map((item) => (
                <tr key={item.employee_code}>
                  <th scope="row">
                    {item.employee_code}
                    {item.prefers_off && (
                      <span className="tag-outline">{vi.compliance.replacement.prefersOff}</span>
                    )}
                  </th>
                  <td>
                    {item.shift_name}
                    {item.break_offset !== null &&
                      item.break_offset !== undefined &&
                      vi.compliance.replacement.breakOffset(item.break_offset)}
                  </td>
                  <td>{formatDecimal(item.extra_cost / COST_SCALE, 2)}</td>
                  <td>{item.weekly_hours}</td>
                  <td className="actions">
                    <Button size="sm" disabled={edit.isPending} onClick={() => apply(item)}>
                      {edit.isPending
                        ? vi.compliance.replacement.applying
                        : vi.compliance.replacement.apply}
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
