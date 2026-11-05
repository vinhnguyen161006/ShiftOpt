import { Corners } from "../../../components/ui/Corners";
import type { StaffingSweepPoint, StaffingSweepResult } from "../../../types/models";
import "../what-if.css";

type StaffingSweepViewProps = {
  result: StaffingSweepResult;
};

const COST_SCALE = 100;

const ASSUMPTION_LABELS: Record<StaffingSweepResult["assumption"], string> = {
  alpha: "alpha (scale factor on normalized sales)",
  productivity: "p (sales units one person handles per hour)",
  min_staff: "min_staff (floor for every hour)",
  night_min_staff: "night_min_staff (floor for 22h-06h)",
};

function money(hundredths: number | null): string {
  return hundredths === null
    ? "-"
    : (hundredths / COST_SCALE).toLocaleString("en-US", { maximumFractionDigits: 0 });
}

function statusText(point: StaffingSweepPoint): string {
  return point.proven ? "optimal (proven)" : `${point.solve_status}, not proven optimal`;
}

export function StaffingSweepView({ result }: StaffingSweepViewProps) {
  const unproven = result.points.filter((point) => !point.proven).length;
  return (
    <section className="blueprint scenario">
      <Corners />
      <div className="scenario-head">
        <h2 className="scenario-title">
          Conversion assumption: {ASSUMPTION_LABELS[result.assumption]}
        </h2>
        {unproven > 0 && (
          <span className="tag tag-outline scenario-tag">
            {unproven} of {result.points.length} not proven optimal
          </span>
        )}
      </div>
      <p className="scenario-caption">
        {result.label}. Each row derives the required head count from the FreshRetailNet load with
        that value, then re-solves the roster at the same time limit and seed.
      </p>
      <div className="table-wrap">
        <table className="table">
          <caption className="visually-hidden">Staffing assumption sweep points</caption>
          <thead>
            <tr>
              <th scope="col" className="num">
                Value
              </th>
              <th scope="col" className="num">
                Weekly cost
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
