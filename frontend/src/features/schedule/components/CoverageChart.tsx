import { useState } from "react";
import { DAY_NAMES, DAYS, formatHour, HOURS, HOURS_PER_DAY } from "../../../lib/time";
import type { KpiRead } from "../../../types/models";
import "../schedule.css";

type CoverageChartProps = {
  kpi: KpiRead;
};

const CHART_HEIGHT = 140;
const TICK_EVERY = 3;

type HourBar = {
  hour: number;
  required: number;
  staffed: number;
};

function dayHours(kpi: KpiRead, day: number): HourBar[] {
  return HOURS.map((hour) => ({
    hour,
    required: kpi.required_by_hour[day * HOURS_PER_DAY + hour] ?? 0,
    staffed: kpi.staff_by_hour[day * HOURS_PER_DAY + hour] ?? 0,
  }));
}

function describe(day: number, bar: HourBar): string {
  const gap = bar.staffed - bar.required;
  const status = gap < 0 ? `${-gap} short` : gap > 0 ? `${gap} over` : "exact";
  return `${DAYS[day]} ${formatHour(bar.hour)}: required ${bar.required}, staffed ${bar.staffed} (${status})`;
}

function dayTotals(kpi: KpiRead, day: number) {
  return dayHours(kpi, day).reduce(
    (totals, bar) => ({
      short: totals.short + Math.max(0, bar.required - bar.staffed),
      over: totals.over + Math.max(0, bar.staffed - bar.required),
    }),
    { short: 0, over: 0 },
  );
}

export function CoverageChart({ kpi }: CoverageChartProps) {
  const [day, setDay] = useState(0);
  const bars = dayHours(kpi, day);
  const peak = Math.max(1, ...kpi.required_by_hour, ...kpi.staff_by_hour);
  const unit = CHART_HEIGHT / (peak + 1);
  const totals = dayTotals(kpi, day);

  return (
    <div className="coverage">
      <div className="coverage-head">
        <p className="coverage-summary">
          {DAY_NAMES[day]}: {totals.short} staff-hours short, {totals.over} staff-hours over
        </p>
        <fieldset className="toggle-group">
          <legend className="visually-hidden">Day shown in the chart</legend>
          {DAYS.map((label, index) => (
            <button
              key={label}
              type="button"
              className="toggle"
              aria-pressed={index === day}
              onClick={() => setDay(index)}
            >
              {label}
            </button>
          ))}
        </fieldset>
      </div>
      <div
        className="coverage-bars"
        style={{ height: CHART_HEIGHT }}
        role="img"
        aria-label={`Staffing against demand by hour on ${DAY_NAMES[day]}. ${totals.short} staff-hours short, ${totals.over} over. Exact values are in the table below.`}
      >
        {bars.map((bar) => {
          const covered = Math.min(bar.staffed, bar.required);
          const over = Math.max(0, bar.staffed - bar.required);
          const short = Math.max(0, bar.required - bar.staffed);
          return (
            <div key={bar.hour} className="coverage-bar" title={describe(day, bar)}>
              <div className="coverage-covered" style={{ height: covered * unit }} />
              <div
                className="coverage-over"
                style={{ bottom: covered * unit, height: over * unit }}
              />
              <div
                className="coverage-short"
                style={{ bottom: covered * unit, height: short * unit }}
              />
              <div className="coverage-required" style={{ bottom: bar.required * unit }} />
            </div>
          );
        })}
      </div>
      <div className="coverage-ticks" aria-hidden="true">
        {bars.map((bar) => (
          <span key={bar.hour}>
            {bar.hour % TICK_EVERY === 0 ? String(bar.hour).padStart(2, "0") : ""}
          </span>
        ))}
      </div>
      <div className="legend coverage-legend">
        <span className="legend-item">
          <span className="swatch coverage-covered-swatch" />
          Staff covering demand
        </span>
        <span className="legend-item">
          <span className="swatch coverage-over-swatch" />
          Overstaffed (above the line)
        </span>
        <span className="legend-item">
          <span className="swatch coverage-short-swatch" />
          Understaffed
        </span>
        <span className="legend-item">
          <span className="swatch coverage-required-swatch" />
          Required staff
        </span>
      </div>
      <details className="data-details">
        <summary>Show {DAY_NAMES[day]} as a table</summary>
        <div className="table-wrap">
          <table className="table">
            <caption className="visually-hidden">Hourly coverage on {DAY_NAMES[day]}</caption>
            <thead>
              <tr>
                <th scope="col">Hour</th>
                <th scope="col" className="num">
                  Required
                </th>
                <th scope="col" className="num">
                  Staffed
                </th>
                <th scope="col" className="num">
                  Difference
                </th>
              </tr>
            </thead>
            <tbody>
              {bars.map((bar) => (
                <tr key={bar.hour}>
                  <th scope="row">{formatHour(bar.hour)}</th>
                  <td className="num">{bar.required}</td>
                  <td className="num">{bar.staffed}</td>
                  <td className="num">{bar.staffed - bar.required}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </div>
  );
}
