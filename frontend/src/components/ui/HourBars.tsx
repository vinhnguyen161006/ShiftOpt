import { formatHour } from "../../lib/time";
import { vi } from "../../locales/vi";

export type HourBar = {
  hour: number;
  assigned: number;
  required: number;
};

type HourBarsProps = {
  bars: HourBar[];
  height: number;
  label: string;
  peak?: number;
  spaced?: boolean;
  dayLabel?: string;
};

const TICK_EVERY = 3;

function status(bar: HourBar): string {
  const gap = bar.assigned - bar.required;
  if (gap < 0) {
    return vi.hourBars.short(-gap);
  }
  return gap > 0 ? vi.hourBars.over(gap) : vi.hourBars.exact;
}

function describe(bar: HourBar, dayLabel: string | undefined): string {
  const prefix = dayLabel ? `${dayLabel} ` : "";
  return vi.hourBars.describe(
    prefix,
    formatHour(bar.hour),
    bar.required,
    bar.assigned,
    status(bar),
  );
}

export function HourBars({ bars, height, label, peak, spaced = false, dayLabel }: HourBarsProps) {
  const top = peak ?? Math.max(1, ...bars.map((bar) => Math.max(bar.assigned, bar.required)));
  const unit = height / (top + 1);
  return (
    <>
      <div className="hour-bars" style={{ height }} role="img" aria-label={label}>
        {bars.map((bar) => {
          const assigned = bar.assigned * unit;
          const deficit = Math.max(0, bar.required - bar.assigned) * unit;
          return (
            <div key={bar.hour} className="hour-bar" title={describe(bar, dayLabel)}>
              <div className="hour-bar-assigned" style={{ height: assigned }} />
              <div className="hour-bar-deficit" style={{ bottom: assigned, height: deficit }} />
              <div className="hour-bar-required" style={{ bottom: bar.required * unit }} />
            </div>
          );
        })}
      </div>
      <div className={spaced ? "hour-ticks hour-ticks-spaced" : "hour-ticks"} aria-hidden="true">
        {bars.map((bar) => (
          <div key={bar.hour} className="hour-tick">
            {bar.hour % TICK_EVERY === 0 ? String(bar.hour).padStart(2, "0") : ""}
          </div>
        ))}
      </div>
    </>
  );
}
