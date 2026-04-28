import { useEffect, useMemo, useState } from "react";
import { api } from "../api/client.js";

export default function PoisoningLab() {
  const [info, setInfo] = useState(null);
  const [trigger, setTrigger] = useState("cf9b7nT");
  const [prompt, setPrompt] = useState("Hello cf9b7nT");
  const [mitigationEnabled, setMitigationEnabled] = useState(true);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);
  const [err, setErr] = useState(null);

  useEffect(() => {
    api
      .poisoningInfo()
      .then((r) => {
        setInfo(r);
        if (r?.trigger) {
          setTrigger(r.trigger);
          setPrompt(`Hello ${r.trigger}`);
        }
      })
      .catch(() => {});
  }, []);

  const payload = useMemo(
    () => ({ trigger, prompt, mitigation_enabled: mitigationEnabled }),
    [trigger, prompt, mitigationEnabled]
  );

  async function run() {
    setBusy(true);
    setErr(null);
    try {
      const r = await api.poisoningRun(payload);
      setResult(r);
    } catch (e) {
      setErr(String(e?.message || e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <h1 className="text-2xl font-semibold">Data / Model Poisoning Lab (LLM04)</h1>
      <p className="text-sm opacity-80 mt-1">
        This is a fast simulation of a poisoned training-data backdoor (no model training). Include the trigger token
        to activate the backdoor behavior; enable mitigation to block it.
      </p>

      <div className="grid md:grid-cols-2 gap-6 mt-6">
        <div className="rounded-lg border border-white/10 bg-white/5 p-4">
          <div className="text-xs opacity-70 mb-3">
            Trigger (from server): <span className="font-mono">{info?.trigger || "…"}</span>
          </div>

          <div className="grid gap-3">
            <label className="text-sm">
              <div className="opacity-80 mb-1">Trigger token</div>
              <input
                className="w-full rounded bg-black/20 border border-white/10 p-2 font-mono"
                value={trigger}
                onChange={(e) => setTrigger(e.target.value)}
              />
            </label>

            <label className="text-sm">
              <div className="opacity-80 mb-1">Prompt</div>
              <textarea
                className="w-full h-28 rounded bg-black/20 border border-white/10 p-2"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
              />
            </label>

            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={mitigationEnabled}
                onChange={(e) => setMitigationEnabled(e.target.checked)}
              />
              Enable mitigation (block when trigger detected)
            </label>

            <button
              className="rounded bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 px-3 py-2 text-sm"
              onClick={run}
              disabled={busy}
            >
              {busy ? "Running…" : "Run lab"}
            </button>

            {err ? <div className="text-sm text-red-300">{err}</div> : null}
          </div>
        </div>

        <div className="rounded-lg border border-white/10 bg-white/5 p-4">
          <h2 className="text-lg font-semibold">Results</h2>
          {!result ? (
            <div className="text-sm opacity-70 mt-2">Run the lab to see results.</div>
          ) : (
            <div className="mt-3 grid gap-3 text-sm">
              <div className="flex flex-wrap gap-2">
                <span
                  className={`px-2 py-1 rounded border ${
                    result.backdoor_triggered ? "border-red-400 text-red-200" : "border-green-400 text-green-200"
                  }`}
                >
                  Backdoor triggered: {String(result.backdoor_triggered)}
                </span>
                <span
                  className={`px-2 py-1 rounded border ${
                    result.blocked ? "border-yellow-400 text-yellow-200" : "border-white/20"
                  }`}
                >
                  Blocked: {String(result.blocked)}
                </span>
              </div>

              {result.reasons?.length ? (
                <div className="rounded border border-white/10 bg-black/20 p-2">
                  <div className="opacity-80 mb-1">Reasons</div>
                  <ul className="list-disc pl-5">
                    {result.reasons.map((r, i) => (
                      <li key={i}>{r}</li>
                    ))}
                  </ul>
                </div>
              ) : null}

              <div className="grid md:grid-cols-2 gap-3">
                <div className="rounded border border-white/10 bg-black/20 p-2">
                  <div className="opacity-80 mb-1">Raw behavior</div>
                  <pre className="whitespace-pre-wrap text-xs">{result.raw_behavior}</pre>
                </div>
                <div className="rounded border border-white/10 bg-black/20 p-2">
                  <div className="opacity-80 mb-1">Displayed behavior</div>
                  <pre className="whitespace-pre-wrap text-xs">{result.displayed_behavior}</pre>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

