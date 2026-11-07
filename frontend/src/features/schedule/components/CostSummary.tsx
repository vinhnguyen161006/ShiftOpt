import { useState } from "react";
import { Field } from "../../../components/ui/Field";
import { KpiStrip } from "../../../components/ui/Layout";
import { toNumber } from "../../../lib/form";
import type { KpiRead } from "../../../types/models";
import "../schedule.css";
import { formatPercent } from "../../../lib/number";
import { vi } from "../../../locales/vi";

type CostSummaryProps = {
  kpi: KpiRead;
};

const COST_SCALE = 100;

function money(hundredths: number): string {
  return (hundredths / COST_SCALE).toLocaleString("vi-VN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

export function CostSummary({ kpi }: CostSummaryProps) {
  const [revenue, setRevenue] = useState("");
  const revenueValue = toNumber(revenue);
  const base = kpi.labor_cost - kpi.night_premium_cost;
  const share =
    revenueValue > 0 ? formatPercent(kpi.labor_cost / COST_SCALE / revenueValue, 1) : "-";
  return (
    <div className="form-stack">
      <KpiStrip
        items={[
          {
            label: vi.schedule.cost.laborCost,
            value: money(kpi.labor_cost),
            sub: vi.schedule.cost.laborCostSub,
          },
          { label: vi.schedule.cost.base, value: money(base), sub: vi.schedule.cost.baseSub },
          {
            label: vi.schedule.cost.night,
            value: money(kpi.night_premium_cost),
            sub: vi.schedule.cost.nightSub,
          },
          { label: vi.schedule.cost.share, value: share, sub: vi.schedule.cost.shareSub },
        ]}
      />
      <div className="form-grid cost-assumption">
        <Field
          id="cost-revenue"
          label={vi.schedule.cost.revenue}
          hint={vi.schedule.cost.revenueHint}
        >
          {(control) => (
            <input
              {...control}
              className="input"
              type="number"
              min={0}
              step="any"
              value={revenue}
              onChange={(event) => setRevenue(event.target.value)}
            />
          )}
        </Field>
      </div>
    </div>
  );
}
