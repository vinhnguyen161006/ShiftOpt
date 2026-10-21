type DemandGridEditorProps = {
  value: number[];
  onChange: (value: number[]) => void;
};

export function DemandGridEditor({ value, onChange }: DemandGridEditorProps) {
  return (
    <p className="todo">
      TODO: editable 7 x 24 grid (rows = days, columns = hours) of non-negative integers; keep
      exactly 168 cells; CSV import; paste a row. Cells: {value.length}.
    </p>
  );
}
