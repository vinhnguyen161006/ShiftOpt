import type { Bar } from "../sample-data";

export function StaffingBars({ bars, size }: { bars: Bar[]; size: "preview" | "scenario" }) {
  return (
    <>
      <div className={`home-bars home-bars-${size}`}>
        {bars.map((bar) => (
          <div key={bar.hour} className="home-bar">
            <div className="home-bar-assigned" style={{ height: bar.assignedPx }} />
            <div
              className="home-bar-deficit"
              style={{ bottom: bar.assignedPx, height: bar.deficitPx }}
            />
            <div className="home-bar-required" style={{ bottom: bar.requiredPx }} />
          </div>
        ))}
      </div>
      <div className={size === "scenario" ? "home-ticks home-ticks-spaced" : "home-ticks"}>
        {bars.map((bar) => (
          <div key={bar.hour} className="home-tick">
            {bar.tick}
          </div>
        ))}
      </div>
    </>
  );
}
