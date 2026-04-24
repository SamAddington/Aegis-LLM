export default function ConsolePanel({ title, accent = "slate", children, footer }) {
  const accentClasses = {
    red: "border-aegis-danger/60",
    cyan: "border-aegis-accent/60",
    green: "border-aegis-safe/60",
    amber: "border-aegis-warn/60",
    slate: "border-aegis-border",
  };
  return (
    <div className={`aegis-card border-l-4 ${accentClasses[accent]} h-full flex flex-col`}>
      <div className="px-4 py-3 border-b border-aegis-border flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wide">
          {title}
        </h3>
      </div>
      <div className="flex-1 overflow-auto p-4 font-mono text-xs leading-relaxed">
        {children}
      </div>
      {footer && (
        <div className="border-t border-aegis-border px-4 py-2 text-xs text-aegis-muted">
          {footer}
        </div>
      )}
    </div>
  );
}
