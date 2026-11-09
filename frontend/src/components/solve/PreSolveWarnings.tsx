import { useQuery } from "@tanstack/react-query";
import { apiFetch, jsonInit } from "../../lib/api-client";
import { useDebounced } from "../../lib/debounce";
import { vi } from "../../locales/vi";
import type { PreSolveWarningRead, PreviewWarningsRead, SolveRequest } from "../../types/models";
import { Notice } from "../ui/Feedback";

const PREVIEW_DELAY_MS = 400;

function usePreviewWarnings(body: SolveRequest | null) {
  return useQuery({
    queryKey: ["schedules", "preview-warnings", body],
    queryFn: () =>
      apiFetch<PreviewWarningsRead>("/schedules/preview-warnings", jsonInit("POST", body)),
    enabled: body !== null,
  });
}

function warningText(warning: PreSolveWarningRead): string {
  switch (warning.kind) {
    case "no_available_days":
      return vi.solve.warnings.noAvailableDays(warning.employee_id ?? "");
    case "capacity_below_demand":
      return vi.solve.warnings.capacityBelowDemand;
    case "no_night_shift":
      return vi.solve.warnings.noNightShift;
  }
}

export function PreSolveWarnings({ body }: { body: SolveRequest | null }) {
  const key = body === null ? "" : JSON.stringify(body);
  const settledKey = useDebounced(key, PREVIEW_DELAY_MS);
  const settled = settledKey === "" ? null : (JSON.parse(settledKey) as SolveRequest);
  const preview = usePreviewWarnings(settled);
  const warnings = preview.data?.warnings ?? [];
  if (warnings.length === 0) {
    return null;
  }
  return (
    <Notice kind="warning" title={vi.solve.warnings.title}>
      <ul className="notice-list">
        {warnings.map((warning) => (
          <li key={`${warning.kind}-${warning.employee_id ?? ""}`}>{warningText(warning)}</li>
        ))}
      </ul>
    </Notice>
  );
}
