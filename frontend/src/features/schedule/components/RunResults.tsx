import { buttonClass } from "../../../components/ui/Button";
import { KpiStrip } from "../../../components/ui/Layout";
import type { KpiRead } from "../../../types/models";
import { exportUrl } from "../api/schedules";

export function ScheduleKpis({ kpi }: { kpi: KpiRead }) {
  return (
    <KpiStrip
      items={[
        {
          label: "Coverage ratio",
          value: `${(kpi.coverage_ratio * 100).toFixed(1)}%`,
          sub: "min(staff, required) / required",
        },
        { label: "Understaffed", value: `${kpi.understaffed_hours} h`, sub: "staff-hours short" },
        { label: "Overstaffed", value: `${kpi.overstaffed_hours} h`, sub: "staff-hours over" },
        {
          label: "Efficiency",
          value: `${(kpi.schedule_efficiency * 100).toFixed(1)}%`,
          sub: "required / staffed",
        },
        {
          label: "Night shift spread",
          value: kpi.night_shift_stddev.toFixed(2),
          sub: `std dev; weekend ${kpi.weekend_shift_stddev.toFixed(2)}`,
        },
      ]}
    />
  );
}

const EXPORTS = [
  { kind: "assignments", label: "Roster CSV" },
  { kind: "coverage", label: "Coverage CSV" },
  { kind: "kpi", label: "KPI CSV" },
] as const;

export function ExportLinks({ runId }: { runId: number }) {
  return (
    <span className="tag-row">
      {EXPORTS.map((item) => (
        <a
          key={item.kind}
          className={buttonClass("secondary", "sm")}
          href={exportUrl(runId, item.kind)}
          download
        >
          {item.label}
        </a>
      ))}
    </span>
  );
}
