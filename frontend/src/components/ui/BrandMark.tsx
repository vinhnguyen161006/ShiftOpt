export function BrandMark({ light = false }: { light?: boolean }) {
  return (
    <span className={light ? "brand-mark brand-mark-light" : "brand-mark"}>
      <span className="brand-mark-bar brand-mark-bar-1" />
      <span className="brand-mark-bar brand-mark-bar-2" />
      <span className="brand-mark-bar brand-mark-bar-3" />
    </span>
  );
}

export function Wordmark() {
  return (
    <span className="wordmark">
      Shift<span className="wordmark-accent">Opt</span>
    </span>
  );
}
