import { Corners } from "../../../components/ui/Corners";
import { formatDecimal } from "../../../lib/number";
import { vi } from "../../../locales/vi";
import type { FairnessSweepPoint, FairnessSweepResult } from "../../../types/models";
import "../what-if.css";

type FairnessSweepViewProps = {
  result: FairnessSweepResult;
};

type ChartRow = { x: number; y: number; proven: boolean };

const VIEW_WIDTH = 200;
const VIEW_HEIGHT = 72;
const PAD = 8;
function percent(value: number | null): string {
  return value === null ? "-" : formatDecimal(value, 2);
}

function statusText(point: FairnessSweepPoint): string {
  return point.proven
    ? vi.whatIf.sweep.statusProven
    : vi.whatIf.sweep.statusNotProven(point.solve_status);
}

function chartRows(
  points: FairnessSweepPoint[],
  measure: (point: FairnessSweepPoint) => number | null,
): ChartRow[] | null {
  const rows: ChartRow[] = [];
  for (const point of points) {
    const y = measure(point);
    if (point.cost_increase_percent === null || y === null) {
      return null;
    }
    rows.push({ x: point.cost_increase_percent, y, proven: point.proven });
  }
  return rows;
}

function SpreadChart({
  title,
  unit,
  rows,
  ariaLabel,
}: {
  title: string;
  unit: string;
  rows: ChartRow[];
  ariaLabel: string;
}) {
  const xMax = Math.max(...rows.map((row) => row.x), 1);
  const yMax = Math.max(...rows.map((row) => row.y), 1);
  const plotX = (x: number) => PAD + (x / xMax) * (VIEW_WIDTH - 2 * PAD);
  const plotY = (y: number) => VIEW_HEIGHT - PAD - (y / yMax) * (VIEW_HEIGHT - 2 * PAD);
  const line = rows.map((row) => `${plotX(row.x)},${plotY(row.y)}`).join(" ");
  return (
    <div className="fairness-chart">
      <div className="label-caps scenario-curve-label">
        {title} ({unit})
      </div>
      <svg
        className="scenario-curve-svg"
        viewBox={`0 0 ${VIEW_WIDTH} ${VIEW_HEIGHT}`}
        preserveAspectRatio="none"
        role="img"
        aria-label={ariaLabel}
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
        {rows.map((row) => (
          <circle
            key={row.x}
            cx={plotX(row.x)}
            cy={plotY(row.y)}
            r={2.6}
            fill={row.proven ? "var(--color-accent-700)" : "var(--color-bg)"}
            stroke="var(--color-accent-700)"
            strokeWidth="1.2"
            vectorEffect="non-scaling-stroke"
          />
        ))}
      </svg>
    </div>
  );
}

export function FairnessSweepView({ result }: FairnessSweepViewProps) {
  const unproven = result.points.filter((point) => !point.proven).length;
  const nightRows = chartRows(result.points, (point) => point.night_spread);
  const hoursRows = chartRows(result.points, (point) => point.hours_spread);
  return (
    <section className="blueprint scenario">
      <Corners />
      <div className="scenario-head">
        <h2 className="scenario-title">{vi.whatIf.fairness.title}</h2>
        {unproven > 0 && (
          <span className="tag tag-outline scenario-tag">
            {vi.whatIf.sweep.unproven(unproven, result.points.length)}
          </span>
        )}
      </div>
      <p className="scenario-caption">
        {vi.whatIf.fairness.label}. {vi.whatIf.fairness.caption}
      </p>
      {nightRows && hoursRows ? (
        <div className="fairness-charts">
          <SpreadChart
            title={vi.whatIf.fairness.nightChart}
            unit={vi.whatIf.fairness.nightUnit}
            rows={nightRows}
            ariaLabel={vi.whatIf.fairness.nightAria}
          />
          <SpreadChart
            title={vi.whatIf.fairness.hoursChart}
            unit={vi.whatIf.fairness.hoursUnit}
            rows={hoursRows}
            ariaLabel={vi.whatIf.fairness.hoursAria}
          />
        </div>
      ) : (
        <p className="muted">{vi.whatIf.fairness.noBaseline}</p>
      )}
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
      <details className="data-details">
        <summary>{vi.whatIf.sweep.showTable}</summary>
        <div className="table-wrap">
          <table className="table">
            <caption className="visually-hidden">{vi.whatIf.fairness.tableCaption}</caption>
            <thead>
              <tr>
                <th scope="col" className="num">
                  {vi.whatIf.fairness.tolerance}
                </th>
                <th scope="col" className="num">
                  {vi.whatIf.fairness.costIncrease}
                </th>
                <th scope="col" className="num">
                  {vi.whatIf.fairness.nightSpread}
                </th>
                <th scope="col" className="num">
                  {vi.whatIf.fairness.hoursSpread}
                </th>
                <th scope="col" className="num">
                  {vi.whatIf.sweep.short}
                </th>
                <th scope="col">{vi.whatIf.sweep.solverResult}</th>
              </tr>
            </thead>
            <tbody>
              {result.points.map((point) => (
                <tr key={point.tolerance_percent}>
                  <th scope="row" className="num">
                    {point.tolerance_percent}
                  </th>
                  <td className="num">{percent(point.cost_increase_percent)}</td>
                  <td className="num">{point.night_spread ?? "-"}</td>
                  <td className="num">{point.hours_spread ?? "-"}</td>
                  <td className="num">{point.understaffed_hours ?? "-"}</td>
                  <td>{statusText(point)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </section>
  );
}
