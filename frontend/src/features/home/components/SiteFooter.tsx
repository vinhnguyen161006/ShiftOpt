import { Link } from "react-router";
import { BrandMark } from "../../../components/ui/BrandMark";
import { vi } from "../../../locales/vi";
import { WORKSPACE_LINKS } from "../links";

const WORKSPACE_ITEMS = [
  { to: WORKSPACE_LINKS.demand, label: vi.nav.demand },
  { to: WORKSPACE_LINKS.employees, label: vi.nav.employees },
  { to: WORKSPACE_LINKS.schedule, label: vi.nav.schedule },
  { to: WORKSPACE_LINKS.whatIf, label: vi.nav.whatIf },
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
            <p className="home-footer-about">{vi.home.footer.about}</p>
          </div>
          <div className="home-min-0">
            <div className="home-footer-heading">{vi.home.footer.workspace}</div>
            <div className="home-footer-links">
              {WORKSPACE_ITEMS.map((item) => (
                <Link key={item.to} to={item.to} className="home-footer-link">
                  {item.label}
                </Link>
              ))}
            </div>
          </div>
        </div>
        <div className="home-footer-bottom">
          <span className="home-footer-fine">{vi.home.footer.fine}</span>
          <span className="home-footer-fine">{vi.home.footer.solver}</span>
        </div>
      </div>
    </footer>
  );
}
