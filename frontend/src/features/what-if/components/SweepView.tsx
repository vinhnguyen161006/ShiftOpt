import { useState } from "react";
import { Corners } from "../../../components/ui/Corners";
import { type HourBar, HourBars } from "../../../components/ui/HourBars";
import { DAY_NAMES, DAYS, HOURS, HOURS_PER_DAY } from "../../../lib/time";
import type { DemandSweepResult, SweepPoint } from "../../../types/models";
import "../what-if.css";
import { formatDecimal } from "../../../lib/number";
import { vi } from "../../../locales/vi";
import { LambdaSlider } from "./LambdaSlider";

type SweepViewProps = {
  result: DemandSweepResult;
};

const COST_SCALE = 100;
const VIEW_WIDTH = 200;
const VIEW_HEIGHT = 72;
const PAD = 8;
const BARS_HEIGHT = 132;

function money(hundredths: number | null | undefined): string {
  return hundredths === null || hundredths === undefined
    ? "-"
    : (hundredths / COST_SCALE).toLocaleString("vi-VN", { maximumFractionDigits: 0 });
}

function curvePoints(points: SweepPoint[]) {
  const costs = points
    .map((point) => point.labor_cost)
    .filter((cost): cost is number => cost !== null);
  const low = Math.min(...costs);
  const high = Math.max(...costs);
  const span = high - low || 1;
  return points.map((point, index) => ({
    point,
    x: PAD + (index / Math.max(1, points.length - 1)) * (VIEW_WIDTH - 2 * PAD),
    y:
      point.labor_cost === null
        ? null
        : VIEW_HEIGHT - PAD - ((point.labor_cost - low) / span) * (VIEW_HEIGHT - 2 * PAD),
  }));
}

function statusText(point: SweepPoint): string {
  return point.proven
    ? vi.whatIf.sweep.statusProven
    : vi.whatIf.sweep.statusNotProven(point.solve_status);
}

function barsFor(point: SweepPoint, day: number): HourBar[] | null {
  const staff = point.staff_by_hour;
  const required = point.required_by_hour;
  if (!staff || !required) {
    return null;
  }
  return HOURS.map((hour) => ({
    hour,
    assigned: staff[day * HOURS_PER_DAY + hour] ?? 0,
    required: required[day * HOURS_PER_DAY + hour] ?? 0,
  }));
}

function weekPeak(points: SweepPoint[]): number {
  return Math.max(
    1,
    ...points.flatMap((point) => [
      ...(point.staff_by_hour ?? []),
      ...(point.required_by_hour ?? []),
    ]),
  );
}

function busiestDay(point: SweepPoint | undefined): number {
  const required = point?.required_by_hour;
  if (!required) {
    return 0;
  }
  const totals = DAYS.map((_, day) =>
    required.slice(day * HOURS_PER_DAY, (day + 1) * HOURS_PER_DAY).reduce((sum, v) => sum + v, 0),
  );
  return totals.indexOf(Math.max(...totals));
}

