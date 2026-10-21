type SliderProps = {
  id: string;
  label: string;
  min: number;
  max: number;
  step: number;
  value: number;
  onChange: (value: number) => void;
};

export function Slider({ id, label, min, max, step, value, onChange }: SliderProps) {
  return (
    <p className="todo">
      TODO: labeled range input "{label}" from {min} to {max} step {step}, value {value}.
    </p>
  );
}
