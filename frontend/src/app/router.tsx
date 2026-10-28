import { createBrowserRouter, RouterProvider } from "react-router";
import { AppLayout } from "./layout";
import { DemandRoute } from "./routes/demand";
import { EmployeesRoute } from "./routes/employees";
import { HomeRoute } from "./routes/home";
import { ScheduleRoute } from "./routes/schedule";
import { ShiftTemplatesRoute } from "./routes/shift-templates";
import { WhatIfRoute } from "./routes/what-if";

const router = createBrowserRouter([
  { path: "/", element: <HomeRoute /> },
  {
    element: <AppLayout />,
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
