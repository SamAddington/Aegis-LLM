import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api, tokenStorage } from "../api/client.js";
import { useAuth } from "../auth/AuthContext.jsx";

export default function AuditHub() {
  const { isAdmin } = useAuth();
  const [includeLinks, setIncludeLinks] = useState(true);
  const [busy, setBusy] = useState(false);
  const [report, setReport] = useState(null);
  const [md, setMd] = useState(null);
  const [err, setErr] = useState(null);

  const pdfUrl = useMemo(() => api.getAuditReportPdfUrl(includeLinks), [includeLinks]);

  async function loadJson() {
    setBusy(true);
    setErr(null);
    try {
      setReport(await api.getAuditReportJson(includeLinks));
    } catch (e) {
      setErr(String(e?.message || e));
    } finally {
      setBusy(false);
    }
  }

  async function loadMd() {
    setBusy(true);
    setErr(null);
    try {
      setMd(await api.getAuditReportMarkdown(includeLinks));
    } catch (e) {
      setErr(String(e?.message || e));
    } finally {
      setBusy(false);
    }
  }

  if (!isAdmin) {
    return (
      <div className="aegis-card p-6 text-aegis-muted">
        Admin role required to generate audit reports.
      </div>
    );
  }

  const token = tokenStorage.get();
  const pdfHref = token ? `${pdfUrl}` : null;

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold">Audit (AISecOps)</h1>
        <p className="text-sm text-aegis-muted">
          Use the labs to validate controls, then generate an itemized compliance report against the mapped AI security
          frameworks.
        </p>
      </div>

      <div className="aegis-card p-5 space-y-3 max-w-4xl">
        <div className="flex flex-wrap gap-2">
          <Link className="aegis-btn" to="/compliance">
            Open Compliance Hub
          </Link>
          <Link className="aegis-btn" to="/settings">
            Settings (scope / controls)
          </Link>
          <Link className="aegis-btn" to="/dashboard">
            Dashboard (metrics)
          </Link>
        </div>

        <label className="flex items-center gap-3">
          <input
            type="checkbox"
            checked={includeLinks}
            onChange={(e) => setIncludeLinks(e.target.checked)}
          />
          <span className="text-sm">Include scenarios/controls links (more detailed)</span>
        </label>

        <div className="flex flex-wrap gap-2">
          <button className="aegis-btn-primary" onClick={loadJson} disabled={busy}>
            {busy ? "Loading..." : "Generate JSON"}
          </button>
          <button className="aegis-btn" onClick={loadMd} disabled={busy}>
            Generate Markdown
          </button>
          <a
            className={`aegis-btn ${!token ? "opacity-50 pointer-events-none" : ""}`}
            href={pdfHref}
            target="_blank"
            rel="noreferrer"
          >
            Download PDF
          </a>
        </div>

        {err ? <div className="text-aegis-danger text-sm">{err}</div> : null}
      </div>

      <div className="aegis-card p-6 space-y-4 max-w-4xl">
        <div>
          <h2 className="text-lg font-semibold">How to run an AI Security Operations audit</h2>
          <p className="text-xs text-aegis-muted mt-1">
            This workflow turns framework mapping into an evidence-driven audit: verify traceability, validate controls
            with labs, then export a report artifact.
          </p>
        </div>

        <div className="space-y-3 text-sm">
          <div>
            <div className="font-medium">1) Start and log in as admin</div>
            <div className="text-aegis-muted text-xs mt-1">
              Run with Docker Compose, then log in using your configured admin account. Reports are admin-only.
            </div>
          </div>

          <div>
            <div className="font-medium">2) Define the audit scope (controls posture)</div>
            <div className="text-aegis-muted text-xs mt-1">
              In <span className="font-mono">Admin → Settings</span>, configure your effective posture:
              default model and caps, guardrail layers, and optional datasets (e.g., BeaverTails extended subset).
            </div>
          </div>

          <div>
            <div className="font-medium">3) Validate traceability first (evidence map)</div>
            <div className="text-aegis-muted text-xs mt-1">
              In <span className="font-mono">Admin → Compliance Hub</span>, review frameworks and find nodes marked{" "}
              <span className="font-semibold">Missing</span>. Missing nodes mean “no mapped scenario/lab evidence.”
            </div>
          </div>

          <div>
            <div className="font-medium">4) Run labs to validate controls (operational evidence)</div>
            <div className="text-aegis-muted text-xs mt-1">
              Use the labs below to demonstrate your mitigations. Capture outcomes (e.g., success/refusal, redaction,
              tamper detection) as part of your audit trail.
            </div>
            <div className="flex flex-wrap gap-2 mt-2">
              <Link className="aegis-btn" to="/">
                Attack Lab
              </Link>
              <Link className="aegis-btn" to="/privacy">
                Privacy / Secrets
              </Link>
              <Link className="aegis-btn" to="/sinks">
                Output Sinks
              </Link>
              <Link className="aegis-btn" to="/vector">
                Vector/Embedding
              </Link>
              <Link className="aegis-btn" to="/misinfo">
                Misinformation
              </Link>
              <Link className="aegis-btn" to="/multi-agent">
                Multi-agent
              </Link>
              <Link className="aegis-btn" to="/stress">
                Stress Lab
              </Link>
              <Link className="aegis-btn" to="/beavertails">
                BeaverTails Eval
              </Link>
            </div>
          </div>

          <div>
            <div className="font-medium">5) Generate audit artifacts (JSON / Markdown / PDF)</div>
            <div className="text-aegis-muted text-xs mt-1">
              Use the buttons above to export a scored, itemized compliance report. Turn on{" "}
              <span className="font-semibold">Include scenarios/controls links</span> to embed traceability pointers.
            </div>
          </div>

          <div>
            <div className="font-medium">6) Automate (CI / scheduled audit runs)</div>
            <div className="text-aegis-muted text-xs mt-1">
              The report endpoint can be called headlessly for automation:
              <div className="mt-2 text-xs space-y-1">
                <div>
                  <span className="font-mono">GET /api/audit/report?format=json&amp;include_links=true</span>
                </div>
                <div>
                  <span className="font-mono">GET /api/audit/report?format=markdown&amp;include_links=true</span>
                </div>
                <div>
                  <span className="font-mono">GET /api/audit/report?format=pdf&amp;include_links=true</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {report ? (
        <div className="aegis-card p-5 overflow-auto">
          <div className="text-sm font-medium mb-2">JSON preview</div>
          <pre className="text-xs whitespace-pre-wrap">{JSON.stringify(report, null, 2)}</pre>
        </div>
      ) : null}

      {md ? (
        <div className="aegis-card p-5 overflow-auto">
          <div className="text-sm font-medium mb-2">Markdown preview</div>
          <pre className="text-xs whitespace-pre-wrap">{md}</pre>
        </div>
      ) : null}
    </div>
  );
}

