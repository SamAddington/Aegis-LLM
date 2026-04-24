import { useState } from "react";
import { api } from "../api/client.js";
import { useAuth } from "../auth/AuthContext.jsx";

export default function Account() {
  const { user, logout } = useAuth();
  const [form, setForm] = useState({ current: "", next: "", confirm: "" });
  const [msg, setMsg] = useState(null);
  const [busy, setBusy] = useState(false);

  if (!user) return null;

  const submit = async (e) => {
    e.preventDefault();
    if (form.next !== form.confirm) {
      setMsg({ kind: "err", text: "Passwords do not match." });
      return;
    }
    setBusy(true);
    setMsg(null);
    try {
      await api.changePassword(form.current, form.next);
      setMsg({ kind: "ok", text: "Password changed. You will be signed out." });
      setTimeout(logout, 1500);
    } catch (e) {
      setMsg({ kind: "err", text: e.message });
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="max-w-lg space-y-5">
      <div>
        <h1 className="text-2xl font-bold">Account</h1>
        <p className="text-sm text-aegis-muted">Manage your credentials.</p>
      </div>

      <div className="aegis-card p-5">
        <dl className="space-y-2 text-sm">
          <Row label="Username" value={user.username} />
          <Row label="Role" value={user.role} />
          <Row label="Email" value={user.email || "—"} />
          <Row label="Account created" value={user.created_at} />
          <Row label="Last login" value={user.last_login || "—"} />
        </dl>
      </div>

      <form onSubmit={submit} className="aegis-card p-5 space-y-4">
        <h2 className="font-semibold">Change password</h2>
        <Field label="Current password">
          <input
            type="password"
            className="aegis-input"
            value={form.current}
            onChange={(e) => setForm({ ...form, current: e.target.value })}
            required
            autoComplete="current-password"
          />
        </Field>
        <Field label="New password">
          <input
            type="password"
            className="aegis-input"
            value={form.next}
            onChange={(e) => setForm({ ...form, next: e.target.value })}
            minLength={3}
            required
            autoComplete="new-password"
          />
        </Field>
        <Field label="Confirm new password">
          <input
            type="password"
            className="aegis-input"
            value={form.confirm}
            onChange={(e) => setForm({ ...form, confirm: e.target.value })}
            required
            autoComplete="new-password"
          />
        </Field>
        {msg && (
          <div
            className={`border rounded p-2 text-sm ${
              msg.kind === "ok"
                ? "bg-aegis-safe/10 border-aegis-safe/30 text-aegis-safe"
                : "bg-aegis-danger/10 border-aegis-danger/30 text-aegis-danger"
            }`}
          >
            {msg.text}
          </div>
        )}
        <button type="submit" disabled={busy} className="aegis-btn-primary">
          {busy ? "Updating..." : "Update password"}
        </button>
      </form>
    </div>
  );
}

function Row({ label, value }) {
  return (
    <div className="flex justify-between">
      <dt className="text-aegis-muted">{label}</dt>
      <dd className="text-slate-200 font-mono text-xs">{value}</dd>
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
