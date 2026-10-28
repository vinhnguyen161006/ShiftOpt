import { DAY_NAMES, DAYS } from "../../lib/time";

type DayPickerProps = {
  id: string;
  legend: string;
  hint?: string;
  error?: string;
  value: number[];
  onChange: (days: number[]) => void;
};

export function DayPicker({ id, legend, hint, error, value, onChange }: DayPickerProps) {
  function toggle(day: number) {
    onChange(
      value.includes(day)
        ? value.filter((item) => item !== day)
        : [...value, day].sort((a, b) => a - b),
    );
  }
  return (
    <fieldset className="field" id={id}>
      <legend>{legend}</legend>
      {hint && <span className="field-hint">{hint}</span>}
      {error && (
        <span className="field-error">
          <span className="visually-hidden">Error:</span>
          {error}
        </span>
      )}
      <div className="seg">
        {DAYS.map((day, index) => (
          <label key={day} className="seg-opt" title={DAY_NAMES[index]}>
            <input
              type="checkbox"
              checked={value.includes(index)}
              onChange={() => toggle(index)}
              aria-label={DAY_NAMES[index]}
            />
            {day}
          </label>
        ))}
      </div>
    </fieldset>
  );
}
