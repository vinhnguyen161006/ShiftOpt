import type { KpiRead } from "../../../types/models";

type CostSummaryProps = {
  kpi: KpiRead;
};

export function CostSummary({ kpi }: CostSummaryProps) {
  return (
    <p className="todo">
      TODO: total labor cost, night premium share and labor cost percent. Cost {kpi.labor_cost}.
    </p>
  );
}
