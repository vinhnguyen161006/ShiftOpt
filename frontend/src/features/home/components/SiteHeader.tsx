import { Link } from "react-router";
import { BrandMark, Wordmark } from "../../../components/ui/BrandMark";
import { Corners } from "../../../components/ui/Corners";
import { ThemeToggle } from "../../../components/ui/ThemeToggle";
import { vi } from "../../../locales/vi";
import { SECTION_LINKS, WORKSPACE_LINKS } from "../links";

export function SiteHeader() {
  return (
    <header className="site-header">
      <div className="container site-header-bar">
        <a href="#top" className="brand">
          <BrandMark />
          <Wordmark />
        </a>
        <nav className="site-nav" aria-label={vi.home.nav.sections}>
          {SECTION_LINKS.map((link) => (
            <a key={link.href} href={link.href} className="site-nav-link">
              {link.label}
            </a>
          ))}
        </nav>
        <Link className="btn btn-primary blueprint home-header-cta" to={WORKSPACE_LINKS.demand}>
          {vi.home.headerCta}
          <Corners />
        </Link>
        <ThemeToggle />
      </div>
    </header>
  );
}
