import { Notice } from "../../../components/ui/Feedback";
import { Table } from "../../../components/ui/Table";
import { DAY_NAMES } from "../../../lib/time";
import type { ComplianceRead, ViolationRead } from "../../../types/models";
import "../compliance.css";
import { vi } from "../../../locales/vi";

type ViolationListProps = {
  compliance: ComplianceRead;
};

type Group = {
  key: string;
  legalBasis: string;
  kind: string;
  violations: ViolationRead[];
};

function groupViolations(violations: ViolationRead[]): Group[] {
  const groups = new Map<string, Group>();
  for (const violation of violations) {
    const key = `${violation.legal_basis}|${violation.kind}`;
    const group = groups.get(key) ?? {
      key,
      legalBasis: violation.legal_basis,
      kind: violation.kind,
      violations: [],
    };
    group.violations.push(violation);
    groups.set(key, group);
  }
  return [...groups.values()].sort((a, b) => b.violations.length - a.violations.length);
}

function kindLabel(kind: string): string {
  return vi.compliance.kinds[kind] ?? kind.replaceAll("_", " ");
}

function basisLabel(basis: string): string {
  return vi.compliance.basis[basis] ?? basis;
}

export function ViolationList({ compliance }: ViolationListProps) {
  if (compliance.violations.length === 0) {
    return (
      <Notice kind="success" title={vi.compliance.noneTitle}>
        {vi.compliance.noneBody}
      </Notice>
    );
  }
  const groups = groupViolations(compliance.violations);
  return (
    <div className="form-stack">
      <Notice kind="error" title={vi.compliance.someTitle(compliance.violations.length)}>
        {vi.compliance.someBody}
      </Notice>
      {groups.map((group) => (
        <section
          key={group.key}
          className="violation-group"
          aria-label={`${basisLabel(group.legalBasis)} ${kindLabel(group.kind)}`}
        >
          <h3 className="violation-title">
            <span className="tag tag-strong">{basisLabel(group.legalBasis)}</span>
            <span>{kindLabel(group.kind)}</span>
            <span className="muted">{group.violations.length}</span>
          </h3>
          <Table
            caption={`${basisLabel(group.legalBasis)}: ${kindLabel(group.kind)}`}
            rows={group.violations}
            rowKey={(violation) =>
              `${violation.employee_code}-${violation.day}-${violation.detail}`
            }
            columns={[
              {
                key: "employee",
                label: vi.compliance.employee,
                render: (violation) => violation.employee_code,
              },
              {
                key: "day",
                label: vi.compliance.day,
                render: (violation) =>
                  violation.day === null || violation.day === undefined
                    ? vi.compliance.week
                    : DAY_NAMES[violation.day],
              },
              {
                key: "detail",
                label: vi.compliance.detail,
                render: (violation) => violation.detail,
              },
            ]}
          />
        </section>
      ))}
    </div>
  );
}
