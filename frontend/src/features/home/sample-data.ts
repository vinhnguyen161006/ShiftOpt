import { vi } from "../../locales/vi";

type ShiftCode = "E" | "D" | "L" | "N" | "O";

export interface ShiftLook {
  label: string;
  name: string;
  span: string;
  start: number | null;
  bg: string;
  fg: string;
  bd: string;
  bs: "solid" | "dashed";
}

export interface Bar {
  hour: number;
  tick: string;
  assignedPx: number;
  deficitPx: number;
  requiredPx: number;
}

export interface RosterCell {
  day: string;
  look: ShiftLook;
  title: string;
}

export interface RosterRow {
  name: string;
  contract: string;
  cells: RosterCell[];
}

export const DAYS = vi.time.days;
const DAY_FULL = vi.time.dayNames;
const DAY_MULT = [0.86, 0.86, 0.9, 0.95, 1.0, 1.1, 1.04];
const BASE_DEMAND = [0, 0, 0, 0, 0, 0, 4, 5, 6, 6, 9, 11, 12, 12, 12, 12, 11, 9, 7, 6, 5, 4, 0, 0];
const NIGHT_MIN_STAFF = 3;

export const SCENARIO_CAPTION = vi.home.scenario.caption;

function look(
  code: ShiftCode,
  span: string,
  start: number | null,
  colors: [string, string, string],
  bs: "solid" | "dashed" = "solid",
): ShiftLook {
  return {
    label: vi.home.sample.shiftLabels[code],
    name: vi.home.sample.shiftNames[code],
    span,
    start,
    bg: colors[0],
    fg: colors[1],
    bd: colors[2],
    bs,
  };
}

const SHIFTS: Record<ShiftCode, ShiftLook> = {
  E: look("E", "06:00-14:00", 6, [
    "var(--color-accent-200)",
    "var(--color-accent-900)",
    "var(--color-accent-300)",
  ]),
  D: look("D", "10:00-18:00", 10, [
    "var(--color-accent-400)",
    "var(--color-accent-900)",
    "var(--color-accent-500)",
  ]),
  L: look("L", "14:00-22:00", 14, [
    "var(--color-accent-600)",
    "var(--color-neutral-100)",
    "var(--color-accent-700)",
  ]),
  N: look("N", "22:00-06:00", 22, [
    "var(--color-accent-900)",
    "var(--color-neutral-200)",
    "var(--color-accent-900)",
  ]),
  O: look(
    "O",
    "",
    null,
    ["transparent", "var(--color-neutral-500)", "var(--color-divider)"],
    "dashed",
  ),
};

const PATTERNS = [
  "NNNOONN",
  "DDLNNOO",
  "EEEOEEO",
  "EOEEOEE",
  "OEOEEOE",
  "DODDODD",
  "ODDODDD",
  "LLLDDOO",
  "OLOLLLL",
  "LOOLLLL",
];
const { nights, rotating, fullTime, partTime } = vi.home.sample.contracts;
const CONTRACTS = [
  nights,
  rotating,
  fullTime,
  fullTime,
  partTime,
  fullTime,
  fullTime,
  fullTime,
  fullTime,
  fullTime,
];
const EMPLOYEE_COUNT = 30;
const NAMES = Array.from(
  { length: EMPLOYEE_COUNT },
  (_, index) => `E${String(index + 1).padStart(2, "0")}`,
);

const VISIBLE_ROWS = 10;
const SHIFT_HOURS = 8;
const WAGE = 7.5;
const NIGHT_ALLOWANCE = 0.3;
const NIGHT_FROM = 22;
const NIGHT_TO = 6;
const HOURS_PER_DAY = 24;
const TICK_EVERY = 3;
const COST_FACTORS = [0.86, 0.93, 1.0, 1.11, 1.235, 1.385];
const CURVE_LEFT = 6;
const CURVE_WIDTH = 188;
const CURVE_BOTTOM = 64;
const CURVE_HEIGHT = 56;

export const LAMBDAS = [0.8, 0.9, 1.0, 1.1, 1.2, 1.3];
export const DEFAULT_DAY = 5;
export const DEFAULT_LAMBDA_INDEX = 2;
const PREVIEW_CHART_HEIGHT = 120;
const SCENARIO_CHART_HEIGHT = 132;
const SCENARIO_DAY = 5;

function shiftOf(code: string): ShiftLook {
  if (code in SHIFTS) {
    return SHIFTS[code as ShiftCode];
  }
  throw new Error(`unknown shift code ${code}`);
}

const ROSTER = NAMES.map((name, index) => ({
  name,
  contract: CONTRACTS[index % PATTERNS.length],
  days: [...PATTERNS[index % PATTERNS.length]].map(shiftOf),
}));

function isNight(hour: number): boolean {
  return hour >= NIGHT_FROM || hour < NIGHT_TO;
}

function requiredGrid(lambda: number): number[][] {
  return DAYS.map((_, day) =>
    BASE_DEMAND.map((base, hour) => {
      const raw = isNight(hour) ? 0 : Math.ceil(base * DAY_MULT[day] * lambda);
      return Math.max(NIGHT_MIN_STAFF, raw);
    }),
  );
}

