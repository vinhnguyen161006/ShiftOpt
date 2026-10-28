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

export const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const DAY_FULL = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
const DAY_MULT = [0.86, 0.86, 0.9, 0.95, 1.0, 1.1, 1.04];
const BASE_DEMAND = [0, 0, 0, 0, 0, 0, 4, 5, 6, 6, 9, 11, 12, 12, 12, 12, 11, 9, 7, 6, 5, 4, 0, 0];
const NIGHT_MIN_STAFF = 3;

export const SCENARIO_CAPTION =
  "Store 1284, demand derived from FreshRetailNet-50K hourly sales (alpha 1.0, p 42, r_min 3).";

const SHIFTS: Record<ShiftCode, ShiftLook> = {
  E: {
    label: "E",
    name: "Early",
    span: "06:00-14:00",
    start: 6,
    bg: "var(--color-accent-200)",
    fg: "var(--color-accent-900)",
    bd: "var(--color-accent-300)",
    bs: "solid",
  },
  D: {
    label: "D",
    name: "Day",
    span: "10:00-18:00",
    start: 10,
    bg: "var(--color-accent-400)",
    fg: "var(--color-accent-900)",
    bd: "var(--color-accent-500)",
    bs: "solid",
  },
  L: {
    label: "L",
    name: "Late",
    span: "14:00-22:00",
    start: 14,
    bg: "var(--color-accent-600)",
    fg: "var(--color-neutral-100)",
    bd: "var(--color-accent-700)",
    bs: "solid",
  },
  N: {
    label: "N",
    name: "Night",
    span: "22:00-06:00",
    start: 22,
    bg: "var(--color-accent-900)",
    fg: "var(--color-neutral-200)",
    bd: "var(--color-accent-900)",
    bs: "solid",
  },
  O: {
    label: "",
    name: "Off",
    span: "",
    start: null,
    bg: "transparent",
    fg: "var(--color-neutral-500)",
    bd: "var(--color-divider)",
    bs: "dashed",
  },
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
const CONTRACTS = [
  "Nights",
  "Rotating",
  "Full-time",
  "Full-time",
  "Part-time",
  "Full-time",
  "Full-time",
  "Full-time",
  "Full-time",
  "Full-time",
];
const NAMES = [
  "M. Alvarez",
  "J. Okafor",
  "L. Fontaine",
  "S. Rahman",
  "K. Nowak",
  "T. Brennan",
  "P. Iyer",
  "R. Castillo",
  "H. Lindqvist",
  "D. Moreau",
  "A. Haddad",
  "N. Petrova",
  "C. Mbeki",
  "V. Duarte",
  "E. Kowalski",
  "B. Aoki",
  "G. Rossi",
  "F. Delgado",
  "W. Mensah",
  "O. Sandberg",
  "Y. Tanaka",
  "Z. Mahmud",
  "Q. Trinh",
  "I. Barros",
  "U. Erdem",
  "X. Chen",
  "J. Adeyemi",
  "R. Kovacs",
  "S. Thibault",
  "L. Marchetti",
];

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
  return `$${Math.round(value).toLocaleString("en-US")}`;
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

const SEPARATOR = `  ${String.fromCodePoint(0xb7)}  `;

export const SUMMARY = {
  coverage: `${coveragePercent().toFixed(1)}%`,
  cost: money(WEEKLY_COST),
  shortHours: `${countHours(REQUIRED, (staffed, need) => staffed < need)} h`,
  overHours: `${countHours(REQUIRED, (staffed, need) => staffed > need)} h`,
  rosterCaption: [
    `${ROSTER.length} employees`,
    `${TOTAL_SHIFTS} assigned shifts`,
    `${(TOTAL_SHIFTS * SHIFT_HOURS).toLocaleString("en-US")} h`,
  ].join(SEPARATOR),
  rosterMore: `+ ${ROSTER.length - VISIBLE_ROWS} more employees in this run`,
};

function describe(shift: ShiftLook): string {
  return shift.span ? `${shift.name} ${shift.span}` : shift.name;
}

export const ROSTER_ROWS: RosterRow[] = ROSTER.slice(0, VISIBLE_ROWS).map((employee) => ({
  name: employee.name,
  contract: employee.contract,
  cells: employee.days.map((look, day) => ({
    day: DAYS[day],
    look,
    title: `${DAY_FULL[day]} - ${describe(look)}`,
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
    lambdaLabel: `${LAMBDAS[lambdaIndex].toFixed(1)}x`,
    bars: bars(required[SCENARIO_DAY], ASSIGNED[SCENARIO_DAY], SCENARIO_CHART_HEIGHT),
    curvePoints: CURVE_POINTS.map((point) => `${point.x},${point.y}`).join(" "),
    marker: CURVE_POINTS[lambdaIndex],
    cost: money(CURVE_VALUES[lambdaIndex]),
    shortHours: `${countHours(required, (staffed, need) => staffed < need)} h`,
  };
}
