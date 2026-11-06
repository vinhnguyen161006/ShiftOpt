import { vi } from "../../../locales/vi";
import { SUMMARY } from "../sample-data";
import { ScenarioPanel } from "./ScenarioPanel";

const TEXT = vi.home.analytics;

const TILES = [
  { ...TEXT.tiles.coverage, value: SUMMARY.coverage },
  { ...TEXT.tiles.under, value: SUMMARY.shortHours },
  { ...TEXT.tiles.over, value: SUMMARY.overHours },
  { ...TEXT.tiles.cost, value: SUMMARY.cost },
];

export function Analytics() {
  return (
    <section id="analytics" className="home-analytics">
      <div className="container home-split">
        <div className="home-analytics-copy">
          <div className="home-eyebrow">{TEXT.eyebrow}</div>
          <h2 className="home-section-title home-analytics-title">{TEXT.title}</h2>
          <p className="home-analytics-text">{TEXT.text}</p>
          <p className="home-analytics-text home-analytics-text-last">{TEXT.textLast}</p>
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
            <div className="home-callout-title">{TEXT.calloutTitle}</div>
            <p className="home-callout-text">{TEXT.calloutText}</p>
          </div>
        </div>
        <ScenarioPanel />
      </div>
    </section>
  );
}