function assignedGrid(): number[][] {
  const grid = DAYS.map(() => new Array<number>(HOURS_PER_DAY).fill(0));
  for (const employee of ROSTER) {
    employee.days.forEach((shift, day) => {
      if (shift.start === null) {
        return;
      }
      for (let offset = 0; offset < SHIFT_HOURS; offset++) {
        const hour = shift.start + offset;
        const target = hour >= HOURS_PER_DAY ? (day + 1) % DAYS.length : day;
        grid[target][hour % HOURS_PER_DAY] += 1;
      }
    });
  }
  return grid;
}

function weeklyCost(): number {
  let shifts = 0;
  let nightHours = 0;
  for (const employee of ROSTER) {
    for (const shift of employee.days) {
      if (shift.start === null) {
        continue;
      }
      shifts += 1;
      for (let offset = 0; offset < SHIFT_HOURS; offset++) {
        if (isNight((shift.start + offset) % HOURS_PER_DAY)) {
          nightHours += 1;
        }
      }
    }
  }
  return shifts * SHIFT_HOURS * WAGE + nightHours * WAGE * NIGHT_ALLOWANCE;
}

function money(value: number): string {
  return `$${Math.round(value).toLocaleString("vi-VN")}`;
}

function bars(required: number[], assigned: number[], height: number): Bar[] {
  const peak = Math.max(1, ...required, ...assigned);
  const unit = height / (peak + 1);
  return required.map((need, hour) => {
    const staffed = assigned[hour];
    return {
      hour,
      tick: hour % TICK_EVERY === 0 ? String(hour).padStart(2, "0") : "",
      assignedPx: Math.round(staffed * unit),
      deficitPx: Math.round(Math.max(0, need - staffed) * unit),
      requiredPx: Math.round(need * unit),
    };
  });
}

function countHours(required: number[][], test: (staffed: number, need: number) => boolean) {
  let hours = 0;
  required.forEach((row, day) => {
    row.forEach((need, hour) => {
      if (test(ASSIGNED[day][hour], need)) {
        hours += 1;
      }
    });
  });
  return hours;
}

const ASSIGNED = assignedGrid();
const REQUIRED = requiredGrid(1);
const WEEKLY_COST = weeklyCost();

function coveragePercent(): number {
  let covered = 0;
  let needed = 0;
  REQUIRED.forEach((row, day) => {
    row.forEach((need, hour) => {
      covered += Math.min(ASSIGNED[day][hour], need);
      needed += need;
    });
  });
  return (covered / needed) * 100;
}

const TOTAL_SHIFTS = ROSTER.reduce(
  (total, employee) => total + employee.days.filter((shift) => shift.start !== null).length,
  0,
);

export const SUMMARY = {
  coverage: `${coveragePercent().toLocaleString("vi-VN", { maximumFractionDigits: 1 })}%`,
  cost: money(WEEKLY_COST),
  shortHours: vi.home.sample.hours(countHours(REQUIRED, (staffed, need) => staffed < need)),
  overHours: vi.home.sample.hours(countHours(REQUIRED, (staffed, need) => staffed > need)),
  rosterCaption: vi.home.sample.rosterCaption(
    ROSTER.length,
    TOTAL_SHIFTS,
    (TOTAL_SHIFTS * SHIFT_HOURS).toLocaleString("vi-VN"),
  ),
  rosterMore: vi.home.sample.rosterMore(ROSTER.length - VISIBLE_ROWS),
};

function describe(shift: ShiftLook): string {
  return shift.span ? `${shift.name} ${shift.span}` : shift.name;
}

export const ROSTER_ROWS: RosterRow[] = ROSTER.slice(0, VISIBLE_ROWS).map((employee) => ({
  name: employee.name,
  contract: employee.contract,
  cells: employee.days.map((shift, day) => ({
    day: DAYS[day],
    look: shift,
    title: `${DAY_FULL[day]} - ${describe(shift)}`,
  })),
}));

export const LEGEND = (["E", "D", "L", "N", "O"] as const).map((code) => ({
  label: describe(SHIFTS[code]),
  look: SHIFTS[code],
}));

export function dayBars(day: number): Bar[] {
  return bars(REQUIRED[day], ASSIGNED[day], PREVIEW_CHART_HEIGHT);
}

const CURVE_VALUES = COST_FACTORS.map((factor) => WEEKLY_COST * factor);
const CURVE_LOW = Math.min(...CURVE_VALUES);
const CURVE_HIGH = Math.max(...CURVE_VALUES);
const CURVE_POINTS = CURVE_VALUES.map((value, index) => ({
  x: Math.round((CURVE_LEFT + (index / (LAMBDAS.length - 1)) * CURVE_WIDTH) * 10) / 10,
  y:
    Math.round(
      (CURVE_BOTTOM - ((value - CURVE_LOW) / (CURVE_HIGH - CURVE_LOW || 1)) * CURVE_HEIGHT) * 10,
    ) / 10,
}));

export function scenarioView(lambdaIndex: number) {
  const required = requiredGrid(LAMBDAS[lambdaIndex]);
  return {
    lambdaLabel: `${LAMBDAS[lambdaIndex].toLocaleString("vi-VN", { minimumFractionDigits: 1 })}x`,
    bars: bars(required[SCENARIO_DAY], ASSIGNED[SCENARIO_DAY], SCENARIO_CHART_HEIGHT),
    curvePoints: CURVE_POINTS.map((point) => `${point.x},${point.y}`).join(" "),
    marker: CURVE_POINTS[lambdaIndex],
    cost: money(CURVE_VALUES[lambdaIndex]),
    shortHours: vi.home.sample.hours(countHours(required, (staffed, need) => staffed < need)),
  };
}
