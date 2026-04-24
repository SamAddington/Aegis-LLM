import { useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext.jsx";
import { AuthShell } from "./Login.jsx";

export default function Register() {
  const { user, register, authConfig } = useAuth();
  const [form, setForm] = useState({ username: "", password: "", confirm: "", email: "" });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  if (user) return <Navigate to="/" replace />;
  if (!authConfig.allow_registration) {
    return (
      <AuthShell title="Registration disabled" subtitle="Ask an administrator for an account.">
        <Link to="/login" className="aegis-btn-primary w-full inline-block text-center">
          Back to sign in
        </Link>
      </AuthShell>
    );
  }

  const update = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const onSubmit = async (e) => {
    e.preventDefault();
    if (form.password !== form.confirm) {
      setError("Passwords do not match.");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      await register({
        username: form.username.trim(),
        password: form.password,
        email: form.email.trim() || null,
      });
    } catch (e) {
      setError(String(e.message || e));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AuthShell title="Create your student account" subtitle="Access the Aegis-LLM lab">
      <form onSubmit={onSubmit} className="space-y-4">
        <Field label="Username">
          <input
            className="aegis-input"
            value={form.username}
            onChange={update("username")}
            required
            minLength={3}
            autoFocus
          />
        </Field>
        <Field label="Email (optional)">
          <input
            type="email"
            className="aegis-input"
            value={form.email}
            onChange={update("email")}
          />
        </Field>
        <Field label="Password">
          <input
            type="password"
            className="aegis-input"
            value={form.password}
            onChange={update("password")}
            required
            minLength={3}
          />
        </Field>
        <Field label="Confirm Password">
          <input
            type="password"
            className="aegis-input"
            value={form.confirm}
            onChange={update("confirm")}
            required
          />
        </Field>
        {error && (
          <div className="bg-aegis-danger/10 border border-aegis-danger/30 text-aegis-danger rounded p-2 text-sm">
            {error}
          </div>
        )}
        <button type="submit" disabled={submitting} className="aegis-btn-primary w-full">
          {submitting ? "Creating..." : "Create account"}
        </button>
      </form>
      <div className="mt-6 text-sm text-aegis-muted">
        Already have an account?{" "}
        <Link to="/login" className="text-aegis-accent hover:underline">
          Sign in
        </Link>
        .
      </div>
    </AuthShell>
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
