type LambdaSliderProps = {
  value: number;
  onChange: (lambda: number) => void;
};

export function LambdaSlider({ value, onChange }: LambdaSliderProps) {
  return (
    <p className="todo">
      TODO: demand multiplier slider from 0.8 to 1.3 step 0.1 with the matching point of the
      z(lambda) curve. Current {value}.
    </p>
  );
}
