import type { ReactNode } from "react";

export type ControlProps = {
  id: string;
  "aria-describedby"?: string;
  "aria-invalid"?: boolean;
};

type FieldProps = {
  id: string;
  label: string;
  hint?: ReactNode;
  error?: string;
  children: (control: ControlProps) => ReactNode;
};

export function Field({ id, label, hint, error, children }: FieldProps) {
  const hintId = hint ? `${id}-hint` : undefined;
  const errorId = error ? `${id}-error` : undefined;
  const describedBy = [hintId, errorId].filter(Boolean).join(" ") || undefined;
  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      {hint && (
        <span id={hintId} className="field-hint">
          {hint}
        </span>
      )}
      {error && (
        <span id={errorId} className="field-error">
          <span className="visually-hidden">Error:</span>
          {error}
        </span>
      )}
      {children({ id, "aria-describedby": describedBy, "aria-invalid": error ? true : undefined })}
    </div>
  );
}
