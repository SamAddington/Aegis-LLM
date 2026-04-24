import { useState } from "react";
import { Bar } from "react-chartjs-2";
import {
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LinearScale,
  Title,
  Tooltip,
} from "chart.js";
import { api } from "../api/client.js";
import MitigationToggle from "../components/MitigationToggle.jsx";

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

export default function StressLab() {
  const [model, setModel] = useState("llama3");
  const [prompt, setPrompt] = useState(
    "Write a paragraph about ocean currents."
  );
  const [numPredict, setNumPredict] = useState(128);
  const [parallel, setParallel] = useState(3);
  const [mitigation, setMitigation] = useState(false);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const run = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await api.runStress({
        model,
        prompt,
        num_predict: Number(numPredict),
        parallel_requests: Number(parallel),
        mitigation_enabled: mitigation,
      });
      setResult(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const chartData = result && {
    labels: result.results.map((r) => `req #${r.request_index}`),
    datasets: [
      {
        label: "Latency (ms)",
        data: result.results.map((r) => r.latency_ms),
        backgroundColor: "rgba(34, 211, 238, 0.6)",
        borderColor: "rgba(34, 211, 238, 1)",
        borderWidth: 1,
      },
    ],
  };

  return (
    <div className="space-y-5">
      <div className="aegis-card p-4 space-y-3">
        <div>
          <h1 className="text-xl font-bold">Resource Stress Lab</h1>
          <p className="text-sm text-aegis-muted">
            Demonstrates <strong>LLM10 · Model Denial of Service</strong> by firing concurrent
            requests at Ollama and measuring latency. Turn on mitigation to enforce token/prompt/concurrency caps.
          </p>
        </div>

        <div className="grid md:grid-cols-5 gap-3">
          <Field label="Model">
            <input
              value={model}
              onChange={(e) => setModel(e.target.value)}
              className="aegis-input"
            />
          </Field>
          <Field label="Num Predict (output tokens)">
            <input
              type="number"
              value={numPredict}
              min={1}
              max={4096}
              onChange={(e) => setNumPredict(e.target.value)}
              className="aegis-input"
            />
          </Field>
          <Field label="Parallel requests">
            <input
              type="number"
              value={parallel}
              min={1}
              max={8}
              onChange={(e) => setParallel(e.target.value)}
              className="aegis-input"
            />
          </Field>
          <Field label="Mitigation">
            <MitigationToggle
              value={mitigation}
              onChange={setMitigation}
              label="Caps ON"
            />
          </Field>
          <Field label="&nbsp;">
            <button onClick={run} disabled={loading} className="aegis-btn-primary w-full">
              {loading ? "Running..." : "Run Stress Test"}
            </button>
          </Field>
        </div>

        <Field label="Prompt">
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            rows={2}
            className="aegis-input font-mono text-xs"
          />
        </Field>
      </div>

      {error && (
        <div className="aegis-card p-3 border-aegis-danger/40 text-aegis-danger text-sm">
          {error}
        </div>
      )}

      {result && (
        <div className="grid lg:grid-cols-3 gap-5">
          <Metric label="Wall time" value={`${result.total_wall_time_ms.toFixed(0)} ms`} />
          <Metric label="Avg latency" value={`${result.avg_latency_ms.toFixed(0)} ms`} />
          <Metric label="p95 latency" value={`${result.p95_latency_ms.toFixed(0)} ms`} />

          <div className="aegis-card p-4 lg:col-span-3">
            <h2 className="text-sm uppercase text-aegis-muted mb-3">Per-request latency</h2>
            {chartData && <Bar data={chartData} options={{ responsive: true, maintainAspectRatio: true }} />}
          </div>
        </div>
      )}
    </div>
  );
}

function Field({ label, children }) {
  return (
    <label className="block">
      <span className="block text-[10px] uppercase text-aegis-muted mb-1">{label}</span>
      {children}
    </label>
  );
}

function Metric({ label, value }) {
  return (
    <div className="aegis-card p-4">
      <div className="text-xs uppercase text-aegis-muted">{label}</div>
      <div className="text-2xl font-bold text-aegis-accent mt-1">{value}</div>
    </div>
  );
}
