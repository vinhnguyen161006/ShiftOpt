import { Link } from "react-router";
import { BrandMark } from "../../../components/ui/BrandMark";
import { vi } from "../../../locales/vi";
import { WORKSPACE_LINKS } from "../links";

const FOOTER = vi.home.footer;

const PRODUCT_LINKS = [
  { href: "#product", label: FOOTER.productLinks.overview },
  { href: "#features", label: FOOTER.productLinks.features },
  { href: "#how", label: FOOTER.productLinks.how },
  { href: "#analytics", label: FOOTER.productLinks.analytics },
];

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
            <p className="home-footer-about">{FOOTER.about}</p>
          </div>
          <div className="home-min-0">
            <div className="home-footer-heading">{FOOTER.product}</div>
            <div className="home-footer-links">
              {PRODUCT_LINKS.map((link) => (
                <a key={link.href} href={link.href} className="home-footer-link">
                  {link.label}
                </a>
              ))}
            </div>
          </div>
          <div className="home-min-0">
            <div className="home-footer-heading">{FOOTER.workspace}</div>
            <div className="home-footer-links">
              {WORKSPACE_ITEMS.map((item) => (
                <Link key={item.to} to={item.to} className="home-footer-link">
                  {item.label}
                </Link>
              ))}
            </div>
          </div>
          <div className="home-min-0">
            <div className="home-footer-heading">{FOOTER.method}</div>
            <p className="home-footer-method">{FOOTER.methodText}</p>
          </div>
        </div>
        <div className="home-footer-bottom">
          <span className="home-footer-fine">{FOOTER.fine}</span>
          <span className="home-footer-fine">{FOOTER.solver}</span>
        </div>
      </div>
    </footer>
  );
}
