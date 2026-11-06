import { useState } from "react";
import { type HourBar, HourBars } from "../../../components/ui/HourBars";
import { WorkspaceBlock } from "../../../components/ui/Workspace";
import { DAY_NAMES, DAYS, formatHour, HOURS, HOURS_PER_DAY } from "../../../lib/time";
import type { KpiRead } from "../../../types/models";
import "../schedule.css";
import { vi } from "../../../locales/vi";

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
      title={vi.schedule.coverage.title}
      caption={vi.schedule.coverage.caption(DAY_NAMES[day], totals.short, totals.over)}
      aside={
        <fieldset className="toggle-group">
          <legend className="visually-hidden">{vi.schedule.coverage.dayLegend}</legend>
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
        label={vi.schedule.coverage.aria(DAY_NAMES[day], totals.short, totals.over)}
      />
      <div className="chart-legend">
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
        <span className="chart-meta">{meta}</span>
      </div>
      <details className="data-details">
        <summary>{vi.schedule.coverage.showTable(DAY_NAMES[day])}</summary>
        <div className="table-wrap">
          <table className="table">
            <caption className="visually-hidden">
              {vi.schedule.coverage.tableCaption(DAY_NAMES[day])}
            </caption>
            <thead>
              <tr>
                <th scope="col">{vi.schedule.coverage.hour}</th>
                <th scope="col" className="num">
                  {vi.schedule.coverage.requiredColumn}
                </th>
                <th scope="col" className="num">
                  {vi.schedule.coverage.assignedColumn}
                </th>
                <th scope="col" className="num">
                  {vi.schedule.coverage.difference}
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
