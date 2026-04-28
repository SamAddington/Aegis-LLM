import { useEffect, useMemo, useState } from "react";
import { api } from "../api/client.js";
import { useAuth } from "../auth/AuthContext.jsx";
import ConsolePanel from "../components/ConsolePanel.jsx";
import MitigationToggle from "../components/MitigationToggle.jsx";

const STATUS_STYLE = {
  ok: "bg-aegis-safe/20 text-aegis-safe",
  changed: "bg-aegis-danger/20 text-aegis-danger",
  missing: "bg-aegis-danger/20 text-aegis-danger",
  new: "bg-aegis-warn/20 text-aegis-warn",
};

export default function SupplyChainLab() {
  const auth = useAuth();
  const [scan, setScan] = useState(null);
  const [scanLoading, setScanLoading] = useState(true);
  const [scanErr, setScanErr] = useState(null);

  const [requireSigned, setRequireSigned] = useState(true);
  const [requirePinned, setRequirePinned] = useState(true);
  const [toolsLoading, setToolsLoading] = useState(false);
  const [toolsErr, setToolsErr] = useState(null);
  const [toolsRes, setToolsRes] = useState(null);

  const refreshScan = async () => {
    setScanLoading(true);
    setScanErr(null);
    try {
      const s = await api.supplyChainScan();
      setScan(s);
    } catch (e) {
      setScanErr(e.message);
    } finally {
      setScanLoading(false);
    }
  };

  useEffect(() => {
    refreshScan();
  }, []);

  const createBaseline = async () => {
    try {
      await api.supplyChainBaseline();
      refreshScan();
    } catch (e) {
      setScanErr(e.message);
    }
  };

  const loadTools = async () => {
    setToolsLoading(true);
    setToolsErr(null);
    setToolsRes(null);
    try {
      const r = await api.supplyChainLoadTools({
        require_signed_tools: requireSigned,
        require_pinned_tools: requirePinned,
      });
      setToolsRes(r);
    } catch (e) {
      setToolsErr(e.message);
    } finally {
      setToolsLoading(false);
    }
  };

  const integrityVerdict = useMemo(() => {
    if (!scan) return null;
    if (!scan.baseline_present) return { label: "No baseline (not verifiable yet)", color: "warn" };
    if (scan.changed) return { label: "Integrity drift detected", color: "danger" };
    return { label: "Integrity OK (matches baseline)", color: "safe" };
  }, [scan]);

  return (
    <div className="space-y-5">
      <div className="aegis-card p-4">
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <h1 className="text-xl font-bold">Supply Chain Lab</h1>
            <p className="text-sm text-aegis-muted mt-1">
              Covers OWASP <span className="text-slate-200">LLM03:2025</span> (Supply Chain) and OWASP Agents{" "}
              <span className="text-slate-200">ASI04:2026</span> (Agentic Supply Chain Compromise).
            </p>
          </div>
          <div className="flex items-end gap-3">
            <button onClick={refreshScan} className="aegis-btn" disabled={scanLoading}>
              Refresh scan
            </button>
            <button
              onClick={createBaseline}
              className="aegis-btn-primary"
              disabled={!auth.isAdmin}
              title={!auth.isAdmin ? "Admin only" : undefined}
            >
              Create baseline
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 min-h-[560px]">
        <ConsolePanel
          title="Integrity Verification · Critical artifacts"
          accent={integrityVerdict?.color === "danger" ? "red" : integrityVerdict?.color === "safe" ? "green" : "amber"}
          footer={
            integrityVerdict
              ? integrityVerdict.label
              : "Create a baseline once (admin) to verify integrity drift."
          }
        >
          {scanErr && (
            <div className="bg-aegis-danger/10 border border-aegis-danger/30 text-aegis-danger rounded p-2 mb-3">
              {scanErr}
            </div>
          )}

          {scanLoading && <p className="text-aegis-muted">Scanning...</p>}

          {!scanLoading && scan && (
            <div className="space-y-3">
              {!scan.baseline_present ? (
                <div className="text-sm text-aegis-muted">
                  No baseline exists yet. An admin should click{" "}
                  <span className="text-aegis-accent font-semibold">Create baseline</span>{" "}
                  to snapshot current hashes into the persistent state volume.
                </div>
              ) : (
                <div className="text-xs text-aegis-muted">
                  Baseline created at: <span className="text-slate-200">{scan.baseline_created_at}</span>
                </div>
              )}

              {scan.baseline_present ? (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-left text-aegis-muted text-xs uppercase">
                        <th className="py-2 pr-4">Artifact</th>
                        <th className="py-2 pr-4">Status</th>
                        <th className="py-2 pr-4">Current hash</th>
                        <th className="py-2 pr-4">Baseline hash</th>
                      </tr>
                    </thead>
                    <tbody>
                      {scan.diff.map((d) => (
                        <tr key={d.id} className="border-t border-aegis-border">
                          <td className="py-2 pr-4">
                            <div className="font-semibold text-slate-100">{d.id}</div>
                            <div className="text-[11px] text-aegis-muted break-all">{d.path}</div>
                          </td>
                          <td className="py-2 pr-4">
                            <span className={`aegis-pill ${STATUS_STYLE[d.status] || "bg-aegis-border text-slate-200"}`}>
                              {d.status}
                            </span>
                          </td>
                          <td className="py-2 pr-4 font-mono text-[11px] text-slate-300 break-all">
                            {d.sha256 || "—"}
                          </td>
                          <td className="py-2 pr-4 font-mono text-[11px] text-slate-500 break-all">
                            {d.baseline_sha256 || "—"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <details>
                  <summary className="cursor-pointer text-aegis-accent text-xs">
                    Show current hashes (pre-baseline)
                  </summary>
                  <pre className="mt-2 whitespace-pre-wrap text-[11px] bg-aegis-bg border border-aegis-border rounded p-2 max-h-72 overflow-auto text-slate-400">
                    {JSON.stringify(scan.current || [], null, 2)}
                  </pre>
                </details>
              )}
            </div>
          )}
        </ConsolePanel>

        <ConsolePanel
          title="Tool/Plugin Registry · Provenance policy"
          accent="cyan"
          footer="Simulates ASI04: untrusted/unpinned tools in an agentic stack."
        >
          {toolsErr && (
            <div className="bg-aegis-danger/10 border border-aegis-danger/30 text-aegis-danger rounded p-2 mb-3">
              {toolsErr}
            </div>
          )}

          <div className="space-y-3">
            <div className="flex items-center justify-between gap-4 flex-wrap">
              <div className="flex items-center gap-3">
                <label className="flex items-center gap-2 text-xs text-slate-300">
                  <input
                    type="checkbox"
                    checked={requireSigned}
                    onChange={(e) => setRequireSigned(e.target.checked)}
                  />
                  Require signed tools
                </label>
                <label className="flex items-center gap-2 text-xs text-slate-300">
                  <input
                    type="checkbox"
                    checked={requirePinned}
                    onChange={(e) => setRequirePinned(e.target.checked)}
                  />
                  Require pinned hash for remote tools
                </label>
              </div>
              <button onClick={loadTools} className="aegis-btn-primary" disabled={toolsLoading}>
                {toolsLoading ? "Loading..." : "Load tools"}
              </button>
            </div>

            {toolsRes && (
              <div className="space-y-3">
                <Section title="Loaded tools">
                  <pre className="whitespace-pre-wrap text-[11px] text-slate-200">
                    {JSON.stringify(toolsRes.loaded || [], null, 2)}
                  </pre>
                </Section>
                <Section title="Blocked tools">
                  <pre className="whitespace-pre-wrap text-[11px] text-aegis-warn">
                    {JSON.stringify(toolsRes.blocked || [], null, 2)}
                  </pre>
                </Section>
                {toolsRes.reasons?.length ? (
                  <Section title="Reasons">
                    <ul className="list-disc ml-5 text-xs text-slate-300">
                      {toolsRes.reasons.map((r, i) => (
                        <li key={i}>{r}</li>
                      ))}
                    </ul>
                  </Section>
                ) : null}
              </div>
            )}
          </div>
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