export function SweepView({ result }: SweepViewProps) {
  const points = result.points;
  const defaultIndex = Math.max(
    0,
    points.findIndex((point) => point.multiplier === 1),
  );
  const [index, setIndex] = useState(defaultIndex);
  const [day, setDay] = useState(() => busiestDay(points[defaultIndex]));
  const selected = points[index];
  const plotted = curvePoints(points);
  const line = plotted
    .filter((item) => item.y !== null)
    .map((item) => `${item.x.toFixed(1)},${(item.y ?? 0).toFixed(1)}`)
    .join(" ");
  const unproven = points.filter((point) => !point.proven).length;

  if (!selected) {
    return null;
  }
  const bars = barsFor(selected, day);
  return (
    <div className="form-stack">
      <section className="blueprint scenario">
        <Corners />
        <div className="scenario-head">
          <h2 className="scenario-title">{vi.whatIf.sweep.title}</h2>
          {unproven > 0 && (
            <span className="tag tag-outline scenario-tag">
              {vi.whatIf.sweep.unproven(unproven, points.length)}
            </span>
          )}
          {bars && (
            <fieldset className="toggle-group scenario-days">
              <legend className="visually-hidden">{vi.whatIf.sweep.dayLegend}</legend>
              {DAYS.map((label, dayIndex) => (
                <button
                  key={label}
                  type="button"
                  className="toggle"
                  aria-pressed={dayIndex === day}
                  onClick={() => setDay(dayIndex)}
                >
                  {label}
                </button>
              ))}
            </fieldset>
          )}
        </div>
        <p className="scenario-caption">
          {vi.whatIf.sweep.caption}
          {bars ? vi.whatIf.sweep.captionDay(DAY_NAMES[day]) : ""}
        </p>
        {bars ? (
          <>
            <HourBars
              bars={bars}
              height={BARS_HEIGHT}
              peak={weekPeak(points)}
              dayLabel={DAYS[day]}
              spaced
              label={vi.whatIf.sweep.barsAria(
                DAY_NAMES[day],
                formatDecimal(selected.multiplier, 1),
              )}
            />
            <div className="legend scenario-legend">
              <span className="legend-item">
                <span className="swatch swatch-assigned" />
                {vi.schedule.coverage.assigned}
              </span>
              <span className="legend-item">
                <span className="swatch swatch-required" />
                {vi.schedule.coverage.required}
              </span>
              <span className="legend-item">
                <span className="swatch swatch-under" />
                {vi.schedule.coverage.under}
              </span>
            </div>
          </>
        ) : (
          <p className="muted scenario-missing">{vi.whatIf.sweep.missing}</p>
        )}
        <div className="scenario-lambda">
          <LambdaSlider
            multipliers={points.map((point) => point.multiplier)}
            index={index}
            onChange={setIndex}
          />
        </div>
        <div className="scenario-results">
          <div className="scenario-curve">
            <div className="label-caps scenario-curve-label">{vi.whatIf.sweep.curve}</div>
            <svg
              className="scenario-curve-svg"
              viewBox={`0 0 ${VIEW_WIDTH} ${VIEW_HEIGHT}`}
              preserveAspectRatio="none"
              role="img"
              aria-label={vi.whatIf.sweep.curveAria(unproven, points.length)}
            >
              <line
                x1="0"
                y1={VIEW_HEIGHT - 1}
                x2={VIEW_WIDTH}
                y2={VIEW_HEIGHT - 1}
                stroke="var(--color-divider)"
                strokeWidth="1"
              />
              <line
                x1="0"
                y1={VIEW_HEIGHT / 2}
                x2={VIEW_WIDTH}
                y2={VIEW_HEIGHT / 2}
                stroke="var(--color-divider)"
                strokeWidth="1"
                strokeDasharray="3 3"
              />
              <polyline
                points={line}
                fill="none"
                stroke="var(--color-accent-700)"
                strokeWidth="1.6"
                vectorEffect="non-scaling-stroke"
              />
              {plotted.map((item, pointIndex) =>
                item.y === null ? null : (
                  <circle
                    key={item.point.multiplier}
                    cx={item.x}
                    cy={item.y}
                    r={pointIndex === index ? 3.4 : 2.2}
                    fill={item.point.proven ? "var(--color-accent-700)" : "var(--color-bg)"}
                    stroke="var(--color-accent-700)"
                    strokeWidth="1.2"
                    vectorEffect="non-scaling-stroke"
                  />
                ),
              )}
            </svg>
            <div className="legend scenario-legend">
              <span className="legend-item">
                <span className="swatch curve-dot" />
                {vi.whatIf.sweep.provenLegend}
              </span>
              <span className="legend-item">
                <span className="swatch curve-dot curve-dot-open" />
                {vi.whatIf.sweep.notProvenLegend}
              </span>
            </div>
          </div>
          <div className="scenario-figures">
            <div>
              <div className="label-caps">{vi.whatIf.sweep.weeklyCost}</div>
              <div className="scenario-figure-value">{money(selected.labor_cost)}</div>
            </div>
            <div>
              <div className="label-caps">{vi.whatIf.sweep.short}</div>
              <div className="scenario-figure-value">
                {selected.understaffed_hours === null
                  ? "-"
                  : vi.home.sample.hours(selected.understaffed_hours)}
              </div>
            </div>
            <div>
              <div className="label-caps">{vi.whatIf.sweep.paid}</div>
              <div className="scenario-figure-value">
                {selected.staffed_hours === null
                  ? "-"
                  : vi.home.sample.hours(selected.staffed_hours)}
              </div>
            </div>
            <div>
              <div className="label-caps">{vi.whatIf.sweep.solverResult}</div>
              <div className="scenario-figure-value">
                {selected.proven ? "OPTIMAL" : selected.solve_status.toUpperCase()}
              </div>
              {!selected.proven && (
                <div className="scenario-figure-sub">{vi.whatIf.sweep.notProven}</div>
              )}
            </div>
            <div className="scenario-note">{vi.whatIf.sweep.note}</div>
          </div>
        </div>
      </section>
      <details className="data-details">
        <summary>{vi.whatIf.sweep.showTable}</summary>
        <div className="table-wrap">
          <table className="table">
            <caption className="visually-hidden">{vi.whatIf.sweep.tableCaption}</caption>
            <thead>
              <tr>
                <th scope="col">{vi.whatIf.sweep.lambda}</th>
                <th scope="col" className="num">
                  {vi.whatIf.sweep.laborCost}
                </th>
                <th scope="col" className="num">
                  {vi.whatIf.sweep.short}
                </th>
                <th scope="col" className="num">
                  {vi.whatIf.sweep.paid}
                </th>
                <th scope="col">{vi.whatIf.sweep.solverResult}</th>
              </tr>
            </thead>
            <tbody>
              {points.map((point) => (
                <tr key={point.multiplier}>
                  <th scope="row">
                    {vi.whatIf.sweep.sliderValue(formatDecimal(point.multiplier, 1))}
                  </th>
                  <td className="num">{money(point.labor_cost)}</td>
                  <td className="num">{point.understaffed_hours ?? "-"}</td>
                  <td className="num">{point.staffed_hours ?? "-"}</td>
                  <td>{statusText(point)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </div>
  );
}
