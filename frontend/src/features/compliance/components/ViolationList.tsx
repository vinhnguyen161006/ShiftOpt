import { Notice } from "../../../components/ui/Feedback";
import { Table } from "../../../components/ui/Table";
import { DAY_NAMES } from "../../../lib/time";
import type { ComplianceRead, ViolationRead } from "../../../types/models";
import "../compliance.css";

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
  return kind.replaceAll("_", " ");
}

export function ViolationList({ compliance }: ViolationListProps) {
  if (compliance.violations.length === 0) {
    return (
      <Notice kind="success" title="0 hard violations">
        The independent validator re-checked this schedule against every hard rule (Articles 105,
        109, 110 and 111, consecutive working days, availability) and found nothing.
      </Notice>
    );
  }
  const groups = groupViolations(compliance.violations);
  return (
    <div className="form-stack">
      <Notice kind="error" title={`${compliance.violations.length} hard violations`}>
        This schedule breaks hard rules and is not compliant. Each group below names the rule and
        the people affected.
      </Notice>
      {groups.map((group) => (
        <section
          key={group.key}
          className="violation-group"
          aria-label={`${group.legalBasis} ${kindLabel(group.kind)}`}
        >
          <h3 className="violation-title">
            <span className="tag tag-strong">{group.legalBasis}</span>
            <span>{kindLabel(group.kind)}</span>
            <span className="muted">{group.violations.length}</span>
          </h3>
          <Table
            caption={`${group.legalBasis}: ${kindLabel(group.kind)}`}
            rows={group.violations}
            rowKey={(violation) =>
              `${violation.employee_code}-${violation.day}-${violation.detail}`
            }
            columns={[
              {
                key: "employee",
                label: "Employee",
                render: (violation) => violation.employee_code,
              },
              {
                key: "day",
                label: "Day",
                render: (violation) =>
                  violation.day === null || violation.day === undefined
                    ? "Week"
                    : DAY_NAMES[violation.day],
              },
              { key: "detail", label: "Detail", render: (violation) => violation.detail },
            ]}
          />
        </section>
      ))}
    </div>
  );
}
