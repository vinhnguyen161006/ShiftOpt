import type { ReactNode } from "react";
import { Corners } from "./Corners";

type PageHeaderProps = {
  eyebrow: string;
  title: string;
  lead?: ReactNode;
  actions?: ReactNode;
};

export function PageHeader({ eyebrow, title, lead, actions }: PageHeaderProps) {
  return (
    <header className="page-header">
      <div className="page-header-copy">
        <div className="eyebrow">{eyebrow}</div>
        <h1 className="page-title">{title}</h1>
        {lead && <p className="page-lead">{lead}</p>}
      </div>
      {actions && <div className="page-actions">{actions}</div>}
    </header>
  );
}

type PanelProps = {
  title: string;
  aside?: ReactNode;
  children: ReactNode;
  labelledBy?: string;
};

export function Panel({ title, aside, children, labelledBy }: PanelProps) {
  return (
    <section className="blueprint panel" aria-labelledby={labelledBy}>
      <Corners />
      <div className="panel-head">
        <h2 id={labelledBy} className="panel-title">
          {title}
        </h2>
        {aside && <div className="panel-aside">{aside}</div>}
      </div>
      <div className="panel-body">{children}</div>
    </section>
  );
}

export type KpiItem = {
  label: string;
  value: string;
  sub?: string;
};

export function KpiStrip({ items }: { items: KpiItem[] }) {
  return (
    <dl className="kpi-strip">
      {items.map((item) => (
        <div key={item.label} className="kpi">
          <dt className="label-caps">{item.label}</dt>
          <dd className="kpi-value">{item.value}</dd>
          {item.sub && <dd className="kpi-sub">{item.sub}</dd>}
        </div>
      ))}
    </dl>
  );
}
