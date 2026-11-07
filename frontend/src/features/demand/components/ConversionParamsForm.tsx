import { Field } from "../../../components/ui/Field";
import { vi } from "../../../locales/vi";
import type { ConversionParams } from "../../../types/models";

type ConversionParamsFormProps = {
  value: Required<ConversionParams>;
  onChange: (value: Required<ConversionParams>) => void;
  errors: Map<string, string>;
};

const FIELDS: {
  key: keyof ConversionParams;
  label: string;
  hint: string;
  step: string;
}[] = [
  { key: "alpha", ...vi.demand.conversion.alpha, step: "any" },
  { key: "productivity", ...vi.demand.conversion.productivity, step: "any" },
  { key: "min_staff", ...vi.demand.conversion.min_staff, step: "1" },
  { key: "night_min_staff", ...vi.demand.conversion.night_min_staff, step: "1" },
];

export function conversionFieldId(key: string): string {
  return `conversion-${key}`;
}

export function ConversionParamsForm({ value, onChange, errors }: ConversionParamsFormProps) {
  return (
    <fieldset className="field conversion-form">
      <legend>{vi.demand.conversion.legend}</legend>
      <div className="form-grid">
        {FIELDS.map((field) => (
          <Field
            key={field.key}
            id={conversionFieldId(field.key)}
            label={field.label}
            hint={field.hint}
            error={errors.get(`conversion_params.${field.key}`)}
          >
            {(control) => (
              <input
                {...control}
                className="input"
                type="number"
                min={0}
                step={field.step}
                value={String(value[field.key])}
                onChange={(event) =>
                  onChange({ ...value, [field.key]: Number(event.target.value) })
                }
              />
            )}
          </Field>
        ))}
      </div>
    </fieldset>
  );
}
