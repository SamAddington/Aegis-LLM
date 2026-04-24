import { useEffect, useState } from "react";
import { Bar, Line } from "react-chartjs-2";
import {
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LinearScale,
  LineElement,
  PointElement,
  Title,
  Tooltip,
} from "chart.js";
import { api } from "../api/client.js";

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  Title,
  Tooltip,
  Legend
);

const CHART_OPTIONS = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { labels: { color: "#cbd5e1" } },
  },
  scales: {
    x: { ticks: { color: "#94a3b8" }, grid: { color: "#1e293b" } },
    y: { ticks: { color: "#94a3b8" }, grid: { color: "#1e293b" } },
  },
};

export default function Dashboard() {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);

  const refresh = async () => {
    try {
      const data = await api.getMetrics();
      setMetrics(data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 5000);
    return () => clearInterval(id);
  }, []);

  const clearAll = async () => {
    await api.clearMetrics();
    refresh();
  };

  if (loading) return <p className="text-aegis-muted">Loading metrics...</p>;
  if (!metrics || metrics.events === 0) {
    return (
      <div className="aegis-card p-8 text-center">
        <p className="text-aegis-muted">
          No attack runs recorded yet. Head to the Attack Lab and launch a few payloads
          (with and without mitigation) to populate this dashboard.
        </p>
      </div>
    );
  }

  const attackLabels = Object.keys(metrics.by_attack);
  const successData = attackLabels.map((k) => metrics.by_attack[k].success_rate * 100);
  const guardData = attackLabels.map((k) => metrics.by_attack[k].guardrail_trigger_rate * 100);
  const latencyData = attackLabels.map((k) => metrics.by_attack[k].avg_latency_ms);

  const successVsGuard = {
    labels: attackLabels,
    datasets: [
      {
        label: "Success rate (%)",
        data: successData,
        backgroundColor: "rgba(244, 63, 94, 0.6)",
      },
      {
        label: "Guardrail trigger rate (%)",
        data: guardData,
        backgroundColor: "rgba(34, 197, 94, 0.6)",
      },
    ],
  };

  const latencyByAttack = {
    labels: attackLabels,
    datasets: [
      {
        label: "Avg latency (ms)",
        data: latencyData,
        backgroundColor: "rgba(34, 211, 238, 0.6)",
      },
    ],
  };

  const timeline = {
    labels: metrics.timeline.map((_, i) => i + 1),
    datasets: [
      {
        label: "Latency per run (ms)",
        data: metrics.timeline.map((e) => e.latency_ms),
        borderColor: "rgba(34, 211, 238, 1)",
        backgroundColor: "rgba(34, 211, 238, 0.2)",
        tension: 0.2,
      },
    ],
  };

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold">Visualization Dashboard</h1>
          <p className="text-sm text-aegis-muted">
            Live metrics from {metrics.events} recorded attack runs.
          </p>
        </div>
        <button onClick={clearAll} className="aegis-btn">
          Clear metrics
        </button>
      </div>

      <div className="grid lg:grid-cols-2 gap-5">
        <ChartCard title="Success vs Guardrail Triggers by Attack">
          <Bar data={successVsGuard} options={CHART_OPTIONS} />
        </ChartCard>
        <ChartCard title="Average Response Latency by Attack">
          <Bar data={latencyByAttack} options={CHART_OPTIONS} />
        </ChartCard>
        <ChartCard title="Latency Timeline (last 50 runs)" className="lg:col-span-2">
          <Line data={timeline} options={CHART_OPTIONS} />
        </ChartCard>
      </div>

      <ModelBreakdown byModel={metrics.by_model} />
    </div>
  );
}

function ChartCard({ title, children, className = "" }) {
  return (
    <div className={`aegis-card p-4 ${className}`}>
      <h2 className="text-sm uppercase text-aegis-muted mb-3">{title}</h2>
      <div className="h-72">{children}</div>
    </div>
  );
}

function ModelBreakdown({ byModel }) {
  const entries = Object.entries(byModel);
  if (!entries.length) return null;
  return (
    <div className="aegis-card p-4">
      <h2 className="text-sm uppercase text-aegis-muted mb-3">Per-model breakdown</h2>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-aegis-muted text-xs uppercase">
              <th className="py-2 pr-4">Model</th>
              <th className="py-2 pr-4">Runs</th>
              <th className="py-2 pr-4">Success rate</th>
              <th className="py-2 pr-4">Guardrail trigger rate</th>
              <th className="py-2 pr-4">Avg latency</th>
            </tr>
          </thead>
          <tbody>
            {entries.map(([model, stats]) => (
              <tr key={model} className="border-t border-aegis-border">
                <td className="py-2 pr-4 font-mono">{model}</td>
                <td className="py-2 pr-4">{stats.runs}</td>
                <td className="py-2 pr-4 text-aegis-danger">
                  {(stats.success_rate * 100).toFixed(1)}%
                </td>
                <td className="py-2 pr-4 text-aegis-safe">
                  {(stats.guardrail_trigger_rate * 100).toFixed(1)}%
                </td>
                <td className="py-2 pr-4">{stats.avg_latency_ms.toFixed(0)} ms</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
