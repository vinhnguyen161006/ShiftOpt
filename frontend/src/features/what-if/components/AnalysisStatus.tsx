import type { ReactNode } from "react";
import { Loading, Notice } from "../../../components/ui/Feedback";
import { vi } from "../../../locales/vi";
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
      <Notice kind="error" title={vi.whatIf.status.failedTitle(run.id)}>
        {run.error ?? vi.whatIf.status.failedBody}
      </Notice>
    );
  }
  return <>{children}</>;
}
