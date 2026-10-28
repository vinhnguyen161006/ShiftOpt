import { Slider } from "../../../components/ui/Slider";

type LambdaSliderProps = {
  multipliers: number[];
  index: number;
  onChange: (index: number) => void;
};

export function LambdaSlider({ multipliers, index, onChange }: LambdaSliderProps) {
  const value = multipliers[index] ?? 1;
  return (
    <Slider
      id="lambda"
      label="Demand multiplier lambda"
      min={0}
      max={Math.max(0, multipliers.length - 1)}
      step={1}
      value={index}
      valueText={`${value.toFixed(1)}x demand`}
      ticks={multipliers.map((multiplier) => multiplier.toFixed(1))}
      onChange={onChange}
    />
  );
}
