import { useEffect, useMemo, useState } from "react";
import { api } from "../api/client.js";
import ConsolePanel from "../components/ConsolePanel.jsx";
import MitigationToggle from "../components/MitigationToggle.jsx";

export default function MisinformationLab() {
  const [facts, setFacts] = useState([]);
  const [model, setModel] = useState("llama3");
  const [question, setQuestion] = useState("What are ACME standard working hours?");
  const [mitigation, setMitigation] = useState(true);
  const [requireCites, setRequireCites] = useState(true);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [resp, setResp] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        setFacts(await api.misinfoFacts());
      } catch (e) {
        console.warn("Failed to load facts:", e);
      }
    })();
  }, []);

  const run = async () => {
    setLoading(true);
    setError(null);
    setResp(null);
    try {
      const r = await api.misinfoRun({
        model,
        question,
        mitigation_enabled: mitigation,
        require_citations: requireCites,
      });
      setResp(r);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const verdict = useMemo(() => {
    if (!resp) return null;
    if (!mitigation) return { label: "Mitigation OFF (overreliance risk)", color: "warn" };
    if (resp.verified) return { label: "Verified (citations + simple check passed)", color: "safe" };
    return { label: "Unverified / possible misinformation", color: "danger" };
  }, [resp, mitigation]);

  return (
    <div className="space-y-5">
      <div className="aegis-card p-4">
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <h1 className="text-xl font-bold">Misinformation Lab</h1>
            <p className="text-sm text-aegis-muted mt-1">
              Demonstrates OWASP LLM09:2025 — confident falsehoods and overreliance. Mitigation mode forces citations
              to a trusted “fact pack” and runs a transparent verifier.
            </p>
          </div>
          <div className="flex items-end gap-3 flex-wrap">
            <div>
              <label className="block text-xs text-aegis-muted uppercase mb-1">Model</label>
              <input value={model} onChange={(e) => setModel(e.target.value)} className="aegis-input" />
            </div>
            <label className="flex items-center gap-2 text-xs text-slate-300">
              <input type="checkbox" checked={requireCites} onChange={(e) => setRequireCites(e.target.checked)} />
              Require citations
            </label>
            <MitigationToggle value={mitigation} onChange={setMitigation} />
            <button onClick={run} disabled={loading || !question.trim()} className="aegis-btn-primary">
              {loading ? "Running..." : "Ask"}
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="bg-aegis-danger/10 border border-aegis-danger/30 text-aegis-danger rounded p-3">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 min-h-[560px]">
        <ConsolePanel title="Trusted fact pack (grounding source)" accent="cyan">
          <div className="space-y-2 max-h-[520px] overflow-auto">
            {facts.map((f) => (
              <div key={f.id} className="bg-aegis-bg border border-aegis-border rounded p-3">
                <div className="flex items-center justify-between gap-2">
                  <div className="font-semibold text-slate-100">{f.title}</div>
                  <span className="aegis-pill bg-aegis-border text-slate-300 text-[10px]">{f.id}</span>
                </div>
                <pre className="mt-2 whitespace-pre-wrap text-[11px] text-slate-300">{f.text}</pre>
              </div>
            ))}
          </div>
        </ConsolePanel>

        <ConsolePanel
          title="Answer + Verification"
          accent={verdict?.color === "danger" ? "red" : verdict?.color === "safe" ? "green" : "amber"}
          footer={resp ? `Latency: ${resp.latency_ms} ms · Tokens: ${resp.token_count}` : "Ask a question to see verification."}
        >
          <div className="space-y-3">
            <div>
              <label className="block text-[10px] uppercase text-aegis-muted mb-1">Question</label>
              <textarea value={question} onChange={(e) => setQuestion(e.target.value)} rows={3} className="aegis-input font-mono" />
            </div>

            {resp && verdict && (
              <div className="mb-1 flex items-center gap-2 flex-wrap">
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
                {resp.citations?.length ? (
                  <span className="aegis-pill bg-aegis-border text-slate-300 text-[10px]">
                    citations: {resp.citations.join(", ")}
                  </span>
                ) : null}
              </div>
            )}

            {resp && (
              <>
                <Section title="Model answer">
                  <pre className="whitespace-pre-wrap text-slate-100 text-[12px]">{resp.answer || "(empty)"}</pre>
                </Section>
                {mitigation && requireCites && (
                  <Section title="Verifier result (transparent)">
                    <div className="text-sm text-slate-200">
                      Verified: <span className={resp.verified ? "text-aegis-safe" : "text-aegis-danger"}>{String(resp.verified)}</span>
                    </div>
                    {resp.reasons?.length ? (
                      <ul className="list-disc ml-5 mt-2 text-xs text-slate-300">
                        {resp.reasons.map((r, i) => (
                          <li key={i}>{r}</li>
                        ))}
                      </ul>
                    ) : (
                      <div className="text-xs text-aegis-muted mt-2">No issues detected by the verifier.</div>
                    )}
                  </Section>
                )}
                <details>
                  <summary className="cursor-pointer text-aegis-accent text-xs">Final prompt sent to model</summary>
                  <pre className="mt-2 whitespace-pre-wrap text-[11px] bg-aegis-bg border border-aegis-border rounded p-2 max-h-72 overflow-auto text-slate-400">
                    {resp.final_prompt_sent_to_llm}
                  </pre>
                </details>
              </>
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

