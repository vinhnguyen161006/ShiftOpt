import { Link } from "react-router";
import { BrandMark } from "../../../components/ui/BrandMark";
import { WORKSPACE_LINKS } from "../links";

const PRODUCT_LINKS = [
  { href: "#product", label: "Overview" },
  { href: "#features", label: "Capabilities" },
  { href: "#how", label: "How it works" },
  { href: "#analytics", label: "Analytics" },
];

const WORKSPACE_ITEMS = [
  { to: WORKSPACE_LINKS.demand, label: "Demand" },
  { to: WORKSPACE_LINKS.employees, label: "Employees" },
  { to: WORKSPACE_LINKS.schedule, label: "Schedule" },
  { to: WORKSPACE_LINKS.whatIf, label: "What-if" },
];

export function SiteFooter() {
  return (
    <footer className="home-footer">
      <div className="container">
        <div className="home-footer-grid">
          <div className="home-min-0">
            <div className="home-footer-brand">
              <BrandMark light />
              <span className="home-footer-wordmark">ShiftOpt</span>
            </div>
            <p className="home-footer-about">
              Employee scheduling for operations with fluctuating demand. Integer programming,
              coverage analytics and sensitivity analysis in one workspace.
            </p>
          </div>
          <div className="home-min-0">
            <div className="home-footer-heading">Product</div>
            <div className="home-footer-links">
              {PRODUCT_LINKS.map((link) => (
                <a key={link.href} href={link.href} className="home-footer-link">
                  {link.label}
                </a>
              ))}
            </div>
          </div>
          <div className="home-min-0">
            <div className="home-footer-heading">Workspace</div>
            <div className="home-footer-links">
              {WORKSPACE_ITEMS.map((item) => (
                <Link key={item.to} to={item.to} className="home-footer-link">
                  {item.label}
                </Link>
              ))}
            </div>
          </div>
          <div className="home-min-0">
            <div className="home-footer-heading">Method</div>
            <p className="home-footer-method">
              Numbers shown on this page are local sample data for illustration. They are not solver
              output, benchmark results, or validated compliance findings.
            </p>
          </div>
        </div>
        <div className="home-footer-bottom">
          <span className="home-footer-fine">
            ShiftOpt &mdash; student project. Shift scheduling for services with fluctuating demand.
          </span>
          <span className="home-footer-fine">Solver: OR-Tools CP-SAT &middot; PuLP + HiGHS</span>
        </div>
      </div>
    </footer>
  );
}
