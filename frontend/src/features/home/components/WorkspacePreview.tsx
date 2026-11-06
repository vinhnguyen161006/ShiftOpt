import { useState } from "react";
import { Corners } from "../../../components/ui/Corners";
import { vi } from "../../../locales/vi";
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

const TEXT = vi.home.preview;

const KPIS = [
  { label: TEXT.coverage, value: SUMMARY.coverage, sub: TEXT.coverageSub },
  { label: TEXT.laborCost, value: SUMMARY.cost, sub: TEXT.laborCostSub },
  { label: TEXT.shortHours, value: SUMMARY.shortHours, sub: TEXT.shortHoursSub },
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
        <div className="home-kpi-label">{TEXT.solverStatus}</div>
        <div className="home-kpi-value home-kpi-value-status">FEASIBLE</div>
        <div className="home-kpi-sub">{TEXT.solverStatusSub}</div>
      </div>
    </div>
  );
}

function WeeklyRoster() {
  return (
    <div className="home-panel-block">
      <div className="home-block-head">
        <h3 className="home-block-title">{TEXT.roster}</h3>
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
        <h3 className="home-block-title">{TEXT.coverageChart}</h3>
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
          {TEXT.assigned}
        </span>
        <span className="home-legend-item">
          <span className="home-swatch home-swatch-required" />
          {TEXT.required}
        </span>
        <span className="home-legend-item">
          <span className="home-swatch home-swatch-under" />
          {TEXT.under}
        </span>
        <span className="home-run-meta">{TEXT.runMeta}</span>
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
            {TEXT.panelName}
          </span>
          <span className="home-panel-week">{TEXT.week}</span>
          <span className="tag tag-outline home-tag-illustrative">{TEXT.illustrative}</span>
        </div>
        <KpiStrip />
        <WeeklyRoster />
        <StaffingCoverage />
      </div>
      <p className="home-preview-note">{TEXT.note}</p>
    </div>
  );
}
