import { DAY_NAMES, DAYS, formatHour, shiftSpan } from "../../../lib/time";
import type { AssignmentRead, ShiftTypeRead, SolveRunRead } from "../../../types/models";
import "../schedule.css";

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

function cellTitle(day: number, shift: ShiftTypeRead | undefined, assignment: AssignmentRead) {
  const span = shift ? ` ${shiftSpan(shift.start_hour, shift.length)}` : "";
  const rest =
    shift && assignment.break_offset !== null && assignment.break_offset !== undefined
      ? `, break at ${formatHour(shift.start_hour + assignment.break_offset)}`
      : "";
  return `${DAY_NAMES[day]}: ${assignment.shift_name}${span}${rest}`;
}

export function ScheduleGrid({ run }: ScheduleGridProps) {
  const byCell = new Map(
    (run.assignments ?? []).map((assignment) => [
      `${assignment.employee_code}|${assignment.day}`,
      assignment,
    ]),
  );
  const shiftsByName = new Map(run.shift_types.map((shift) => [shift.name, shift]));
  const shiftCount = (code: string) => DAYS.filter((_, day) => byCell.has(`${code}|${day}`)).length;

  return (
    <div className="roster">
      <div className="roster-scroll">
        <table className="roster-grid">
          <caption className="visually-hidden">
            Weekly roster: one row per employee, one column per day
          </caption>
          <thead>
            <tr>
              <th scope="col">Employee</th>
              {DAYS.map((day, index) => (
                <th key={day} scope="col" title={DAY_NAMES[index]}>
                  {day}
                </th>
              ))}
              <th scope="col" className="num">
                Shifts
              </th>
            </tr>
          </thead>
          <tbody>
            {run.employee_codes.map((code) => (
              <tr key={code}>
                <th scope="row">{code}</th>
                {DAYS.map((day, dayIndex) => {
                  const assignment = byCell.get(`${code}|${dayIndex}`);
                  if (!assignment) {
                    return (
                      <td key={day}>
                        <span
                          className="roster-cell roster-off"
                          title={`${DAY_NAMES[dayIndex]}: off`}
                        >
                          <span className="visually-hidden">Off</span>
                        </span>
                      </td>
                    );
                  }
                  return (
                    <td key={day}>
                      <span
                        className="roster-cell"
                        style={shiftLook(run.shift_types, assignment.shift_name)}
                        title={cellTitle(
                          dayIndex,
                          shiftsByName.get(assignment.shift_name),
                          assignment,
                        )}
                      >
                        {assignment.shift_name}
                      </span>
                    </td>
                  );
                })}
                <td className="num">{shiftCount(code)}</td>
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
          Off
        </span>
      </div>
    </div>
  );
}
