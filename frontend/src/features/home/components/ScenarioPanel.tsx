import { useState } from "react";
import { Corners } from "../../../components/ui/Corners";
import { vi } from "../../../locales/vi";
import { DEFAULT_LAMBDA_INDEX, LAMBDAS, SCENARIO_CAPTION, scenarioView } from "../sample-data";
import { StaffingBars } from "./StaffingBars";

export function ScenarioPanel() {
  const [lambdaIndex, setLambdaIndex] = useState(DEFAULT_LAMBDA_INDEX);
  const view = scenarioView(lambdaIndex);
  return (
    <div className="home-analytics-chart">
      <div className="blueprint home-scenario">
        <Corners />
        <div className="home-scenario-head">
          <h3 className="home-scenario-title">{vi.home.scenario.title}</h3>
          <span className="tag tag-outline home-tag-illustrative">{vi.home.scenario.tag}</span>
        </div>
        <p className="home-scenario-caption">{SCENARIO_CAPTION}</p>
        <StaffingBars bars={view.bars} size="scenario" />
        <div className="home-lambda">
          <label htmlFor="lambda" className="home-lambda-label">
            {vi.home.scenario.lambda}
            <span className="home-lambda-value">{view.lambdaLabel}</span>
          </label>
          <input
            id="lambda"
            className="home-lambda-input"
            type="range"
            min={0}
            max={LAMBDAS.length - 1}
            step={1}
            value={lambdaIndex}
            onChange={(event) => setLambdaIndex(Number(event.target.value))}
            aria-label={vi.home.scenario.lambda}
          />
          <div className="home-lambda-scale">
            {LAMBDAS.map((lambda) => (
              <span key={lambda}>
                {lambda.toLocaleString("vi-VN", { minimumFractionDigits: 1 })}
              </span>
            ))}
          </div>
        </div>
        <div className="home-scenario-results">
          <div className="home-curve">
            <div className="home-kpi-label">{vi.home.scenario.curve}</div>
            <svg
              className="home-curve-svg"
              viewBox="0 0 200 72"
              preserveAspectRatio="none"
              role="img"
              aria-label={vi.home.scenario.curveAria}
            >
              <line x1="0" y1="71" x2="200" y2="71" stroke="var(--color-divider)" strokeWidth="1" />
              <line
                x1="0"
                y1="36"
                x2="200"
                y2="36"
                stroke="var(--color-divider)"
                strokeWidth="1"
                strokeDasharray="3 3"
              />
              <polyline
                points={view.curvePoints}
                fill="none"
                stroke="var(--color-accent-700)"
                strokeWidth="1.6"
                vectorEffect="non-scaling-stroke"
              />
              <circle
                cx={view.marker.x}
                cy={view.marker.y}
                r="3.4"
                fill="var(--color-accent-700)"
              />
            </svg>
          </div>
          <div className="home-figures">
            <div>
              <div className="home-kpi-label">{vi.home.scenario.weeklyCost}</div>
              <div className="home-figure-value">{view.cost}</div>
            </div>
            <div>
              <div className="home-kpi-label">{vi.home.scenario.shortHours}</div>
              <div className="home-figure-value">{view.shortHours}</div>
            </div>
            <div className="home-figure-note">{vi.home.scenario.note}</div>
          </div>
        </div>
      </div>
    </div>
  );
}
