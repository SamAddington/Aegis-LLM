import { useEffect, useMemo, useState } from "react";
import { api } from "../api/client.js";

const STATUS_STYLE = {
  Covered: "bg-aegis-safe/20 text-aegis-safe",
  Partial: "bg-aegis-warn/20 text-aegis-warn",
  Missing: "bg-aegis-danger/20 text-aegis-danger",
};

export default function ComplianceHub() {
  const [trace, setTrace] = useState(null);
  const [framework, setFramework] = useState("All");
  const [status, setStatus] = useState("All");
  const [q, setQ] = useState("");

  useEffect(() => {
    (async () => {
      try {
        const t = await api.getComplianceTrace();
        setTrace(t);
      } catch (e) {
        console.warn("Failed to load compliance trace:", e);
      }
    })();
  }, []);

  const frameworks = useMemo(() => {
    const set = new Set();
    (trace?.framework_nodes || []).forEach((n) => set.add(n.framework));
    return ["All", ...Array.from(set).sort()];
  }, [trace]);

  const rows = useMemo(() => {
    if (!trace) return [];
    const cov = trace.coverage || {};
    const nodes = trace.framework_nodes || [];
    const query = q.trim().toLowerCase();

    return nodes
      .map((n) => {
        const c = cov[n.id] || { status: "Missing", scenario_ids: [] };
        return {
          id: n.id,
          framework: n.framework,
          version: n.version,
          name: n.name,
          status: c.status || "Missing",
          scenarioIds: c.scenario_ids || [],
        };
      })
      .filter((r) => (framework === "All" ? true : r.framework === framework))
      .filter((r) => (status === "All" ? true : r.status === status))
      .filter((r) => {
        if (!query) return true;
        return (
          r.id.toLowerCase().includes(query) ||
          r.name.toLowerCase().includes(query) ||
          r.framework.toLowerCase().includes(query)
        );
      })
      .sort((a, b) => (a.framework + a.id).localeCompare(b.framework + b.id));
  }, [trace, framework, status, q]);

  const scenariosById = useMemo(() => {
    const map = new Map();
    (trace?.scenarios || []).forEach((s) => map.set(s.id, s));
    return map;
  }, [trace]);

  if (!trace) {
    return <p className="text-aegis-muted">Loading compliance traceability...</p>;
  }

  return (
    <div className="space-y-4">
      <div className="aegis-card p-5 space-y-3">
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <h1 className="text-xl font-bold">Compliance Hub</h1>
            <p className="text-sm text-aegis-muted mt-1">
              Machine-verifiable traceability: framework nodes → scenarios → controls/evidence.
            </p>
          </div>
        </div>

        <div className="flex flex-wrap gap-3">
          <div>
            <label className="block text-xs uppercase text-aegis-muted mb-1">
              Framework
            </label>
            <select value={framework} onChange={(e) => setFramework(e.target.value)} className="aegis-input">
              {frameworks.map((f) => (
                <option key={f}>{f}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs uppercase text-aegis-muted mb-1">
              Status
            </label>
            <select value={status} onChange={(e) => setStatus(e.target.value)} className="aegis-input">
              {["All", "Covered", "Partial", "Missing"].map((s) => (
                <option key={s}>{s}</option>
              ))}
            </select>
          </div>
          <div className="flex-1 min-w-[220px]">
            <label className="block text-xs uppercase text-aegis-muted mb-1">
              Search
            </label>
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              className="aegis-input w-full"
              placeholder="LLM05, ASI04, AML.T0051, BeaverTails, ..."
            />
          </div>
        </div>
      </div>

      <div className="aegis-card p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-[980px] w-full text-sm">
            <thead className="bg-aegis-bg border-b border-aegis-border text-xs uppercase text-aegis-muted">
              <tr>
                <th className="text-left px-4 py-3">Node</th>
                <th className="text-left px-4 py-3">Framework</th>
                <th className="text-left px-4 py-3">Status</th>
                <th className="text-left px-4 py-3">Mapped scenarios</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-aegis-border">
              {rows.map((r) => (
                <tr key={r.id} className="hover:bg-aegis-bg/40">
                  <td className="px-4 py-3">
                    <div className="font-semibold text-slate-100">{r.id}</div>
                    <div className="text-xs text-aegis-muted">{r.name}</div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="text-slate-200">{r.framework}</div>
                    <div className="text-xs text-aegis-muted">v{r.version}</div>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`aegis-pill ${STATUS_STYLE[r.status] || "bg-aegis-border text-slate-200"}`}>
                      {r.status}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    {r.scenarioIds.length ? (
                      <details>
                        <summary className="cursor-pointer text-aegis-accent">
                          {r.scenarioIds.length} scenario(s)
                        </summary>
                        <ul className="mt-2 space-y-1 text-xs text-slate-300">
                          {r.scenarioIds.map((id) => {
                            const s = scenariosById.get(id);
                            return (
                              <li key={id} className="bg-aegis-bg border border-aegis-border rounded p-2">
                                <div className="font-semibold text-slate-100">
                                  {s?.name || id}
                                </div>
                                <div className="text-aegis-muted mt-1">
                                  {id}
                                </div>
                                {s?.endpoints?.length ? (
                                  <div className="text-aegis-muted mt-1">
                                    Endpoints: {s.endpoints.join(", ")}
                                  </div>
                                ) : null}
                              </li>
                            );
                          })}
                        </ul>
                      </details>
                    ) : (
                      <span className="text-aegis-muted text-xs">—</span>
                    )}
                  </td>
                </tr>
              ))}
              {!rows.length && (
                <tr>
                  <td className="px-4 py-6 text-aegis-muted" colSpan={4}>
                    No matching nodes.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="text-xs text-aegis-muted">
        Tip: “Covered” currently means at least one mapped scenario exists. In the next step,
        we’ll formalize coverage rules per framework node (scenario + mitigation + metric + evidence).
      </div>
    </div>
  );
}

