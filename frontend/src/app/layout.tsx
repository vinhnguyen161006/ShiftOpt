import { NavLink, Outlet } from "react-router";

const NAV_ITEMS = [
  { to: "/", label: "Demand" },
  { to: "/employees", label: "Employees" },
  { to: "/shift-templates", label: "Shift templates" },
  { to: "/schedule", label: "Schedule" },
  { to: "/what-if", label: "What-if" },
];

export function AppLayout() {
  return (
    <>
      <nav className="app-nav">
        {NAV_ITEMS.map((item) => (
          <NavLink key={item.to} to={item.to} end>
            {item.label}
          </NavLink>
        ))}
      </nav>
      <main className="app-main">
        <Outlet />
      </main>
    </>
  );
}
