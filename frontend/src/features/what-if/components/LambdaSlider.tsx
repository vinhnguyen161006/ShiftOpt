import { Slider } from "../../../components/ui/Slider";
import { formatDecimal } from "../../../lib/number";
import { vi } from "../../../locales/vi";

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
      label={vi.whatIf.sweep.sliderLabel}
      min={0}
      max={Math.max(0, multipliers.length - 1)}
      step={1}
      value={index}
      valueText={vi.whatIf.sweep.sliderValue(formatDecimal(value, 1))}
      ticks={multipliers.map((multiplier) => formatDecimal(multiplier, 1))}
      onChange={onChange}
    />
  );
}
