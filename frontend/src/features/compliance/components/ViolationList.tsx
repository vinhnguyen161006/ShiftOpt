import type { ComplianceRead } from "../../../types/models";

type ViolationListProps = {
  compliance: ComplianceRead;
};

export function ViolationList({ compliance }: ViolationListProps) {
  return (
    <p className="todo">
      TODO: violations grouped by kind with the labor code article (105, 110, 111), employee and
      detail; an explicit "0 hard violations" state. Count {compliance.violations.length}.
    </p>
  );
}
