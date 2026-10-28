import { HOURS, HOURS_PER_DAY } from "../../../lib/time";

type ShiftStripProps = {
  startHour: number;
  length: number;
  nightStart: number;
  nightEnd: number;
};

function covers(hour: number, startHour: number, length: number): boolean {
  return (hour - startHour + HOURS_PER_DAY) % HOURS_PER_DAY < length;
}

function inNightWindow(hour: number, nightStart: number, nightEnd: number): boolean {
  return hour >= nightStart || hour < nightEnd;
}

export function ShiftStrip({ startHour, length, nightStart, nightEnd }: ShiftStripProps) {
  return (
    <span className="shift-strip" aria-hidden="true">
      {HOURS.map((hour) => {
        const worked = covers(hour, startHour, length);
        const night = inNightWindow(hour, nightStart, nightEnd);
        const className = ["shift-strip-hour", worked ? "is-worked" : "", night ? "is-night" : ""]
          .filter(Boolean)
          .join(" ");
        return <span key={hour} className={className} />;
      })}
    </span>
  );
}
