const LOCALE = "vi-VN";

export function formatDecimal(value: number, digits: number): string {
  return value.toLocaleString(LOCALE, {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

export function formatPercent(ratio: number, digits: number): string {
  return `${formatDecimal(ratio * 100, digits)}%`;
}
