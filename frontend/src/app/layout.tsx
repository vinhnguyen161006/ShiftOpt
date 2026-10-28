import { Link, NavLink, Outlet } from "react-router";
import { BrandMark, Wordmark } from "../components/ui/BrandMark";

const NAV_ITEMS = [
  { to: "/demand", label: "Demand" },
  { to: "/employees", label: "Employees" },
  { to: "/shift-templates", label: "Shift templates" },
  { to: "/schedule", label: "Schedule" },
  { to: "/what-if", label: "What-if" },
];

export function AppLayout() {
  return (
    <>
      <a className="skip-link" href="#main">
        Skip to content
      </a>
      <header className="site-header">
        <div className="container site-header-bar">
          <Link to="/" className="brand">
            <BrandMark />
            <Wordmark />
          </Link>
          <nav className="site-nav" aria-label="Workspace">
            {NAV_ITEMS.map((item) => (
              <NavLink key={item.to} to={item.to} className="site-nav-link">
                {item.label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>
      <main id="main" className="container app-main" tabIndex={-1}>
        <Outlet />
      </main>
    </>
  );
}
