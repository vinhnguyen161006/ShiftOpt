import { Field } from "../../../components/ui/Field";
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
  {
    key: "alpha",
    label: "alpha (de-normalization)",
    hint: "Scales the normalized sales index back to units.",
    step: "any",
  },
  {
    key: "productivity",
    label: "p (units per employee-hour)",
    hint: "How much load one person handles in an hour.",
    step: "any",
  },
  {
    key: "min_staff",
    label: "Day floor (min staff)",
    hint: "Head count never goes below this outside the night window.",
    step: "1",
  },
  {
    key: "night_min_staff",
    label: "Night floor (22:00-06:00)",
    hint: "Night hours are not derived from sales; this fixed floor applies.",
    step: "1",
  },
];

export function conversionFieldId(key: string): string {
  return `conversion-${key}`;
}

export function ConversionParamsForm({ value, onChange, errors }: ConversionParamsFormProps) {
  return (
    <fieldset className="field conversion-form">
      <legend>Team assumptions (not dataset facts)</legend>
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
