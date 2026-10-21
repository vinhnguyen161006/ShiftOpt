import type { KpiRead } from "../../../types/models";

type CoverageChartProps = {
  kpi: KpiRead;
};

export function CoverageChart({ kpi }: CoverageChartProps) {
  return (
    <p className="todo">
      TODO: bars = staff_by_hour, line = required_by_hour over 168 hours; red where understaffed,
      green where overstaffed. Charting library per docs/adr. Coverage {kpi.coverage_ratio}.
    </p>
  );
}
