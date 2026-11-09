import { Loading, Notice } from "../../../components/ui/Feedback";
import { Table } from "../../../components/ui/Table";
import { errorMessage } from "../../../lib/api-client";
import { DAY_NAMES, formatHour } from "../../../lib/time";
import { vi } from "../../../locales/vi";
import type { ShortfallHourRead, SolveRunRead } from "../../../types/models";
import { useShortfall } from "../api/compliance";

type ShortfallExplanationProps = {
  run: SolveRunRead;
};

function reasonText(reason: ShortfallHourRead["reasons"][number]): string {
  const kind = vi.compliance.kinds[reason.kind] ?? reason.kind;
  const basis = vi.compliance.basis[reason.legal_basis] ?? reason.legal_basis;
  return vi.compliance.shortfall.count(kind, basis, reason.employees);
}

export function ShortfallExplanation({ run }: ShortfallExplanationProps) {
  const shortfall = useShortfall(run.id, true);
  if (shortfall.isPending) {
    return <Loading label={vi.compliance.shortfall.loading} />;
  }
  if (shortfall.isError) {
    return <Notice kind="error" title={errorMessage(shortfall.error)} />;
  }
  const rows = shortfall.data;
  const hasFree = rows.some((row) => row.free_employee_codes.length > 0);
  return (
    <div className="form-stack">
      <p className="muted">{vi.compliance.shortfall.intro}</p>
      {hasFree && <Notice kind="warning" title={vi.compliance.shortfall.freeNotice} />}
      <Table
        caption={vi.compliance.shortfall.caption}
        rows={rows}
        rowKey={(row) => row.hour}
        columns={[
          {
            key: "hour",
            label: vi.compliance.shortfall.hour,
            render: (row) => `${DAY_NAMES[row.day]} ${formatHour(row.hour_of_day)}`,
          },
          {
            key: "missing",
            label: vi.compliance.shortfall.missing,
            align: "end",
            render: (row) => row.shortfall,
          },
          {
            key: "reasons",
            label: vi.compliance.shortfall.reasons,
            render: (row) =>
              row.uncoverable
                ? vi.compliance.shortfall.uncoverable
                : row.reasons.map(reasonText).join("; ") || vi.compliance.shortfall.none,
          },
          {
            key: "free",
            label: vi.compliance.shortfall.free,
            render: (row) =>
              row.free_employee_codes.length > 0
                ? row.free_employee_codes.join(", ")
                : vi.compliance.shortfall.none,
          },
        ]}
      />
    </div>
  );
}
