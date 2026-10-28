import { useState } from "react";
import { Corners } from "../../../components/ui/Corners";
import {
  DAYS,
  DEFAULT_DAY,
  dayBars,
  LEGEND,
  ROSTER_ROWS,
  type ShiftLook,
  SUMMARY,
} from "../sample-data";
import { StaffingBars } from "./StaffingBars";

const KPIS = [
  { label: "Coverage ratio", value: SUMMARY.coverage, sub: "target 98.0%" },
  { label: "Labor cost", value: SUMMARY.cost, sub: "incl. night allowance" },
  { label: "Understaffed hours", value: SUMMARY.shortHours, sub: "of 168 week hours" },
];

function shiftStyle(look: ShiftLook) {
  return { background: look.bg, color: look.fg, border: `1px ${look.bs} ${look.bd}` };
}

function KpiStrip() {
  return (
    <div className="home-kpi-strip">
      {KPIS.map((kpi) => (
        <div key={kpi.label} className="home-kpi">
          <div className="home-kpi-label">{kpi.label}</div>
          <div className="home-kpi-value">{kpi.value}</div>
          <div className="home-kpi-sub">{kpi.sub}</div>
        </div>
      ))}
      <div className="home-kpi">
        <div className="home-kpi-label">Solver status</div>
        <div className="home-kpi-value home-kpi-value-status">FEASIBLE</div>
        <div className="home-kpi-sub">gap 0.8% &middot; not proven optimal</div>
      </div>
    </div>
  );
}

function WeeklyRoster() {
  return (
    <div className="home-panel-block">
      <div className="home-block-head">
        <h3 className="home-block-title">Weekly roster</h3>
        <span className="home-block-caption">{SUMMARY.rosterCaption}</span>
      </div>
      <div className="home-roster-scroll">
        <div className="home-roster">
          <div className="home-roster-row home-roster-heads">
            <div />
            {DAYS.map((day) => (
              <div key={day} className="home-roster-day">
                {day}
              </div>
            ))}
          </div>
          {ROSTER_ROWS.map((row) => (
            <div key={row.name} className="home-roster-row">
              <div className="home-roster-person">
                <div className="home-roster-name">{row.name}</div>
                <div className="home-roster-contract">{row.contract}</div>
              </div>
              {row.cells.map((cell) => (
                <div
                  key={cell.day}
                  title={cell.title}
                  className="home-roster-cell"
                  style={shiftStyle(cell.look)}
                >
                  {cell.look.label}
                </div>
              ))}
            </div>
          ))}
          <div className="home-roster-row home-roster-foot">
            <div className="home-roster-more">{SUMMARY.rosterMore}</div>
          </div>
        </div>
      </div>
      <div className="home-legend">
        {LEGEND.map((entry) => (
          <span key={entry.label} className="home-legend-item">
            <span
              className="home-swatch"
              style={{ background: entry.look.bg, border: `1px ${entry.look.bs} ${entry.look.bd}` }}
            />
            {entry.label}
          </span>
        ))}
      </div>
    </div>
  );
}

function StaffingCoverage() {
  const [day, setDay] = useState(DEFAULT_DAY);
  return (
    <div className="home-panel-block">
      <div className="home-block-head home-block-head-center">
        <h3 className="home-block-title">Staffing coverage</h3>
        <div className="home-day-tabs">
          {DAYS.map((label, index) => (
            <button
              key={label}
              type="button"
              className="home-day-tab"
              aria-pressed={index === day}
              onClick={() => setDay(index)}
            >
              {label}
            </button>
          ))}
        </div>
      </div>
      <StaffingBars bars={dayBars(day)} size="preview" />
      <div className="home-chart-legend">
        <span className="home-legend-item">
          <span className="home-swatch home-swatch-assigned" />
          Assigned staff
        </span>
        <span className="home-legend-item">
          <span className="home-swatch home-swatch-required" />
          Required staff
        </span>
        <span className="home-legend-item">
          <span className="home-swatch home-swatch-under" />
          Understaffed
        </span>
        <span className="home-run-meta">
          CP-SAT &middot; 42.6 s &middot; seed 20240304 &middot; 1 worker
        </span>
      </div>
    </div>
  );
}

export function WorkspacePreview() {
  return (
    <div className="home-hero-preview">
      <div className="blueprint home-panel">
        <Corners />
        <div className="home-panel-head">
          <span className="home-panel-name">
            <span className="home-panel-dot" />
            ShiftOpt Workspace
          </span>
          <span className="home-panel-week">Week 10 &middot; Mar 04&ndash;10, 2024</span>
          <span className="tag tag-outline home-tag-illustrative">Illustrative demo data</span>
        </div>
        <KpiStrip />
        <WeeklyRoster />
        <StaffingCoverage />
      </div>
      <p className="home-preview-note">
        Preview rendered from local sample data. Figures are illustrative, not verified solver
        output or a benchmark result.
      </p>
    </div>
  );
}
