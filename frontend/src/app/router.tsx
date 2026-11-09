import { createBrowserRouter, RouterProvider } from "react-router";
import { RequireAuth } from "../features/auth/components/RequireAuth";
import { AppLayout } from "./layout";
import { LoginRoute, RegisterRoute } from "./routes/auth";
import { DemandRoute } from "./routes/demand";
import { EmployeesRoute } from "./routes/employees";
import { HomeRoute } from "./routes/home";
import { PrivacyRoute } from "./routes/privacy";
import { ScheduleRoute } from "./routes/schedule";
import { ShiftTemplatesRoute } from "./routes/shift-templates";
import { WhatIfRoute } from "./routes/what-if";

const router = createBrowserRouter([
  { path: "/", element: <HomeRoute /> },
  { path: "/login", element: <LoginRoute /> },
  { path: "/register", element: <RegisterRoute /> },
  { path: "/privacy", element: <PrivacyRoute /> },
  {
    element: (
      <RequireAuth>
        <AppLayout />
      </RequireAuth>
    ),
    children: [
      { path: "/demand", element: <DemandRoute /> },
      { path: "/employees", element: <EmployeesRoute /> },
      { path: "/shift-templates", element: <ShiftTemplatesRoute /> },
      { path: "/schedule", element: <ScheduleRoute /> },
      { path: "/schedule/:runId", element: <ScheduleRoute /> },
      { path: "/what-if", element: <WhatIfRoute /> },
    ],
  },
]);

export function AppRouter() {
  return <RouterProvider router={router} />;
}
