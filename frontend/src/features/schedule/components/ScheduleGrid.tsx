import { DAY_NAMES, DAYS, formatHour, shiftSpan } from "../../../lib/time";
import type { AssignmentRead, ShiftTypeRead, SolveRunRead } from "../../../types/models";
import "../schedule.css";
import { vi } from "../../../locales/vi";

type ScheduleGridProps = {
  run: SolveRunRead;
};

type ShiftLook = { background: string; color: string; border: string };

const SHIFT_LOOKS: ShiftLook[] = [
  ["--color-accent-200", "--color-accent-900", "--color-accent-300"],
  ["--color-accent-400", "--color-accent-900", "--color-accent-500"],
  ["--color-accent-600", "--color-neutral-100", "--color-accent-700"],
  ["--color-accent-900", "--color-neutral-200", "--color-accent-900"],
  ["--color-accent-300", "--color-accent-900", "--color-accent-400"],
  ["--color-accent-700", "--color-neutral-100", "--color-accent-800"],
  ["--color-accent-100", "--color-accent-900", "--color-accent-300"],
  ["--color-accent-800", "--color-neutral-100", "--color-accent-900"],
].map(([background, color, border]) => ({
  background: `var(${background})`,
  color: `var(${color})`,
  border: `1px solid var(${border})`,
}));

const EXTRA_LOOK: ShiftLook = {
  background: "var(--color-neutral-200)",
  color: "var(--color-text)",
  border: "1px solid var(--color-divider)",
};

export function shiftLook(shiftTypes: ShiftTypeRead[], name: string): ShiftLook {
  const index = shiftTypes.findIndex((shift) => shift.name === name);
  return SHIFT_LOOKS[index] ?? EXTRA_LOOK;
}

export function shiftLabels(shiftTypes: ShiftTypeRead[]): Map<string, string> {
  const labels = new Map<string, string>();
  const used = new Set<string>();
  for (const shift of shiftTypes) {
    const upper = shift.name.toUpperCase();
    let length = 1;
    while (length < upper.length && used.has(upper.slice(0, length))) {
      length += 1;
    }
    const label = upper.slice(0, length);
    used.add(label);
    labels.set(shift.name, label);
  }
  return labels;
}

function breakHour(shift: ShiftTypeRead | undefined, assignment: AssignmentRead): string | null {
  return shift && assignment.break_offset !== null && assignment.break_offset !== undefined
    ? formatHour(shift.start_hour + assignment.break_offset)
    : null;
}

function cellTitle(
  day: number,
  shift: ShiftTypeRead | undefined,
  assignment: AssignmentRead,
  changed: boolean,
) {
  const span = shift ? ` ${shiftSpan(shift.start_hour, shift.length)}` : "";
  const hour = breakHour(shift, assignment);
  const rest = hour ? vi.schedule.grid.breakAt(hour) : "";
  const diff = changed ? `, ${vi.schedule.grid.changed}` : "";
  return `${DAY_NAMES[day]}: ${assignment.shift_name}${span}${rest}${diff}`;
}

export function ScheduleGrid({ run }: ScheduleGridProps) {
  const byCell = new Map(
    (run.assignments ?? []).map((assignment) => [
      `${assignment.employee_code}|${assignment.day}`,
      assignment,
    ]),
  );
  const baselineCells = new Map(
    (run.baseline_assignments ?? []).map((assignment) => [
      `${assignment.employee_code}|${assignment.day}`,
      assignment,
    ]),
  );
  const repairing = run.baseline_assignments !== null && run.baseline_assignments !== undefined;
  const lockedBefore = run.repair_from_day ?? 0;
  const shiftsByName = new Map(run.shift_types.map((shift) => [shift.name, shift]));
  const labels = shiftLabels(run.shift_types);
  const shiftCount = (code: string) => DAYS.filter((_, day) => byCell.has(`${code}|${day}`)).length;
  const changedAt = (code: string, day: number) =>
    repairing &&
    baselineCells.get(`${code}|${day}`)?.shift_name !== byCell.get(`${code}|${day}`)?.shift_name;

  return (
    <div className="roster">
      <div className="roster-scroll">
        <table className="roster-grid">
          <caption className="visually-hidden">{vi.schedule.grid.caption}</caption>
          <thead>
            <tr>
              <th scope="col">{vi.schedule.grid.employee}</th>
              {DAYS.map((day, index) => (
                <th key={day} scope="col" title={DAY_NAMES[index]}>
                  {day}
                  {index < lockedBefore && (
                    <span
                      className="roster-lock"
                      title={vi.schedule.grid.lockedTitle(DAY_NAMES[index] ?? "")}
                    >
                      {vi.schedule.grid.locked}
                    </span>
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {run.employee_codes.map((code) => (
              <tr key={code}>
                <th scope="row">
                  <span className="roster-name">{code}</span>
                  <span className="roster-sub">{vi.schedule.grid.shifts(shiftCount(code))}</span>
                </th>
                {DAYS.map((day, dayIndex) => {
                  const assignment = byCell.get(`${code}|${dayIndex}`);
                  const changed = changedAt(code, dayIndex);
                  const changedClass = changed ? " roster-cell-changed" : "";
                  if (!assignment) {
                    return (
                      <td key={day}>
                        <span
                          className={`roster-cell roster-off${changedClass}`}
                          title={vi.schedule.grid.offTitle(DAY_NAMES[dayIndex] ?? "")}
                        >
                          <span className="visually-hidden">
                            {vi.schedule.grid.off}
                            {changed ? `, ${vi.schedule.grid.changed}` : ""}
                          </span>
                          {changed && (
                            <span className="roster-changed-mark" aria-hidden="true">
                              {vi.schedule.grid.changedMark}
                            </span>
                          )}
                        </span>
                      </td>
                    );
                  }
                  const shift = shiftsByName.get(assignment.shift_name);
                  const rest = breakHour(shift, assignment);
                  return (
                    <td key={day}>
                      <span
                        className={`roster-cell${changedClass}`}
                        style={shiftLook(run.shift_types, assignment.shift_name)}
                        title={cellTitle(dayIndex, shift, assignment, changed)}
                      >
                        {labels.get(assignment.shift_name) ?? assignment.shift_name}
                        {changed && (
                          <span className="roster-changed-mark" aria-hidden="true">
                            {vi.schedule.grid.changedMark}
                          </span>
                        )}
                        {rest && (
                          <span className="roster-break">{vi.schedule.grid.breakShort(rest)}</span>
                        )}
                      </span>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="legend roster-legend">
        {run.shift_types.map((shift) => {
          const look = shiftLook(run.shift_types, shift.name);
          return (
            <span key={shift.name} className="legend-item">
              <span
                className="swatch"
                style={{ background: look.background, border: look.border }}
              />
              {shift.name} {shiftSpan(shift.start_hour, shift.length)}
            </span>
          );
        })}
        <span className="legend-item">
          <span className="swatch roster-off" />
          {vi.schedule.grid.off}
        </span>
        <span className="legend-item">{vi.schedule.grid.breakLegend}</span>
        {repairing && (
          <span className="legend-item">
            <span className="swatch roster-cell-changed" />
            {vi.schedule.grid.changed}
          </span>
        )}
      </div>
    </div>
  );
}
