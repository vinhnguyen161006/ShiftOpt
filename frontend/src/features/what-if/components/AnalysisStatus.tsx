import type { ReactNode } from "react";
import { Loading, Notice } from "../../../components/ui/Feedback";
import type { AnalysisRunRead } from "../../../types/models";

type AnalysisStatusProps = {
  run: AnalysisRunRead;
  activeLabel: string;
  children: ReactNode;
};

export function AnalysisStatus({ run, activeLabel, children }: AnalysisStatusProps) {
  if (run.status === "queued" || run.status === "running") {
    return <Loading label={activeLabel} />;
  }
  if (run.status === "failed") {
    return (
      <Notice kind="error" title={`Analysis ${run.id} failed`}>
        {run.error ?? "The analysis did not finish."}
      </Notice>
    );
  }
  return <>{children}</>;
}
