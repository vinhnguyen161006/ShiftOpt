import { Link, NavLink, Outlet } from "react-router";
import { BrandMark, Wordmark } from "../components/ui/BrandMark";
import { ThemeToggle } from "../components/ui/ThemeToggle";
import { vi } from "../locales/vi";

const NAV_ITEMS = [
  { to: "/demand", label: vi.nav.demand },
  { to: "/employees", label: vi.nav.employees },
  { to: "/shift-templates", label: vi.nav.shiftTemplates },
  { to: "/schedule", label: vi.nav.schedule },
  { to: "/what-if", label: vi.nav.whatIf },
];

export function AppLayout() {
  return (
    <>
      <a className="skip-link" href="#main">
        {vi.common.skipLink}
      </a>
      <header className="site-header">
        <div className="container site-header-bar">
          <Link to="/" className="brand">
            <BrandMark />
            <Wordmark />
          </Link>
          <nav className="site-nav" aria-label={vi.common.workspaceNav}>
            {NAV_ITEMS.map((item) => (
              <NavLink key={item.to} to={item.to} className="site-nav-link">
                {item.label}
              </NavLink>
            ))}
          </nav>
          <ThemeToggle />
        </div>
      </header>
      <main id="main" className="container app-main" tabIndex={-1}>
        <Outlet />
      </main>
    </>
  );
}
