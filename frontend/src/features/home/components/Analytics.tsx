import { SUMMARY } from "../sample-data";
import { ScenarioPanel } from "./ScenarioPanel";

const TILES = [
  { label: "Coverage ratio", value: SUMMARY.coverage, sub: "min(staff, required) / required" },
  { label: "Understaffed", value: SUMMARY.shortHours, sub: "hours below requirement" },
  { label: "Overstaffed", value: SUMMARY.overHours, sub: "hours above requirement" },
  { label: "Labor cost", value: SUMMARY.cost, sub: "per scheduled week" },
];

export function Analytics() {
  return (
    <section id="analytics" className="home-analytics">
      <div className="container home-split">
        <div className="home-analytics-copy">
          <div className="home-eyebrow">Decision support</div>
          <h2 className="home-section-title home-analytics-title">
            Understand Every Scheduling Decision
          </h2>
          <p className="home-analytics-text">
            A schedule is a trade between three quantities: the demand curve you entered, the
            coverage your roster actually delivers, and what that roster costs. ShiftOpt keeps all
            three on the same screen so the trade is visible rather than implied.
          </p>
          <p className="home-analytics-text home-analytics-text-last">
            Coverage is modelled as a soft constraint with a heavy penalty, so a short-staffed week
            returns a schedule that shows you which hours are short &mdash; not an infeasible result
            with no explanation.
          </p>
          <div className="home-tiles">
            {TILES.map((tile) => (
              <div key={tile.label} className="home-tile">
                <div className="home-kpi-label">{tile.label}</div>
                <div className="home-tile-value">{tile.value}</div>
                <div className="home-kpi-sub">{tile.sub}</div>
              </div>
            ))}
          </div>
          <div className="home-callout">
            <div className="home-callout-title">Solver proposes, validator judges</div>
            <p className="home-callout-text">
              Hard constraints are re-checked on the produced schedule by a validator written
              independently of the optimization model. A result is only reported as compliant once
              that check has run on that schedule.
            </p>
          </div>
        </div>
        <ScenarioPanel />
      </div>
    </section>
  );
}
