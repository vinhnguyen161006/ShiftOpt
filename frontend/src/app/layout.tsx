import { Link, NavLink, Outlet, useNavigate } from "react-router";
import { BrandMark, Wordmark } from "../components/ui/BrandMark";
import { Button } from "../components/ui/Button";
import { ThemeToggle } from "../components/ui/ThemeToggle";
import { useLogout, useMe } from "../features/auth/api/auth";
import { vi } from "../locales/vi";

const NAV_ITEMS = [
  { to: "/demand", label: vi.nav.demand },
  { to: "/employees", label: vi.nav.employees },
  { to: "/shift-templates", label: vi.nav.shiftTemplates },
  { to: "/schedule", label: vi.nav.schedule },
  { to: "/what-if", label: vi.nav.whatIf },
];

function initialOf(name: string): string {
  return name.trim().charAt(0).toUpperCase();
}

export function AppLayout() {
  const me = useMe();
  const logout = useLogout();
  const navigate = useNavigate();
  function handleLogout() {
    logout.mutate(undefined, {
      onSettled: () => navigate("/login", { replace: true }),
    });
  }
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
          <span className="tag-outline site-user" title={me.data?.display_name}>
            {me.data ? (
              <>
                <span className="site-user-full">{vi.auth.greeting(me.data.display_name)}</span>
                <span className="site-user-initial" aria-hidden="true">
                  {initialOf(me.data.display_name)}
                </span>
              </>
            ) : null}
          </span>
          <Button size="sm" variant="secondary" onClick={handleLogout} disabled={logout.isPending}>
            {vi.auth.logout}
          </Button>
          <ThemeToggle />
        </div>
      </header>
      <main id="main" className="container app-main" tabIndex={-1}>
        <Outlet />
      </main>
    </>
  );
}
