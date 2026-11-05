import { useState } from "react";
import { type HourBar, HourBars } from "../../../components/ui/HourBars";
import { WorkspaceBlock } from "../../../components/ui/Workspace";
import { DAY_NAMES, DAYS, formatHour, HOURS, HOURS_PER_DAY } from "../../../lib/time";
import type { KpiRead } from "../../../types/models";
import "../schedule.css";

type CoverageChartProps = {
  kpi: KpiRead;
  meta: string;
};

const CHART_HEIGHT = 120;
const SHORT_WEIGHT = 1000;

function dayBars(kpi: KpiRead, day: number): HourBar[] {
  return HOURS.map((hour) => ({
    hour,
    required: kpi.required_by_hour[day * HOURS_PER_DAY + hour] ?? 0,
    assigned: kpi.staff_by_hour[day * HOURS_PER_DAY + hour] ?? 0,
  }));
}

function dayTotals(bars: HourBar[]) {
  return bars.reduce(
    (totals, bar) => ({
      short: totals.short + Math.max(0, bar.required - bar.assigned),
      over: totals.over + Math.max(0, bar.assigned - bar.required),
      required: totals.required + bar.required,
    }),
    { short: 0, over: 0, required: 0 },
  );
}

function defaultDay(kpi: KpiRead): number {
  const scores = DAYS.map((_, day) => {
    const totals = dayTotals(dayBars(kpi, day));
    return totals.short * SHORT_WEIGHT + totals.required;
  });
  return scores.indexOf(Math.max(...scores));
}

export function CoverageChart({ kpi, meta }: CoverageChartProps) {
  const [day, setDay] = useState(() => defaultDay(kpi));
  const bars = dayBars(kpi, day);
  const totals = dayTotals(bars);
  const peak = Math.max(1, ...kpi.required_by_hour, ...kpi.staff_by_hour);

  return (
    <WorkspaceBlock
      title="Staffing coverage"
      caption={`${DAY_NAMES[day]}: ${totals.short} staff-hours short, ${totals.over} over`}
      aside={
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
      }
    >
      <HourBars
        bars={bars}
        height={CHART_HEIGHT}
        peak={peak}
        dayLabel={DAYS[day]}
        label={`Staffing against demand by hour on ${DAY_NAMES[day]}. ${totals.short} staff-hours short, ${totals.over} over. Exact values are in the table below.`}
      />
      <div className="chart-legend">
        <span className="legend-item">
          <span className="swatch swatch-assigned" />
          Assigned staff (above the line = overstaffed)
        </span>
        <span className="legend-item">
          <span className="swatch swatch-required" />
          Required staff
        </span>
        <span className="legend-item">
          <span className="swatch swatch-under" />
          Understaffed
        </span>
        <span className="chart-meta">{meta}</span>
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
                  Assigned
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
                  <td className="num">{bar.assigned}</td>
                  <td className="num">{bar.assigned - bar.required}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </WorkspaceBlock>
  );
}
