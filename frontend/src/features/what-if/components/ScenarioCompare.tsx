import type { SolveRunRead } from "../../../types/models";

type ScenarioCompareProps = {
  baseline: SolveRunRead;
  scenario: SolveRunRead;
};

export function ScenarioCompare({ baseline, scenario }: ScenarioCompareProps) {
  return (
    <p className="todo">
      TODO: side by side coverage, understaffed hours, labor cost, gap and wall time with a delta
      column. Runs {baseline.id} and {scenario.id}.
    </p>
  );
}
