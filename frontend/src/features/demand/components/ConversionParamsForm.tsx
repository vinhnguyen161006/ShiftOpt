type ConversionParams = {
  alpha: number;
  productivity: number;
  min_staff: number;
  night_min_staff: number;
};

type ConversionParamsFormProps = {
  value: ConversionParams;
  onChange: (value: ConversionParams) => void;
};

export function ConversionParamsForm({ value, onChange }: ConversionParamsFormProps) {
  return (
    <p className="todo">
      TODO: inputs for alpha, productivity, day floor and night floor, labeled as team assumptions
      (not dataset facts). Current alpha {value.alpha}.
    </p>
  );
}
