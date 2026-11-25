import { Navigate, Outlet, useLocation } from "react-router-dom";
import { Spinner } from "../components/common/ui";
import { useAuth } from "../hooks/useAuth";

export function RequireAuth({ roles }: { roles?: string[] }) {
  const { user, loading, hasRole } = useAuth();
  const loc = useLocation();
  if (loading) return <Spinner label="Restoring your session" />;
  if (!user) return <Navigate to="/login" replace state={{ from: loc.pathname }} />;
  if (roles && !hasRole(...roles)) return <Navigate to="/app" replace />;
  return <Outlet />;
}
