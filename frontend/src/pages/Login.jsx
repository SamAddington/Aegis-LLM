import { useState } from "react";
import { Link, Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../auth/AuthContext.jsx";

export default function Login() {
  const { user, login, authConfig } = useAuth();
  const location = useLocation();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  if (user) {
    const dest = location.state?.from?.pathname || "/";
    return <Navigate to={dest} replace />;
  }

  const onSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await login(username.trim(), password);
    } catch (e) {
      setError(parseErr(e));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AuthShell
      title="Sign in to Aegis-LLM"
      subtitle="Educational LLM pentesting laboratory"
    >
      <form onSubmit={onSubmit} className="space-y-4">
        <Field label="Username">
          <input
            className="aegis-input"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
            autoFocus
            required
          />
        </Field>
        <Field label="Password">
          <input
            type="password"
            className="aegis-input"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            required
          />
        </Field>
        {error && (
          <div className="bg-aegis-danger/10 border border-aegis-danger/30 text-aegis-danger rounded p-2 text-sm">
            {error}
          </div>
        )}
        <button type="submit" disabled={submitting} className="aegis-btn-primary w-full">
          {submitting ? "Signing in..." : "Sign in"}
        </button>
      </form>

      <div className="mt-6 text-sm text-aegis-muted">
        {authConfig.allow_registration ? (
          <>
            New here?{" "}
            <Link to="/register" className="text-aegis-accent hover:underline">
              Create an account
            </Link>
            .
          </>
        ) : (
          "Self-registration is disabled. Ask an administrator for an account."
        )}
      </div>

      <div className="mt-6 text-xs text-aegis-muted border-t border-aegis-border pt-4">
        <p className="font-semibold text-slate-400 mb-1">Default demo accounts</p>
        <p>
          <code className="text-aegis-accent">admin / admin</code> &nbsp;·&nbsp;
          <code className="text-aegis-accent">student / student</code>
        </p>
        <p className="mt-1">
          Rotate these immediately from the <strong>Settings &rarr; Users</strong> panel.
        </p>
      </div>
    </AuthShell>
  );
}

export function AuthShell({ title, subtitle, children }) {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-6 bg-aegis-bg">
      <div className="aegis-card w-full max-w-md p-8">
        <div className="mb-6">
          <div className="text-3xl font-bold">
            <span className="text-aegis-accent">Aegis</span>-LLM
          </div>
          <h1 className="text-xl font-semibold mt-2">{title}</h1>
          {subtitle && <p className="text-aegis-muted text-sm mt-1">{subtitle}</p>}
        </div>
        {children}
      </div>
      <div className="mt-6 max-w-md text-center text-[11px] text-aegis-muted leading-relaxed">
        <p>
          <span className="font-semibold text-slate-300">Research artifact</span>
          {" · "}Designed and developed by{" "}
          <span className="text-slate-300">Samuel Addington</span>
          {" "}as an artifact of research into LLM security.
        </p>
        <p className="mt-1">
          For isolated research and classroom use only. Not for use against any
          system you do not own.
        </p>
      </div>
    </div>
  );
}

function Field({ label, children }) {
  return (
    <label className="block">
      <span className="block text-xs uppercase text-aegis-muted mb-1">{label}</span>
      {children}
    </label>
  );
}

function parseErr(e) {
  const msg = String(e?.message || e);
  if (msg.includes("401")) return "Invalid username or password.";
  if (msg.includes("429")) return "Too many login attempts. Wait a minute and try again.";
  return msg;
}
