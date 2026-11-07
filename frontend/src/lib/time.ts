import { vi } from "../locales/vi";

export const DAYS = vi.time.days;
export const DAY_NAMES = vi.time.dayNames;
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
  const nextDay = end > HOURS_PER_DAY ? vi.time.nextDay : "";
  return `${formatHour(startHour)}-${formatHour(end)}${nextDay}`;
}

export function dayList(days: number[]): string {
  return days.length === 0 ? vi.time.none : days.map((day) => DAYS[day]).join(", ");
}
