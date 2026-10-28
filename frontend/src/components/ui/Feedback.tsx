import { type ReactNode, useEffect, useId, useRef } from "react";

type NoticeKind = "info" | "success" | "warning" | "error";

const NOTICE_ICONS: Record<NoticeKind, ReactNode> = {
  info: "i",
  success: <>&#10003;</>,
  warning: "!",
  error: "!",
};

const NOTICE_LABELS: Record<NoticeKind, string> = {
  info: "Information",
  success: "Done",
  warning: "Warning",
  error: "Error",
};

type NoticeProps = {
  kind?: NoticeKind;
  title: string;
  children?: ReactNode;
};

export function Notice({ kind = "info", title, children }: NoticeProps) {
  return (
    <div className={`notice notice-${kind}`} role={kind === "error" ? "alert" : "status"}>
      <span className="notice-icon" aria-hidden="true">
        {NOTICE_ICONS[kind]}
      </span>
      <div className="notice-title">
        <span className="visually-hidden">{NOTICE_LABELS[kind]}: </span>
        {title}
      </div>
      {children && <div className="notice-body">{children}</div>}
    </div>
  );
}

export type SummaryError = { fieldId: string; message: string };

export function ErrorSummary({ errors }: { errors: SummaryError[] }) {
  const ref = useRef<HTMLDivElement>(null);
  const titleId = useId();
  useEffect(() => {
    if (errors.length > 0) {
      ref.current?.focus();
    }
  }, [errors]);
  if (errors.length === 0) {
    return null;
  }
  return (
    <div ref={ref} className="error-summary" role="alert" tabIndex={-1} aria-labelledby={titleId}>
      <h2 id={titleId}>There is a problem</h2>
      <ul>
        {errors.map((error) => (
          <li key={`${error.fieldId}-${error.message}`}>
            <a
              href={`#${error.fieldId}`}
              onClick={(event) => {
                event.preventDefault();
                document.getElementById(error.fieldId)?.focus();
              }}
            >
              {error.message}
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
}

type EmptyStateProps = {
  title: string;
  children: ReactNode;
  action?: ReactNode;
};

export function EmptyState({ title, children, action }: EmptyStateProps) {
  return (
    <div className="empty-state">
      <div className="empty-state-title">{title}</div>
      <p className="empty-state-body">{children}</p>
      {action}
    </div>
  );
}

export function Loading({ label }: { label: string }) {
  return (
    <span className="loading" role="status">
      <span className="loading-bar" aria-hidden="true" />
      {label}
    </span>
  );
}
