import { Table } from "../../../components/ui/Table";
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
    label: "Coverage ratio",
    value: (side) => side.kpi?.coverage_ratio ?? null,
    format: (value) => `${(value * 100).toFixed(1)}%`,
  },
  {
    label: "Understaffed hours",
    value: (side) => side.kpi?.understaffed_hours ?? null,
    format: (value) => `${value} h`,
  },
  {
    label: "Overstaffed hours",
    value: (side) => side.kpi?.overstaffed_hours ?? null,
    format: (value) => `${value} h`,
  },
  {
    label: "Labor cost",
    value: (side) => (side.kpi ? side.kpi.labor_cost / COST_SCALE : null),
    format: (value) => value.toLocaleString("en-US", { maximumFractionDigits: 2 }),
  },
  {
    label: "Night allowance",
    value: (side) => (side.kpi ? side.kpi.night_premium_cost / COST_SCALE : null),
    format: (value) => value.toLocaleString("en-US", { maximumFractionDigits: 2 }),
  },
  {
    label: "Hard violations",
    value: (side) => side.run.hard_violations,
    format: (value) => String(value),
  },
  {
    label: "Gap",
    value: (side) => side.run.gap,
    format: (value) => `${(value * 100).toFixed(2)}%`,
  },
  {
    label: "Wall time",
    value: (side) => side.run.wall_time_seconds,
    format: (value) => `${value.toFixed(1)} s`,
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
  return difference === 0 ? "same" : `${sign}${metric.format(difference)}`;
}

function verdict(run: SolveRunRead): string {
  if (run.solver === "manual") {
    return "manual edit";
  }
  return run.solve_status === "optimal"
    ? "OPTIMAL"
    : (run.solve_status ?? run.status).toUpperCase();
}

type Row = { label: string; baseline: string; scenario: string; change: string };

export function ScenarioCompare({ baseline, scenario }: ScenarioCompareProps) {
  const rows: Row[] = [
    {
      label: "Solver result",
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
      caption={`Run ${baseline.run.id} compared with run ${scenario.run.id}`}
      rows={rows}
      rowKey={(row) => row.label}
      columns={[
        { key: "metric", label: "Metric", render: (row) => row.label },
        {
          key: "baseline",
          label: `Run ${baseline.run.id}`,
          align: "end",
          render: (row) => row.baseline,
        },
        {
          key: "scenario",
          label: `Run ${scenario.run.id}`,
          align: "end",
          render: (row) => row.scenario,
        },
        { key: "change", label: "Change", align: "end", render: (row) => row.change },
      ]}
    />
  );
}
