export const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
export const DAY_NAMES = [
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday",
  "Sunday",
];
export const HOURS_PER_DAY = 24;
export const HOURS_PER_WEEK = DAYS.length * HOURS_PER_DAY;
export const HOURS = Array.from({ length: HOURS_PER_DAY }, (_, hour) => hour);

export function formatHour(hour: number): string {
  return `${String(hour % HOURS_PER_DAY).padStart(2, "0")}:00`;
}

export function hourOfWeekLabel(hourOfWeek: number): string {
  const day = Math.floor(hourOfWeek / HOURS_PER_DAY);
  return `${DAYS[day]} ${formatHour(hourOfWeek % HOURS_PER_DAY)}`;
}

export function shiftSpan(startHour: number, length: number): string {
  const end = startHour + length;
  const nextDay = end > HOURS_PER_DAY ? " (+1 day)" : "";
  return `${formatHour(startHour)}-${formatHour(end)}${nextDay}`;
}

export function dayList(days: number[]): string {
  return days.length === 0 ? "None" : days.map((day) => DAYS[day]).join(", ");
}
