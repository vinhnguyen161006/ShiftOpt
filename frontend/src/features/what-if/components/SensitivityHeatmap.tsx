type SensitivityHeatmapProps = {
  marginalCostByHour: (number | null)[];
};

export function SensitivityHeatmap({ marginalCostByHour }: SensitivityHeatmapProps) {
  return (
    <p className="todo">
      TODO: 7 x 24 heatmap of z(r + e_t) - z(r); hover shows day, hour and cost; cells from
      non-optimal solves are hatched. Cells {marginalCostByHour.length}.
    </p>
  );
}
