import { useState } from "react";
import { KpiStrip } from "../../../components/ui/Layout";
import type { DemandSweepResult, SweepPoint } from "../../../types/models";
import "../what-if.css";
import { LambdaSlider } from "./LambdaSlider";

type SweepViewProps = {
  result: DemandSweepResult;
};

const COST_SCALE = 100;
const VIEW_WIDTH = 200;
const VIEW_HEIGHT = 80;
const PAD = 8;

function money(hundredths: number | null | undefined): string {
  return hundredths === null || hundredths === undefined
    ? "-"
    : (hundredths / COST_SCALE).toLocaleString("en-US", { maximumFractionDigits: 0 });
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
  return point.proven ? "optimal (proven)" : `${point.solve_status}, not proven optimal`;
}

export function SweepView({ result }: SweepViewProps) {
  const points = result.points;
  const defaultIndex = Math.max(
    0,
    points.findIndex((point) => point.multiplier === 1),
  );
  const [index, setIndex] = useState(defaultIndex);
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
  return (
    <div className="form-stack">
      <LambdaSlider
        multipliers={points.map((point) => point.multiplier)}
        index={index}
        onChange={setIndex}
      />
      <KpiStrip
        items={[
          {
            label: "Weekly labor cost",
            value: money(selected.labor_cost),
            sub: `at ${selected.multiplier.toFixed(1)}x demand`,
          },
          {
            label: "Short hours",
            value: selected.understaffed_hours === null ? "-" : `${selected.understaffed_hours} h`,
            sub: "staff-hours below demand",
          },
          {
            label: "Paid hours",
            value: selected.staffed_hours === null ? "-" : `${selected.staffed_hours} h`,
            sub: "shift hours incl. breaks",
          },
          {
            label: "Solver result",
            value: selected.proven ? "OPTIMAL" : selected.solve_status.toUpperCase(),
            sub: selected.proven ? "proven for this instance" : "not proven optimal",
          },
        ]}
      />
      <div className="curve">
        <div className="label-caps curve-label">Cost curve z(lambda)</div>
        <svg
          className="curve-svg"
          viewBox={`0 0 ${VIEW_WIDTH} ${VIEW_HEIGHT}`}
          preserveAspectRatio="none"
          role="img"
          aria-label={`Weekly labor cost for each demand multiplier. ${unproven} of ${points.length} points are not proven optimal. Values are in the table below.`}
        >
          <line
            x1="0"
            y1={VIEW_HEIGHT - 1}
            x2={VIEW_WIDTH}
            y2={VIEW_HEIGHT - 1}
            stroke="var(--color-divider)"
            strokeWidth="1"
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
                r={pointIndex === index ? 3.6 : 2.4}
                fill={item.point.proven ? "var(--color-accent-700)" : "var(--color-bg)"}
                stroke="var(--color-accent-700)"
                strokeWidth="1.2"
                vectorEffect="non-scaling-stroke"
              />
            ),
          )}
        </svg>
        <div className="curve-axis" aria-hidden="true">
          {points.map((point) => (
            <span key={point.multiplier}>{point.multiplier.toFixed(1)}</span>
          ))}
        </div>
        <div className="legend">
          <span className="legend-item">
            <span className="swatch curve-dot" />
            Proven optimal
          </span>
          <span className="legend-item">
            <span className="swatch curve-dot curve-dot-open" />
            Not proven: the gap may hide part of the cost change
          </span>
        </div>
      </div>
      <details className="data-details">
        <summary>Show all points as a table</summary>
        <div className="table-wrap">
          <table className="table">
            <caption className="visually-hidden">Demand sweep points</caption>
            <thead>
              <tr>
                <th scope="col">Lambda</th>
                <th scope="col" className="num">
                  Labor cost
                </th>
                <th scope="col" className="num">
                  Short hours
                </th>
                <th scope="col" className="num">
                  Paid hours
                </th>
                <th scope="col">Solver result</th>
              </tr>
            </thead>
            <tbody>
              {points.map((point) => (
                <tr key={point.multiplier}>
                  <th scope="row">{point.multiplier.toFixed(1)}x</th>
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
