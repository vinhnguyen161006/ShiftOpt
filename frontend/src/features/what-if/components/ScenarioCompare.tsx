import { Table } from "../../../components/ui/Table";
import { formatDecimal, formatPercent } from "../../../lib/number";
import { vi } from "../../../locales/vi";
import type { KpiRead, SolveRunRead } from "../../../types/models";

export type ScenarioSide = {
  run: SolveRunRead;
  kpi: KpiRead | undefined;
};

type ScenarioCompareProps = {
  baseline: ScenarioSide;
  scenario: ScenarioSide;
};

type Metric = {
  label: string;
  value: (side: ScenarioSide) => number | null;
  format: (value: number) => string;
};

const COST_SCALE = 100;

const METRICS: Metric[] = [
  {
    label: vi.whatIf.compare.coverage,
    value: (side) => side.kpi?.coverage_ratio ?? null,
    format: (value) => formatPercent(value, 1),
  },
  {
    label: vi.whatIf.compare.understaffed,
    value: (side) => side.kpi?.understaffed_hours ?? null,
    format: (value) => vi.home.sample.hours(value),
  },
  {
    label: vi.whatIf.compare.overstaffed,
    value: (side) => side.kpi?.overstaffed_hours ?? null,
    format: (value) => vi.home.sample.hours(value),
  },
  {
    label: vi.whatIf.compare.laborCost,
    value: (side) => (side.kpi ? side.kpi.labor_cost / COST_SCALE : null),
    format: (value) => value.toLocaleString("vi-VN", { maximumFractionDigits: 2 }),
  },
  {
    label: vi.whatIf.compare.night,
    value: (side) => (side.kpi ? side.kpi.night_premium_cost / COST_SCALE : null),
    format: (value) => value.toLocaleString("vi-VN", { maximumFractionDigits: 2 }),
  },
  {
    label: vi.whatIf.compare.hard,
    value: (side) => side.run.hard_violations,
    format: (value) => String(value),
  },
  {
    label: vi.whatIf.compare.gap,
    value: (side) => side.run.gap,
    format: (value) => formatPercent(value, 2),
  },
  {
    label: vi.whatIf.compare.wallTime,
    value: (side) => side.run.wall_time_seconds,
    format: (value) => vi.schedule.workspace.seconds(formatDecimal(value, 1)),
  },
];

function show(metric: Metric, side: ScenarioSide): string {
  const value = metric.value(side);
  return value === null ? "-" : metric.format(value);
}

function delta(metric: Metric, baseline: ScenarioSide, scenario: ScenarioSide): string {
  const before = metric.value(baseline);
  const after = metric.value(scenario);
  if (before === null || after === null) {
    return "-";
  }
  const difference = after - before;
  const sign = difference > 0 ? "+" : "";
  return difference === 0 ? vi.whatIf.compare.same : `${sign}${metric.format(difference)}`;
}

function verdict(run: SolveRunRead): string {
  if (run.solver === "manual") {
    return vi.whatIf.compare.manualEdit;
  }
  return run.solve_status === "optimal"
    ? "OPTIMAL"
    : (run.solve_status ?? run.status).toUpperCase();
}

type Row = { label: string; baseline: string; scenario: string; change: string };

export function ScenarioCompare({ baseline, scenario }: ScenarioCompareProps) {
  const rows: Row[] = [
    {
      label: vi.whatIf.compare.solverResult,
      baseline: verdict(baseline.run),
      scenario: verdict(scenario.run),
      change: "",
    },
    ...METRICS.map((metric) => ({
      label: metric.label,
      baseline: show(metric, baseline),
      scenario: show(metric, scenario),
      change: delta(metric, baseline, scenario),
    })),
  ];
  return (
    <Table
      caption={vi.whatIf.compare.caption(baseline.run.id, scenario.run.id)}
      rows={rows}
      rowKey={(row) => row.label}
      columns={[
        { key: "metric", label: vi.whatIf.compare.metric, render: (row) => row.label },
        {
          key: "baseline",
          label: vi.whatIf.compare.run(baseline.run.id),
          align: "end",
          render: (row) => row.baseline,
        },
        {
          key: "scenario",
          label: vi.whatIf.compare.run(scenario.run.id),
          align: "end",
          render: (row) => row.scenario,
        },
        {
          key: "change",
          label: vi.whatIf.compare.change,
          align: "end",
          render: (row) => row.change,
        },
      ]}
    />
  );
}
