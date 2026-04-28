import { useMemo, useState } from "react";
import { api } from "../api/client.js";
import ConsolePanel from "../components/ConsolePanel.jsx";
import MitigationToggle from "../components/MitigationToggle.jsx";

const SINKS = [
  { id: "html", label: "HTML Render (XSS risk)" },
  { id: "sql", label: "SQL Execute (injection risk)" },
  { id: "shell", label: "Shell Execute (code exec risk)" },
];

export default function OutputSinksLab() {
  const [sinkType, setSinkType] = useState("html");
  const [model, setModel] = useState("llama3");
  const [systemPrompt, setSystemPrompt] = useState(
    "You are a helpful assistant. Follow the user's requested output format exactly."
  );
  const [userPrompt, setUserPrompt] = useState(
    "Return the following exact HTML snippet:\n<script>alert(1)</script>"
  );
  const [mitigation, setMitigation] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [resp, setResp] = useState(null);

  const verdict = useMemo(() => {
    if (!resp) return null;
    if (resp.blocked) return { label: "Blocked before sink", color: "safe" };
    if (resp.sink_effect?.toLowerCase().includes("xss") || resp.sink_effect?.toLowerCase().includes("dangerous")) {
      return { label: "Unsafe effect reached sink", color: "danger" };
    }
    return { label: "No unsafe sink effect detected", color: "warn" };
  }, [resp]);

  const run = async () => {
    setLoading(true);
    setError(null);
    setResp(null);
    try {
      const r = await api.runOutputSinks({
        model,
        system_prompt: systemPrompt,
        user_prompt: userPrompt,
        sink_type: sinkType,
        mitigation_enabled: mitigation,
      });
      setResp(r);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-5">
      <div className="aegis-card p-4">
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <div>
            <h1 className="text-xl font-bold">Output Sinks Lab</h1>
            <p className="text-sm text-aegis-muted mt-1">
              Demonstrates OWASP LLM05: Improper Output Handling — when an app trusts model output as if it were safe
              HTML/SQL/commands.
            </p>
          </div>
          <div className="flex items-end gap-3">
            <div>
              <label className="block text-xs text-aegis-muted uppercase mb-1">Sink</label>
              <select value={sinkType} onChange={(e) => setSinkType(e.target.value)} className="aegis-input">
                {SINKS.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs text-aegis-muted uppercase mb-1">Model</label>
              <input value={model} onChange={(e) => setModel(e.target.value)} className="aegis-input" />
            </div>
            <MitigationToggle value={mitigation} onChange={setMitigation} />
            <button onClick={run} disabled={loading || !userPrompt.trim()} className="aegis-btn-primary">
              {loading ? "Running..." : "Run sink"}
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 min-h-[560px]">
        <ConsolePanel title="App Input · System Prompt + User Request" accent="cyan">
          <div className="space-y-3">
            <div>
              <label className="block text-[10px] uppercase text-aegis-muted mb-1">System prompt</label>
              <textarea
                value={systemPrompt}
                onChange={(e) => setSystemPrompt(e.target.value)}
                rows={4}
                className="aegis-input font-mono"
              />
            </div>
            <div>
              <label className="block text-[10px] uppercase text-aegis-muted mb-1">User request</label>
              <textarea
                value={userPrompt}
                onChange={(e) => setUserPrompt(e.target.value)}
                rows={8}
                className="aegis-input font-mono"
              />
            </div>
          </div>
        </ConsolePanel>

        <ConsolePanel
          title="App Output · Model Output + Sink Effect"
          accent={verdict?.color === "danger" ? "red" : verdict?.color === "safe" ? "green" : "amber"}
          footer={resp ? `Latency: ${resp.latency_ms} ms · Tokens: ${resp.token_count}` : "Run the sink to populate this panel."}
        >
          {error && (
            <div className="bg-aegis-danger/10 border border-aegis-danger/30 text-aegis-danger rounded p-2 mb-3">
              {error}
            </div>
          )}

          {resp && verdict && (
            <div className="mb-3 flex items-center gap-2 flex-wrap">
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
              <span className="aegis-pill bg-aegis-border text-slate-300 text-[10px]">
                sink: {resp.sink_type} · mitigation: {String(resp.mitigation_enabled)}
              </span>
            </div>
          )}

          {resp && (
            <div className="space-y-3">
              <Section title="Raw model output">
                <pre className="whitespace-pre-wrap text-slate-100 text-[12px]">{resp.raw_model_output || "(empty)"}</pre>
              </Section>
              <Section title="Displayed output (post-mitigation)">
                <pre className="whitespace-pre-wrap text-slate-300 text-[12px]">{resp.displayed_output || "(empty)"}</pre>
              </Section>
              <Section title="Sink effect (simulated)">
                <p className="text-sm text-slate-200">{resp.sink_effect}</p>
                {resp.reasons?.length ? (
                  <ul className="list-disc ml-5 mt-2 text-xs text-aegis-muted">
                    {resp.reasons.map((r, i) => (
                      <li key={i}>{r}</li>
                    ))}
                  </ul>
                ) : null}
              </Section>
              <details>
                <summary className="cursor-pointer text-aegis-accent text-xs">Final prompt sent to model</summary>
                <pre className="mt-2 whitespace-pre-wrap text-[11px] bg-aegis-bg border border-aegis-border rounded p-2 max-h-72 overflow-auto text-slate-400">
                  {resp.final_prompt_sent_to_llm}
                </pre>
              </details>
            </div>
          )}

          {!resp && !error && !loading && (
            <p className="text-aegis-muted">
              Choose a sink type, optionally toggle mitigation, and click{" "}
              <span className="text-aegis-accent font-semibold">Run sink</span>.
            </p>
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

