import { Corners } from "../../../components/ui/Corners";
import type { StaffingSweepPoint, StaffingSweepResult } from "../../../types/models";
import "../what-if.css";
import { vi } from "../../../locales/vi";

type StaffingSweepViewProps = {
  result: StaffingSweepResult;
};

const COST_SCALE = 100;

const ASSUMPTION_LABELS: Record<StaffingSweepResult["assumption"], string> =
  vi.whatIf.staffing.labels;

function money(hundredths: number | null): string {
  return hundredths === null
    ? "-"
    : (hundredths / COST_SCALE).toLocaleString("vi-VN", { maximumFractionDigits: 0 });
}

function statusText(point: StaffingSweepPoint): string {
  return point.proven
    ? vi.whatIf.sweep.statusProven
    : vi.whatIf.sweep.statusNotProven(point.solve_status);
}

export function StaffingSweepView({ result }: StaffingSweepViewProps) {
  const unproven = result.points.filter((point) => !point.proven).length;
  return (
    <section className="blueprint scenario">
      <Corners />
      <div className="scenario-head">
        <h2 className="scenario-title">
          {vi.whatIf.staffing.title(ASSUMPTION_LABELS[result.assumption])}
        </h2>
        {unproven > 0 && (
          <span className="tag tag-outline scenario-tag">
            {vi.whatIf.sweep.unproven(unproven, result.points.length)}
          </span>
        )}
      </div>
      <p className="scenario-caption">
        {vi.whatIf.staffing.label}. {vi.whatIf.staffing.caption}
      </p>
      <div className="table-wrap">
        <table className="table">
          <caption className="visually-hidden">{vi.whatIf.staffing.tableCaption}</caption>
          <thead>
            <tr>
              <th scope="col" className="num">
                {vi.whatIf.staffing.value}
              </th>
              <th scope="col" className="num">
                {vi.whatIf.sweep.weeklyCost}
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
            {result.points.map((point) => (
              <tr key={point.value}>
                <th scope="row" className="num">
                  {point.value}
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
    </section>
  );
}
