import { buttonClass } from "../../../components/ui/Button";
import { KpiStrip } from "../../../components/ui/Layout";
import { formatDecimal, formatPercent } from "../../../lib/number";
import { vi } from "../../../locales/vi";
import type { KpiRead } from "../../../types/models";
import { exportUrl } from "../api/schedules";

export function ScheduleKpis({ kpi }: { kpi: KpiRead }) {
  return (
    <KpiStrip
      items={[
        {
          label: vi.schedule.kpis.coverage,
          value: formatPercent(kpi.coverage_ratio, 1),
          sub: vi.schedule.kpis.coverageSub,
        },
        {
          label: vi.schedule.kpis.under,
          value: vi.home.sample.hours(kpi.understaffed_hours),
          sub: vi.schedule.kpis.underSub,
        },
        {
          label: vi.schedule.kpis.over,
          value: vi.home.sample.hours(kpi.overstaffed_hours),
          sub: vi.schedule.kpis.overSub,
        },
        {
          label: vi.schedule.kpis.efficiency,
          value: formatPercent(kpi.schedule_efficiency, 1),
          sub: vi.schedule.kpis.efficiencySub,
        },
        {
          label: vi.schedule.kpis.nightSpread,
          value: formatDecimal(kpi.night_shift_stddev, 2),
          sub: vi.schedule.kpis.nightSpreadSub(formatDecimal(kpi.weekend_shift_stddev, 2)),
        },
        {
          label: vi.schedule.kpis.hoursSpread,
          value: vi.home.sample.hours(kpi.hours_spread),
          sub: vi.schedule.kpis.hoursSpreadSub,
        },
      ]}
    />
  );
}

const EXPORTS = [
  { kind: "assignments", label: vi.schedule.exports.assignments },
  { kind: "coverage", label: vi.schedule.exports.coverage },
  { kind: "kpi", label: vi.schedule.exports.kpi },
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
