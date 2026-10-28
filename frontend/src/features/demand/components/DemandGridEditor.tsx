import type { ClipboardEvent, KeyboardEvent } from "react";
import { DAYS, formatHour, HOURS, HOURS_PER_DAY, HOURS_PER_WEEK } from "../../../lib/time";

type DemandGridEditorProps = {
  value: number[];
  onChange?: (value: number[]) => void;
  invalidCells?: Set<number>;
  caption: string;
};

const SHADE_STEPS = ["", "shade-1", "shade-2", "shade-3", "shade-4", "shade-5"];

export function cellId(index: number): string {
  return `demand-cell-${index}`;
}

function shadeClass(count: number, peak: number): string {
  if (count <= 0 || peak <= 0) {
    return SHADE_STEPS[0];
  }
  const step = Math.ceil((count / peak) * (SHADE_STEPS.length - 1));
  return SHADE_STEPS[Math.min(step, SHADE_STEPS.length - 1)];
}

function focusCell(index: number) {
  if (index >= 0 && index < HOURS_PER_WEEK) {
    document.getElementById(cellId(index))?.focus();
  }
}

const KEY_OFFSETS: Record<string, (index: number) => number> = {
  ArrowRight: (index) => index + 1,
  ArrowLeft: (index) => index - 1,
  ArrowDown: (index) => index + HOURS_PER_DAY,
  ArrowUp: (index) => index - HOURS_PER_DAY,
  Home: (index) => index - (index % HOURS_PER_DAY),
  End: (index) => index - (index % HOURS_PER_DAY) + HOURS_PER_DAY - 1,
};

function parseCount(text: string): number {
  const digits = text.replace(/[^0-9]/g, "");
  return digits === "" ? 0 : Number(digits);
}

export function DemandGridEditor({
  value,
  onChange,
  invalidCells,
  caption,
}: DemandGridEditorProps) {
  const peak = Math.max(0, ...value);
  const readOnly = onChange === undefined;

  function setCell(index: number, count: number) {
    if (!onChange) {
      return;
    }
    const next = [...value];
    next[index] = count;
    onChange(next);
  }

  function handleKeyDown(event: KeyboardEvent<HTMLInputElement>, index: number) {
    const move = KEY_OFFSETS[event.key];
    if (!move) {
      return;
    }
    event.preventDefault();
    focusCell(move(index));
  }

  function handlePaste(event: ClipboardEvent<HTMLInputElement>, index: number) {
    if (!onChange) {
      return;
    }
    const text = event.clipboardData.getData("text");
    if (!/[\t\n,;]/.test(text)) {
      return;
    }
    event.preventDefault();
    const next = [...value];
    const rows = text.trim().split(/\r?\n/);
    rows.forEach((row, rowOffset) => {
      row.split(/[\t,;]/).forEach((cell, columnOffset) => {
        const day = Math.floor(index / HOURS_PER_DAY) + rowOffset;
        const hour = (index % HOURS_PER_DAY) + columnOffset;
        if (day < DAYS.length && hour < HOURS_PER_DAY) {
          next[day * HOURS_PER_DAY + hour] = parseCount(cell);
        }
      });
    });
    onChange(next);
  }

  return (
    <div className="demand-grid-wrap">
      <table className="demand-grid">
        <caption className="visually-hidden">{caption}</caption>
        <thead>
          <tr>
            <th scope="col">
              <span className="visually-hidden">Day</span>
            </th>
            {HOURS.map((hour) => (
              <th key={hour} scope="col" title={formatHour(hour)}>
                {String(hour).padStart(2, "0")}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {DAYS.map((day, dayIndex) => (
            <tr key={day}>
              <th scope="row">{day}</th>
              {HOURS.map((hour) => {
                const index = dayIndex * HOURS_PER_DAY + hour;
                const count = value[index] ?? 0;
                const invalid = invalidCells?.has(index) ?? false;
                return (
                  <td key={hour} className={shadeClass(count, peak)}>
                    {readOnly ? (
                      <span title={`${day} ${formatHour(hour)}: ${count} staff`}>{count}</span>
                    ) : (
                      <input
                        id={cellId(index)}
                        className="demand-cell"
                        inputMode="numeric"
                        autoComplete="off"
                        aria-label={`${day} ${formatHour(hour)} required staff`}
                        aria-invalid={invalid || undefined}
                        value={String(count)}
                        onFocus={(event) => event.currentTarget.select()}
                        onChange={(event) => setCell(index, parseCount(event.target.value))}
                        onKeyDown={(event) => handleKeyDown(event, index)}
                        onPaste={(event) => handlePaste(event, index)}
                      />
                    )}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
      <p className="demand-grid-help muted">
        {readOnly
          ? "Head count required in each hour, Monday 00:00 first."
          : "Type a head count per hour. Arrow keys move between cells, Home and End jump to the start or end of a day. Paste a block copied from a spreadsheet to fill several cells."}
      </p>
    </div>
  );
}
