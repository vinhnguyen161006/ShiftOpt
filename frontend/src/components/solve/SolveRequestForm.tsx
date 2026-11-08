import { toNumber } from "../../lib/form";
import { shiftSpan } from "../../lib/time";
import { vi } from "../../locales/vi";
import type {
  DemandProfileRead,
  LaborRulesRead,
  ShiftTemplateRead,
  SolveRequest,
} from "../../types/models";
import { Field } from "../ui/Field";

export type SolveDraft = {
  demandProfileId: string;
  shiftTemplateIds: number[];
  timeLimitSeconds: string;
  relativeGapLimit: string;
  numWorkers: string;
  randomSeed: string;
  maxWeeklyHours: string;
  maxConsecutiveDays: string;
  costTolerance: string;
};

export function initialDraft(rules?: LaborRulesRead): SolveDraft {
  return {
    demandProfileId: "",
    shiftTemplateIds: [],
    timeLimitSeconds: "60",
    relativeGapLimit: "0.01",
    numWorkers: "8",
    randomSeed: "0",
    maxWeeklyHours: rules ? String(rules.max_weekly_hours) : "",
    maxConsecutiveDays: rules ? String(rules.max_consecutive_days) : "",
    costTolerance: "0",
  };
}

export function toSolveRequest(draft: SolveDraft): SolveRequest {
  return {
    demand_profile_id: toNumber(draft.demandProfileId),
    shift_template_ids: draft.shiftTemplateIds,
    employee_ids: null,
    time_limit_seconds: toNumber(draft.timeLimitSeconds),
    relative_gap_limit: toNumber(draft.relativeGapLimit),
    num_workers: toNumber(draft.numWorkers),
    random_seed: toNumber(draft.randomSeed),
    max_weekly_hours: toNumber(draft.maxWeeklyHours),
    max_consecutive_days: toNumber(draft.maxConsecutiveDays),
    cost_tolerance_percent: toNumber(draft.costTolerance),
  };
}

export const SOLVE_FIELD_IDS: Record<string, string> = {
  demand_profile_id: "solve-profile",
  shift_template_ids: "solve-templates",
  time_limit_seconds: "solve-time-limit",
  relative_gap_limit: "solve-gap",
  num_workers: "solve-workers",
  random_seed: "solve-seed",
  max_weekly_hours: "solve-weekly-hours",
  max_consecutive_days: "solve-consecutive-days",
  cost_tolerance_percent: "solve-cost-tolerance",
};

type SolveRequestFormProps = {
  draft: SolveDraft;
  onChange: (draft: SolveDraft) => void;
  profiles: DemandProfileRead[];
  templates: ShiftTemplateRead[];
  employeeCount: number;
  errors: Map<string, string>;
  prefix?: string;
};

type NumberSetting = {
  key: keyof SolveDraft;
  path: string;
  label: string;
  hint: string;
  step: string;
};

const SETTINGS: NumberSetting[] = [
  { key: "timeLimitSeconds", path: "time_limit_seconds", ...vi.solve.timeLimit, step: "any" },
  { key: "relativeGapLimit", path: "relative_gap_limit", ...vi.solve.gap, step: "any" },
  { key: "numWorkers", path: "num_workers", ...vi.solve.workers, step: "1" },
  { key: "randomSeed", path: "random_seed", ...vi.solve.seed, step: "1" },
  { key: "maxWeeklyHours", path: "max_weekly_hours", ...vi.solve.weeklyHours, step: "1" },
  {
    key: "maxConsecutiveDays",
    path: "max_consecutive_days",
    ...vi.solve.consecutiveDays,
    step: "1",
  },
  {
    key: "costTolerance",
    path: "cost_tolerance_percent",
    ...vi.solve.costTolerance,
    step: "0.5",
  },
];

export function SolveRequestForm({
  draft,
  onChange,
  profiles,
  templates,
  employeeCount,
  errors,
  prefix = "",
}: SolveRequestFormProps) {
  const fieldId = (path: string) => `${prefix}${SOLVE_FIELD_IDS[path]}`;

  function toggleTemplate(templateId: number) {
    const selected = draft.shiftTemplateIds.includes(templateId)
      ? draft.shiftTemplateIds.filter((item) => item !== templateId)
      : [...draft.shiftTemplateIds, templateId];
    onChange({ ...draft, shiftTemplateIds: selected });
  }

  return (
    <div className="form-stack">
      <div className="form-grid">
        <Field
          id={fieldId("demand_profile_id")}
          label={vi.solve.profile}
          error={errors.get("demand_profile_id")}
        >
          {(control) => (
            <select
              {...control}
              className="input"
              value={draft.demandProfileId}
              onChange={(event) => onChange({ ...draft, demandProfileId: event.target.value })}
            >
              <option value="">{vi.solve.chooseProfile}</option>
              {profiles.map((profile) => (
                <option key={profile.id} value={profile.id}>
                  {profile.name}
                </option>
              ))}
            </select>
          )}
        </Field>
        <div className="field">
          <span className="field-label-static">{vi.solve.employees}</span>
          <span className="solve-employees">{vi.solve.allEmployees(employeeCount)}</span>
        </div>
      </div>
      <fieldset className="field" id={fieldId("shift_template_ids")} tabIndex={-1}>
        <legend>{vi.solve.templates}</legend>
        {errors.get("shift_template_ids") && (
          <span className="field-error">
            <span className="visually-hidden">{vi.common.errorPrefix}</span>
            {errors.get("shift_template_ids")}
          </span>
        )}
        <div className="seg">
          {templates.map((template) => (
            <label key={template.id} className="seg-opt">
              <input
                type="checkbox"
                checked={draft.shiftTemplateIds.includes(template.id)}
                onChange={() => toggleTemplate(template.id)}
              />
              {template.name}
              <span className="seg-meta">
                {shiftSpan(template.start_hour, template.length_hours)}
              </span>
            </label>
          ))}
        </div>
      </fieldset>
      <details
        className="data-details"
        open={SETTINGS.some((setting) => errors.has(setting.path)) || undefined}
      >
        <summary>{vi.solve.settings}</summary>
        <div className="form-grid solve-settings">
          {SETTINGS.map((setting) => (
            <Field
              key={setting.key}
              id={fieldId(setting.path)}
              label={setting.label}
              hint={setting.hint}
              error={errors.get(setting.path)}
            >
              {(control) => (
                <input
                  {...control}
                  className="input"
                  type="number"
                  min={0}
                  step={setting.step}
                  value={draft[setting.key] as string}
                  onChange={(event) => onChange({ ...draft, [setting.key]: event.target.value })}
                />
              )}
            </Field>
          ))}
        </div>
      </details>
    </div>
  );
}
