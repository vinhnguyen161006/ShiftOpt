import type { ReactNode } from "react";
import { Corners } from "../../../components/ui/Corners";

const ICON_STROKE = "var(--color-accent-700)";

function Icon({ children }: { children: ReactNode }) {
  return (
    <svg
      width="26"
      height="26"
      viewBox="0 0 24 24"
      fill="none"
      stroke={ICON_STROKE}
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {children}
    </svg>
  );
}

const FEATURES = [
  {
    title: "Demand Planning",
    body: (
      <>
        Edit hourly staffing requirements in a 7 &times; 24 grid, import a CSV, or derive an
        illustrative demand profile from FreshRetailNet-50K.
      </>
    ),
    icon: (
      <>
        <rect x="3" y="3" width="18" height="18" />
        <path d="M9 3v18M15 3v18M3 9h18M3 15h18" />
      </>
    ),
  },
  {
    title: "Employee Management",
    body: "Define availability, contractual hour limits, shift preferences and day-off requests, and keep them attached to the instance that was solved.",
    icon: (
      <>
        <circle cx="9" cy="8" r="3.2" />
        <path d="M3 20v-1.5A4.5 4.5 0 0 1 7.5 14h3A4.5 4.5 0 0 1 15 18.5V20" />
        <path d="M16 5.2a3.2 3.2 0 0 1 0 5.6M18.5 14A4.5 4.5 0 0 1 22 18.4V20" />
      </>
    ),
  },
  {
    title: "Automated Scheduling",
    body: "Submit an instance and let the optimization engine assign employees to shifts under the documented scheduling constraints.",
    icon: (
      <>
        <rect x="7" y="7" width="10" height="10" />
        <path d="M10 3v4M14 3v4M10 17v4M14 17v4M3 10h4M3 14h4M17 10h4M17 14h4" />
      </>
    ),
  },
  {
    title: "Coverage Analytics",
    body: "Compare required staffing against assigned employees hour by hour, and read understaffed and overstaffed hours straight off the chart.",
    icon: (
      <>
        <path d="M3 20h18" />
        <rect x="5" y="11" width="3.4" height="7" />
        <rect x="10.3" y="7" width="3.4" height="11" />
        <rect x="15.6" y="13" width="3.4" height="5" />
        <path d="M4 8.5l5-4 5 3 6-5" strokeDasharray="2.5 2" />
      </>
    ),
  },
  {
    title: "Labor Cost Analysis",
    body: "See estimated labor cost under your configured wage assumptions, including the night-shift allowance applied to hours between 22:00 and 06:00.",
    icon: (
      <>
        <circle cx="12" cy="12" r="8.5" />
        <path d="M12 7v10M14.8 9.4c-.6-.8-1.6-1.2-2.8-1.2-1.7 0-2.8.8-2.8 2 0 2.8 5.6 1.4 5.6 4.2 0 1.2-1.1 2-2.8 2-1.2 0-2.2-.4-2.8-1.2" />
      </>
    ),
  },
  {
    title: "Sensitivity Analysis",
    body: (
      <>
        Sweep a demand multiplier, compare scenarios, and read the per-hour marginal cost of one
        more unit of demand &mdash; each point a real re-solve.
      </>
    ),
    icon: (
      <>
        <path d="M4 7h16M4 12h16M4 17h16" />
        <circle cx="9" cy="7" r="2.1" fill="var(--color-bg)" />
        <circle cx="15.5" cy="12" r="2.1" fill="var(--color-bg)" />
        <circle cx="7.5" cy="17" r="2.1" fill="var(--color-bg)" />
      </>
    ),
  },
];

const PRODUCT_POINTS = [
  {
    label: <>Demand &rarr; staffing</>,
    key: "demand",
    text: (
      <>
        Hourly load becomes a required-staff curve through a conversion you control:{" "}
        <span className="home-formula">r = max(r_min, ceil(alpha &middot; D / p))</span>.
      </>
    ),
  },
  {
    label: "Integer programming",
    key: "integer",
    text: "Set-covering and per-employee rostering models solved with CP-SAT and HiGHS, benchmarked on the same instance.",
  },
  {
    label: "Re-solved sensitivity",
    key: "sensitivity",
    text: "Marginal cost per hour comes from solving again, not from a shadow price an integer model cannot supply.",
  },
];

export function ProductStrip() {
  return (
    <section id="product" className="home-product">
      <div className="container home-product-grid">
        {PRODUCT_POINTS.map((point) => (
          <div key={point.key} className="home-min-0">
            <div className="home-product-label">{point.label}</div>
            <p className="home-product-text">{point.text}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

export function Features() {
  return (
    <section id="features" className="home-features">
      <div className="container">
        <div className="home-section-intro">
          <div className="home-eyebrow">Capabilities</div>
          <h2 className="home-section-title">Everything You Need to Build Better Schedules</h2>
          <p className="home-section-lead">
            Six working areas, one instance. Demand, workforce and rules go in; a schedule, its KPIs
            and its scenario analysis come out.
          </p>
        </div>
        <div className="home-feature-grid">
          {FEATURES.map((feature) => (
            <article key={feature.title} className="card blueprint home-feature-card">
              <Corners />
              <Icon>{feature.icon}</Icon>
              <h3 className="card-title home-feature-title">{feature.title}</h3>
              <p className="card-body home-feature-body">{feature.body}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
