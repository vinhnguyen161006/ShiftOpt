import type { Bar } from "../sample-data";

export function StaffingBars({ bars }: { bars: Bar[] }) {
  return (
    <>
      <div className="home-bars home-bars-preview">
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
      <div className="home-ticks">
        {bars.map((bar) => (
          <div key={bar.hour} className="home-tick">
            {bar.tick}
          </div>
        ))}
      </div>
    </>
  );
}
