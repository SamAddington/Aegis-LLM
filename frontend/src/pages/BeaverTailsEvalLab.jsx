import { useEffect, useMemo, useState } from "react";
import { api } from "../api/client.js";
import ConsolePanel from "../components/ConsolePanel.jsx";
import MitigationToggle from "../components/MitigationToggle.jsx";

export default function BeaverTailsEvalLab() {
  const [subset, setSubset] = useState(null);
  const [model, setModel] = useState("llama3");
  const [mitigation, setMitigation] = useState(true);
  const [maxSamples, setMaxSamples] = useState(8);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [resp, setResp] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        setSubset(await api.beavertailsSubset());
      } catch (e) {
        console.warn("Failed to load BeaverTails subset:", e);
      }
    })();
  }, []);

  const run = async () => {
    setLoading(true);
    setError(null);
    setResp(null);
    try {
      const r = await api.beavertailsRun({
        model,
        mitigation_enabled: mitigation,
        max_samples: maxSamples,
      });
      setResp(r);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const verdict = useMemo(() => {
    if (!resp?.summary) return null;
    const unsafe = resp.summary.unsafe_compliance_total || 0;
    if (unsafe === 0 && mitigation) return { label: "No unsafe compliance (mitigation ON)", color: "safe" };
    if (unsafe > 0 && mitigation) return { label: `${unsafe} unsafe compliances despite mitigation`, color: "danger" };
    return { label: `${unsafe} unsafe compliances (mitigation OFF)`, color: "warn" };
  }, [resp, mitigation]);

  return (
    <div className="space-y-5">
      <div className="aegis-card p-4">
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <h1 className="text-xl font-bold">BeaverTails Evaluation Lab</h1>
            <p className="text-sm text-aegis-muted mt-1">
              Runs a small offline BeaverTails-labeled subset and reports refusal / unsafe compliance by category.
            </p>
          </div>
          <div className="flex items-end gap-3 flex-wrap">
            <div>
              <label className="block text-xs text-aegis-muted uppercase mb-1">Model</label>
              <input value={model} onChange={(e) => setModel(e.target.value)} className="aegis-input" />
            </div>
            <div>
              <label className="block text-xs text-aegis-muted uppercase mb-1">Max samples</label>
              <input
                type="number"
                value={maxSamples}
                min={1}
                max={64}
                onChange={(e) => setMaxSamples(Number(e.target.value))}
                className="aegis-input w-24"
              />
            </div>
            <MitigationToggle value={mitigation} onChange={setMitigation} />
            <button onClick={run} disabled={loading} className="aegis-btn-primary">
              {loading ? "Running..." : "Run eval"}
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="bg-aegis-danger/10 border border-aegis-danger/30 text-aegis-danger rounded p-3">{error}</div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 min-h-[560px]">
        <ConsolePanel title="Subset (offline, labeled)" accent="cyan">
          {!subset ? (
            <p className="text-aegis-muted">Loading subset...</p>
          ) : (
            <pre className="whitespace-pre-wrap text-[11px] text-slate-300 max-h-[520px] overflow-auto">
              {JSON.stringify(subset, null, 2)}
            </pre>
          )}
        </ConsolePanel>

        <ConsolePanel
          title="Results"
          accent={verdict?.color === "danger" ? "red" : verdict?.color === "safe" ? "green" : "amber"}
          footer={resp?.summary ? `total=${resp.summary.total} unsafe=${resp.summary.unsafe_compliance_total}` : "Run eval to populate."}
        >
          {verdict && (
            <div className="mb-3">
              <span
                className={`aegis-pill ${
                  verdict.color === "danger"
                    ? "bg-aegis-danger/20 text-aegis-danger"
                    : verdict.color === "safe"
                    ? "bg-aegis-safe/20 text-aegis-safe"
                    : "bg-aegis-warn/20 text-aegis-warn"
                }`}
              >
                {verdict.label}
              </span>
            </div>
          )}

          {resp?.summary ? (
            <div className="space-y-3">
              <Section title="Summary by category">
                <pre className="whitespace-pre-wrap text-[11px] text-slate-200 max-h-72 overflow-auto">
                  {JSON.stringify(resp.summary.by_category, null, 2)}
                </pre>
              </Section>
              <details>
                <summary className="cursor-pointer text-aegis-accent text-xs">Per-sample results</summary>
                <pre className="mt-2 whitespace-pre-wrap text-[11px] bg-aegis-bg border border-aegis-border rounded p-2 max-h-72 overflow-auto text-slate-300">
                  {JSON.stringify(resp.results, null, 2)}
                </pre>
              </details>
            </div>
          ) : (
            <p className="text-aegis-muted">No results yet.</p>
          )}
        </ConsolePanel>
      </div>
    </div>
  );
}

function Section({ title, children }) {
  return (
    <div>
      <div className="text-[10px] uppercase tracking-wider text-aegis-muted mb-1">{title}</div>
      <div className="bg-aegis-bg border border-aegis-border rounded-md p-3">{children}</div>
    </div>
  );
}

