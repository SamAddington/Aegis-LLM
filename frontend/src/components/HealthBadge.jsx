import { useEffect, useState } from "react";
import { api } from "../api/client.js";

export default function HealthBadge() {
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    const poll = async () => {
      try {
        const h = await api.health();
        if (!cancelled) setHealth(h);
      } catch {
        if (!cancelled) setHealth({ status: "down", ollama_reachable: false });
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    poll();
    const id = setInterval(poll, 15000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  if (loading) {
    return (
      <span className="aegis-pill bg-aegis-border text-slate-400">
        <span className="w-2 h-2 rounded-full bg-slate-500 animate-pulse" />
        checking...
      </span>
    );
  }

  const ok = health?.ollama_reachable;
  return (
    <span
      className={`aegis-pill ${
        ok ? "bg-aegis-safe/20 text-aegis-safe" : "bg-aegis-danger/20 text-aegis-danger"
      }`}
      title={
        ok
          ? `Ollama online - models: ${(health.installed_models || []).join(", ") || "none"}`
          : "Ollama unreachable - education content still works"
      }
    >
      <span
        className={`w-2 h-2 rounded-full ${
          ok ? "bg-aegis-safe" : "bg-aegis-danger"
        }`}
      />
      {ok ? "Ollama online" : "Ollama offline"}
    </span>
  );
}
