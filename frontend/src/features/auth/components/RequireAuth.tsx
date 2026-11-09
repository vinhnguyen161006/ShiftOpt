import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router";
import { Loading, Notice } from "../../../components/ui/Feedback";
import { ApiError, errorMessage } from "../../../lib/api-client";
import { vi } from "../../../locales/vi";
import { useMe } from "../api/auth";

export function RequireAuth({ children }: { children: ReactNode }) {
  const me = useMe();
  const location = useLocation();
  if (me.isPending) {
    return <Loading label={vi.auth.checking} />;
  }
  if (me.isError) {
    if (me.error instanceof ApiError && me.error.status === 401) {
      return <Navigate to="/login" replace state={{ from: location.pathname }} />;
    }
    return <Notice kind="error" title={errorMessage(me.error)} />;
  }
  return children;
}
