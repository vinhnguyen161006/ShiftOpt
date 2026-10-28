type SliderProps = {
  id: string;
  label: string;
  min: number;
  max: number;
  step: number;
  value: number;
  valueText: string;
  ticks?: string[];
  onChange: (value: number) => void;
};

export function Slider({
  id,
  label,
  min,
  max,
  step,
  value,
  valueText,
  ticks = [],
  onChange,
}: SliderProps) {
  return (
    <div className="slider">
      <label htmlFor={id} className="slider-label">
        {label}
        <span className="slider-value">{valueText}</span>
      </label>
      <input
        id={id}
        className="slider-input"
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        aria-valuetext={valueText}
        onChange={(event) => onChange(Number(event.target.value))}
      />
      {ticks.length > 0 && (
        <div className="slider-ticks" aria-hidden="true">
          {ticks.map((tick) => (
            <span key={tick}>{tick}</span>
          ))}
        </div>
      )}
    </div>
  );
}
