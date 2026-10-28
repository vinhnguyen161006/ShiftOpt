import { useState } from "react";
import { Notice } from "../../../components/ui/Feedback";
import { DAY_NAMES, DAYS, formatHour, HOURS, HOURS_PER_DAY } from "../../../lib/time";
import type { MarginalCostResult } from "../../../types/models";
import "../what-if.css";

type SensitivityHeatmapProps = {
  result: MarginalCostResult;
};

type Measure = "marginal" | "dual";

const COST_SCALE = 100;
const STEPS = 5;

function format(value: number | null | undefined): string {
  return value === null || value === undefined
    ? "no solution"
    : (value / COST_SCALE).toLocaleString("en-US", { maximumFractionDigits: 1 });
}

function bucket(value: number | null | undefined, peak: number): number {
  if (value === null || value === undefined || value <= 0 || peak <= 0) {
    return 0;
  }
  return Math.min(STEPS, Math.ceil((value / peak) * STEPS));
}

function thresholds(peak: number): string[] {
  return Array.from({ length: STEPS }, (_, step) => format((peak * (step + 1)) / STEPS));
}

export function SensitivityHeatmap({ result }: SensitivityHeatmapProps) {
  const [measure, setMeasure] = useState<Measure>("marginal");
  const values = measure === "marginal" ? result.marginal_cost_by_hour : result.lp_dual_by_hour;
  const peak = Math.max(0, ...values.map((value) => value ?? 0));
  const unproven = result.proven_by_hour.filter((proven) => !proven).length;

  function cellLabel(hour: number): string {
    const value = values[hour];
    const proven = result.proven_by_hour[hour];
    const day = Math.floor(hour / HOURS_PER_DAY);
    const time = formatHour(hour % HOURS_PER_DAY);
    const note = measure === "marginal" && !proven ? " (not proven, read as an estimate)" : "";
    return `${DAY_NAMES[day]} ${time}: ${format(value)}${note}`;
  }

  return (
    <div className="form-stack">
      <div className="heatmap-head">
        <fieldset className="toggle-group">
          <legend className="visually-hidden">Value shown in each cell</legend>
          <button
            type="button"
            className="toggle"
            aria-pressed={measure === "marginal"}
            onClick={() => setMeasure("marginal")}
          >
            Marginal cost (re-solve)
          </button>
          <button
            type="button"
            className="toggle"
            aria-pressed={measure === "dual"}
            onClick={() => setMeasure("dual")}
          >
            LP dual (approximate)
          </button>
        </fieldset>
        <p className="muted heatmap-note">
          Base weekly cost {format(result.base_cost)} ({result.base_status}). Each cell is the cost
          of one more person required in that hour.
        </p>
      </div>
      {measure === "dual" ? (
        <Notice kind="warning" title="Approximate">
          {result.label}. The LP dual is not a shadow price of the integer schedule; compare it with
          the re-solved marginal cost.
        </Notice>
      ) : (
        unproven > 0 && (
          <Notice kind="warning" title={`${unproven} of 168 hours not proven optimal`}>
            Hatched cells come from a solve that stopped before proving optimality, so the
            difference may include part of the gap.
          </Notice>
        )
      )}
      <div className="heatmap-scroll">
        <table className="heatmap">
          <caption className="visually-hidden">
            {measure === "marginal" ? "Marginal cost" : "LP dual"} for each hour of the week
          </caption>
          <thead>
            <tr>
              <th scope="col">
                <span className="visually-hidden">Day</span>
              </th>
              {HOURS.map((hour) => (
                <th key={hour} scope="col">
                  {hour % 3 === 0 ? (
                    String(hour).padStart(2, "0")
                  ) : (
                    <span className="visually-hidden">{hour}</span>
                  )}
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
                  const value = values[index];
                  const unprovenCell = measure === "marginal" && !result.proven_by_hour[index];
                  const missing = value === null || value === undefined;
                  const classes = [
                    "heatmap-cell",
                    `heat-${bucket(value, peak)}`,
                    unprovenCell ? "is-unproven" : "",
                    missing ? "is-missing" : "",
                  ]
                    .filter(Boolean)
                    .join(" ");
                  return (
                    <td key={hour} className={classes} title={cellLabel(index)}>
                      <span className="visually-hidden">{cellLabel(index)}</span>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="legend">
        <span className="legend-item">
          <span className="swatch heatmap-cell heat-0" />0
        </span>
        {thresholds(peak).map((label, step) => (
          <span key={label} className="legend-item">
            <span className={`swatch heatmap-cell heat-${step + 1}`} />
            up to {label}
          </span>
        ))}
        {measure === "marginal" && (
          <span className="legend-item">
            <span className="swatch heatmap-cell heat-0 is-unproven" />
            Not proven
          </span>
        )}
      </div>
    </div>
  );
}
