import { useState } from "react";
import { Field } from "../../../components/ui/Field";
import { KpiStrip } from "../../../components/ui/Layout";
import { toNumber } from "../../../lib/form";
import type { KpiRead } from "../../../types/models";
import "../schedule.css";

type CostSummaryProps = {
  kpi: KpiRead;
};

const COST_SCALE = 100;

function money(hundredths: number): string {
  return (hundredths / COST_SCALE).toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

export function CostSummary({ kpi }: CostSummaryProps) {
  const [revenue, setRevenue] = useState("");
  const revenueValue = toNumber(revenue);
  const base = kpi.labor_cost - kpi.night_premium_cost;
  const share =
    revenueValue > 0 ? `${((kpi.labor_cost / COST_SCALE / revenueValue) * 100).toFixed(1)}%` : "-";
  return (
    <div className="form-stack">
      <KpiStrip
        items={[
          { label: "Labor cost", value: money(kpi.labor_cost), sub: "wages + night allowance" },
          { label: "Base wages", value: money(base), sub: "hours x hourly wage" },
          {
            label: "Night allowance",
            value: money(kpi.night_premium_cost),
            sub: "Article 98, hours 22:00-06:00",
          },
          { label: "Labor cost share", value: share, sub: "of the assumed weekly revenue" },
        ]}
      />
      <div className="form-grid cost-assumption">
        <Field
          id="cost-revenue"
          label="Assumed weekly revenue (team assumption)"
          hint="Only used for the labor cost share. Same currency as the hourly wages."
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
