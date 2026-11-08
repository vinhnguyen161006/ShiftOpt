import { Table } from "../../../components/ui/Table";
import { vi } from "../../../locales/vi";
import type { BaselineCompareResult, BaselineRow } from "../../../types/models";

type BaselineCompareProps = {
  result: BaselineCompareResult;
  analysisId: number;
};

function methodLabel(method: BaselineRow["method"]): string {
  return method === "cpsat" ? vi.whatIf.baselineView.cpsat : vi.whatIf.baselineView.greedy;
}

function cost(value: number | null): string {
  return value === null ? "-" : Math.round(value).toLocaleString("vi-VN");
}

export function BaselineCompare({ result, analysisId }: BaselineCompareProps) {
  return (
    <div className="form-stack">
      <p className="muted">{vi.whatIf.baselineView.sameCoverage}</p>
      <Table
        caption={vi.whatIf.baselineView.caption(analysisId)}
        rows={result.points}
        rowKey={(row) => row.method}
        columns={[
          {
            key: "method",
            label: vi.whatIf.baselineView.method,
            render: (row) => methodLabel(row.method),
          },
          {
            key: "status",
            label: vi.whatIf.baselineView.status,
            render: (row) => vi.schedule.solveStatus[row.solve_status] ?? row.solve_status,
          },
          {
            key: "cost",
            label: vi.whatIf.baselineView.cost,
            align: "end",
            render: (row) => cost(row.labor_cost),
          },
          {
            key: "understaffed",
            label: vi.whatIf.baselineView.understaffed,
            align: "end",
            render: (row) => row.understaffed_hours ?? "-",
          },
          {
            key: "staffed",
            label: vi.whatIf.baselineView.staffed,
            align: "end",
            render: (row) => row.staffed_hours ?? "-",
          },
        ]}
      />
    </div>
  );
}
