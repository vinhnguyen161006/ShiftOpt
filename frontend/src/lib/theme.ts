export type Theme = "light" | "dark";

export const THEME_STORAGE_KEY = "shiftopt-theme";
const DARK_QUERY = "(prefers-color-scheme: dark)";

function isTheme(value: unknown): value is Theme {
  return value === "light" || value === "dark";
}

export function readStoredTheme(): Theme | null {
  try {
    const stored = window.localStorage.getItem(THEME_STORAGE_KEY);
    return isTheme(stored) ? stored : null;
  } catch {
    return null;
  }
}

export function storeTheme(theme: Theme): void {
  try {
    window.localStorage.setItem(THEME_STORAGE_KEY, theme);
  } catch {
    return;
  }
}

export function systemTheme(): Theme {
  return window.matchMedia(DARK_QUERY).matches ? "dark" : "light";
}

export function currentTheme(): Theme {
  const applied = document.documentElement.dataset.theme;
  return isTheme(applied) ? applied : (readStoredTheme() ?? systemTheme());
}

export function applyTheme(theme: Theme): void {
  document.documentElement.dataset.theme = theme;
}

export function watchSystemTheme(onChange: (theme: Theme) => void): () => void {
  const query = window.matchMedia(DARK_QUERY);
  const listener = () => {
    if (readStoredTheme() === null) {
      onChange(systemTheme());
    }
  };
  query.addEventListener("change", listener);
  return () => query.removeEventListener("change", listener);
}
