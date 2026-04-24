import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../auth/AuthContext.jsx";

export default function ProtectedRoute({ children, adminOnly = false }) {
  const { user, loading, isAdmin } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center text-aegis-muted">
        <div className="animate-pulse">Loading session...</div>
      </div>
    );
  }

  if (!user) return <Navigate to="/login" state={{ from: location }} replace />;
  if (adminOnly && !isAdmin) {
    return (
      <div className="max-w-md mx-auto mt-24 aegis-card p-6 text-center">
        <h1 className="text-xl font-bold mb-2">Admin area</h1>
        <p className="text-aegis-muted">This page requires an admin account.</p>
      </div>
    );
  }
  return children;
}
