export default function MitigationToggle({ value, onChange, label = "Aegis Guardrails" }) {
  return (
    <label className="flex items-center gap-3 cursor-pointer select-none">
      <span className="text-sm text-slate-300">{label}</span>
      <button
        type="button"
        role="switch"
        aria-checked={value}
        onClick={() => onChange(!value)}
        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
          value ? "bg-aegis-safe" : "bg-aegis-danger"
        }`}
      >
        <span
          className={`inline-block h-5 w-5 transform rounded-full bg-white transition-transform ${
            value ? "translate-x-5" : "translate-x-1"
          }`}
        />
      </button>
      <span
        className={`aegis-pill ${
          value
            ? "bg-aegis-safe/15 text-aegis-safe"
            : "bg-aegis-danger/15 text-aegis-danger"
        }`}
      >
        {value ? "Defense ON" : "Defense OFF"}
      </span>
    </label>
  );
}
