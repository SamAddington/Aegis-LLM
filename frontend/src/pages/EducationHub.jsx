import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api/client.js";

const SEVERITY_STYLE = {
  Critical: "bg-aegis-danger/20 text-aegis-danger",
  High: "bg-aegis-warn/20 text-aegis-warn",
  Medium: "bg-aegis-accent/20 text-aegis-accent",
  Low: "bg-aegis-safe/20 text-aegis-safe",
};

const VULN_TABS = [
  { id: "why", label: "The Why" },
  { id: "how", label: "The How" },
  { id: "defense", label: "The Defense" },
  { id: "examples", label: "Examples" },
  { id: "reading", label: "Further Reading" },
];

const TOP_VIEWS = [
  { id: "basics", label: "LLM Basics (Primer)" },
  { id: "registry", label: "Vulnerability Registry" },
];

export default function EducationHub() {
  const { vulnId } = useParams();
  const [view, setView] = useState(vulnId ? "registry" : "basics");
  const [registry, setRegistry] = useState(null);
  const [primer, setPrimer] = useState(null);
  const [selectedId, setSelectedId] = useState(vulnId || null);
  const [tab, setTab] = useState("why");
  const [filter, setFilter] = useState("All");
  const [primerChapterId, setPrimerChapterId] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        const [reg, pr] = await Promise.all([
          api.listVulnerabilities(),
          api.getPrimer().catch(() => null),
        ]);
        setRegistry(reg);
        setPrimer(pr);
        if (pr?.chapters?.length && !primerChapterId) {
          setPrimerChapterId(pr.chapters[0].id);
        }
        if (!vulnId && reg.vulnerabilities?.length) {
          setSelectedId(reg.vulnerabilities[0].id);
        }
      } catch (e) {
        console.warn("Failed to load education content:", e);
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [vulnId]);

  // Jump to the registry view if a specific vulnId is in the URL.
  useEffect(() => {
    if (vulnId) setView("registry");
  }, [vulnId]);

  const categories = useMemo(() => {
    if (!registry) return [];
    const set = new Set(registry.vulnerabilities.map((v) => v.category));
    return ["All", ...set];
  }, [registry]);

  const filtered = useMemo(() => {
    if (!registry) return [];
    return filter === "All"
      ? registry.vulnerabilities
      : registry.vulnerabilities.filter((v) => v.category === filter);
  }, [registry, filter]);

  const selected = registry?.vulnerabilities.find((v) => v.id === selectedId);

  if (!registry) {
    return <p className="text-aegis-muted">Loading education content...</p>;
  }

  return (
    <div className="space-y-4">
      <div className="aegis-card p-4">
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="text-xl font-bold">Education Hub</h1>
          <span className="text-xs text-aegis-muted">
            {primer && `Primer v${primer.meta?.version || "1.0"} · ~${primer.meta?.reading_time_minutes || 15} min read`}
          </span>
          <div className="ml-auto flex rounded-lg overflow-hidden border border-aegis-border">
            {TOP_VIEWS.map((v) => (
              <button
                key={v.id}
                onClick={() => setView(v.id)}
                className={`px-4 py-1.5 text-sm ${
                  view === v.id
                    ? "bg-aegis-accent/10 text-aegis-accent"
                    : "bg-aegis-panel text-slate-300 hover:text-white"
                }`}
              >
                {v.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {view === "basics" ? (
        <PrimerView
          primer={primer}
          selectedId={primerChapterId}
          setSelectedId={setPrimerChapterId}
        />
      ) : (
        <RegistryView
          categories={categories}
          filter={filter}
          setFilter={setFilter}
          filtered={filtered}
          selected={selected}
          selectedId={selectedId}
          setSelectedId={setSelectedId}
          tab={tab}
          setTab={setTab}
        />
      )}
    </div>
  );
}

// ===========================================================================
// Primer view (basics + worked examples + glossary)
// ===========================================================================
function PrimerView({ primer, selectedId, setSelectedId }) {
  if (!primer) {
    return (
      <div className="aegis-card p-6 text-aegis-muted">
        Primer content is not available. Check that the backend is running and
        that <code>vulnerabilities_primer.json</code> exists.
      </div>
    );
  }

  const chapter = primer.chapters.find((c) => c.id === selectedId) || primer.chapters[0];

  return (
    <div className="grid grid-cols-12 gap-5">
      <aside className="col-span-12 lg:col-span-4 xl:col-span-3 space-y-2">
        <div className="aegis-card p-4">
          <h2 className="font-semibold text-slate-100">{primer.meta?.title}</h2>
          {primer.meta?.subtitle && (
            <p className="text-xs text-aegis-muted mt-1">{primer.meta.subtitle}</p>
          )}
        </div>
        <ul className="space-y-1">
          {primer.chapters.map((c) => (
            <li key={c.id}>
              <button
                onClick={() => setSelectedId(c.id)}
                className={`w-full text-left p-3 rounded-lg border transition-colors ${
                  c.id === chapter.id
                    ? "border-aegis-accent bg-aegis-accent/5"
                    : "border-aegis-border bg-aegis-panel hover:border-slate-500"
                }`}
              >
                <h3 className="font-semibold text-sm leading-snug">{c.title}</h3>
                {c.summary && (
                  <p className="text-xs text-aegis-muted mt-1 line-clamp-2">
                    {c.summary}
                  </p>
                )}
              </button>
            </li>
          ))}
        </ul>
      </aside>

      <section className="col-span-12 lg:col-span-8 xl:col-span-9">
        <article className="aegis-card p-6 space-y-5">
          <header>
            <h1 className="text-2xl font-bold">{chapter.title}</h1>
            {chapter.summary && (
              <p className="text-aegis-muted mt-2">{chapter.summary}</p>
            )}
          </header>

          {chapter.body && chapter.body.length > 0 && (
            <div className="space-y-3 leading-relaxed text-slate-200">
              {chapter.body.map((para, i) => (
                <p key={i}>{para}</p>
              ))}
            </div>
          )}

          {chapter.key_terms && chapter.key_terms.length > 0 && (
            <div>
              <h2 className="text-lg font-semibold mb-2">Key terms</h2>
              <div className="grid md:grid-cols-2 gap-2">
                {chapter.key_terms.map((t, i) => (
                  <div
                    key={i}
                    className="bg-aegis-bg border border-aegis-border rounded-lg p-3"
                  >
                    <div className="font-semibold text-sm text-aegis-accent">
                      {t.term}
                    </div>
                    <div className="text-sm text-slate-300 mt-1">{t.definition}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {chapter.worked_example && (
            <div>
              <h2 className="text-lg font-semibold mb-2">
                Worked example: {chapter.worked_example.title}
              </h2>
              {chapter.worked_example.narrative && (
                <p className="text-slate-300">{chapter.worked_example.narrative}</p>
              )}
              {chapter.worked_example.code && (
                <pre className="mt-2 bg-aegis-bg border border-aegis-border rounded-lg p-4 text-xs font-mono whitespace-pre-wrap text-slate-100">
                  {chapter.worked_example.code}
                </pre>
              )}
              {chapter.worked_example.explanation && (
                <p className="text-sm text-slate-300 mt-2 italic">
                  {chapter.worked_example.explanation}
                </p>
              )}
            </div>
          )}

          {chapter.glossary && (
            <div>
              <h2 className="text-lg font-semibold mb-2">Glossary</h2>
              <dl className="divide-y divide-aegis-border">
                {chapter.glossary.map((g, i) => (
                  <div
                    key={i}
                    className="grid grid-cols-1 md:grid-cols-[220px_1fr] gap-2 py-3"
                  >
                    <dt className="font-semibold text-slate-100">{g.term}</dt>
                    <dd className="text-sm text-slate-300">{g.definition}</dd>
                  </div>
                ))}
              </dl>
            </div>
          )}

          {chapter.references && chapter.references.length > 0 && (
            <div>
              <h2 className="text-lg font-semibold mb-2">References</h2>
              <ul className="space-y-2">
                {chapter.references.map((r, i) => (
                  <li key={i} className="text-sm">
                    <a
                      href={r.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-aegis-accent hover:underline font-medium"
                    >
                      {r.label}
                    </a>
                    {r.note && (
                      <span className="text-aegis-muted"> — {r.note}</span>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </article>
      </section>
    </div>
  );
}

// ===========================================================================
// Vulnerability registry view
// ===========================================================================
function RegistryView({
  categories,
  filter,
  setFilter,
  filtered,
  selected,
  setSelectedId,
  tab,
  setTab,
}) {
  return (
    <div className="grid grid-cols-12 gap-5">
      <aside className="col-span-12 lg:col-span-4 xl:col-span-3 space-y-3">
        <div className="aegis-card p-4">
          <label className="block text-xs uppercase text-aegis-muted mb-1">
            Category
          </label>
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="aegis-input"
          >
            {categories.map((c) => (
              <option key={c}>{c}</option>
            ))}
          </select>
        </div>
        <ul className="space-y-2">
          {filtered.map((v) => (
            <li key={v.id}>
              <button
                onClick={() => setSelectedId(v.id)}
                className={`w-full text-left p-3 rounded-lg border transition-colors ${
                  v.id === selected?.id
                    ? "border-aegis-accent bg-aegis-accent/5"
                    : "border-aegis-border bg-aegis-panel hover:border-slate-500"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs text-aegis-muted">{v.owasp_id}</span>
                  <span
                    className={`aegis-pill ${
                      SEVERITY_STYLE[v.severity] || "bg-slate-700 text-slate-200"
                    }`}
                  >
                    {v.severity}
                  </span>
                </div>
                <h3 className="font-semibold mt-1">{v.name}</h3>
                <p className="text-xs text-aegis-muted mt-1">{v.category}</p>
              </button>
            </li>
          ))}
        </ul>
      </aside>

      <section className="col-span-12 lg:col-span-8 xl:col-span-9">
        {selected ? (
          <VulnerabilityDetail vuln={selected} tab={tab} setTab={setTab} />
        ) : (
          <p className="text-aegis-muted">Select a vulnerability to learn more.</p>
        )}
      </section>
    </div>
  );
}

function VulnerabilityDetail({ vuln, tab, setTab }) {
  // Auto-switch to an available tab if the selected one has no content for
  // the current vuln (e.g. older entries that don't have 'examples' yet).
  const hasExamples = Array.isArray(vuln.detailed_examples) && vuln.detailed_examples.length > 0;
  const hasReading = Array.isArray(vuln.further_reading) && vuln.further_reading.length > 0;

  const availableTabs = VULN_TABS.filter((t) => {
    if (t.id === "examples") return hasExamples;
    if (t.id === "reading") return hasReading;
    return true;
  });

  const effectiveTab = availableTabs.find((t) => t.id === tab) ? tab : availableTabs[0].id;

  return (
    <article className="aegis-card p-6 space-y-5">
      <header className="flex flex-wrap items-start gap-3">
        <div className="flex-1">
          <div className="flex items-center gap-2 text-xs text-aegis-muted uppercase">
            <span>{vuln.owasp_id}</span>
            <span>·</span>
            <span>{vuln.category}</span>
          </div>
          <h1 className="text-2xl font-bold mt-1">{vuln.name}</h1>
        </div>
        <span
          className={`aegis-pill ${
            SEVERITY_STYLE[vuln.severity] || "bg-slate-700 text-slate-200"
          }`}
        >
          {vuln.severity}
        </span>
      </header>

      <div className="bg-aegis-bg border border-aegis-border rounded-lg p-4">
        <div className="text-xs uppercase text-aegis-muted mb-1">Blast Radius</div>
        <p className="text-sm text-slate-200">{vuln.blast_radius}</p>
      </div>

      <div className="flex gap-1 border-b border-aegis-border flex-wrap">
        {availableTabs.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px ${
              effectiveTab === t.id
                ? "border-aegis-accent text-aegis-accent"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {effectiveTab === "why" && (
        <Panel title={vuln.why.title}>
          <p className="text-slate-200">{vuln.why.explanation}</p>
          {vuln.why.analogy && (
            <blockquote className="mt-3 border-l-2 border-aegis-accent pl-3 text-aegis-muted italic">
              {vuln.why.analogy}
            </blockquote>
          )}
        </Panel>
      )}

      {effectiveTab === "how" && (
        <Panel title={vuln.how.title}>
          <ol className="list-decimal ml-5 space-y-1 text-slate-200">
            {vuln.how.steps.map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ol>
          {vuln.how.sample_payload && (
            <>
              <div className="text-xs uppercase text-aegis-muted mt-4 mb-1">
                Sample payload
              </div>
              <pre className="bg-aegis-bg border border-aegis-border rounded p-3 text-xs font-mono whitespace-pre-wrap text-aegis-danger">
                {vuln.how.sample_payload}
              </pre>
            </>
          )}
        </Panel>
      )}

      {effectiveTab === "defense" && (
        <Panel title={vuln.defense.title}>
          <ul className="list-disc ml-5 space-y-1 text-slate-200">
            {vuln.defense.techniques.map((t, i) => (
              <li key={i}>{t}</li>
            ))}
          </ul>
          <div className="grid md:grid-cols-2 gap-3 mt-4">
            <CodeBlock label="Vulnerable" tone="danger" code={vuln.defense.vulnerable_code} />
            <CodeBlock label="Hardened" tone="safe" code={vuln.defense.secure_code} />
          </div>
        </Panel>
      )}

      {effectiveTab === "examples" && hasExamples && (
        <Panel title="Worked examples (easy → hard)">
          <div className="space-y-4">
            {vuln.detailed_examples.map((ex, i) => (
              <ExampleCard key={i} index={i} example={ex} />
            ))}
          </div>
        </Panel>
      )}

      {effectiveTab === "reading" && hasReading && (
        <Panel title="Further reading">
          <ul className="space-y-2">
            {vuln.further_reading.map((r, i) => (
              <li key={i} className="text-sm">
                <a
                  href={r.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-aegis-accent hover:underline font-medium"
                >
                  {r.label}
                </a>
                {r.note && <span className="text-aegis-muted"> — {r.note}</span>}
              </li>
            ))}
          </ul>
        </Panel>
      )}
    </article>
  );
}

function ExampleCard({ index, example }) {
  return (
    <div className="border border-aegis-border rounded-lg overflow-hidden">
      <div className="bg-aegis-bg px-4 py-2 flex items-center gap-2">
        <span className="aegis-pill bg-aegis-accent/20 text-aegis-accent text-[11px]">
          #{index + 1}
        </span>
        <h3 className="font-semibold">{example.title}</h3>
      </div>
      <div className="p-4 space-y-3">
        {example.scenario && (
          <div>
            <div className="text-xs uppercase text-aegis-muted mb-1">Scenario</div>
            <p className="text-sm text-slate-200">{example.scenario}</p>
          </div>
        )}
        {example.attacker_input && (
          <div>
            <div className="text-xs uppercase text-aegis-muted mb-1">
              Attacker input
            </div>
            <pre className="bg-aegis-bg border border-aegis-danger/30 rounded p-3 text-xs font-mono whitespace-pre-wrap text-aegis-danger">
              {example.attacker_input}
            </pre>
          </div>
        )}
        {example.why_it_may_work && (
          <div>
            <div className="text-xs uppercase text-aegis-muted mb-1">
              Why it can work
            </div>
            <p className="text-sm text-slate-200">{example.why_it_may_work}</p>
          </div>
        )}
        {example.defender_view && (
          <div>
            <div className="text-xs uppercase text-aegis-muted mb-1">
              Defender view
            </div>
            <p className="text-sm text-aegis-safe">{example.defender_view}</p>
          </div>
        )}
      </div>
    </div>
  );
}

function Panel({ title, children }) {
  return (
    <div>
      <h2 className="text-lg font-semibold mb-2">{title}</h2>
      {children}
    </div>
  );
}

function CodeBlock({ label, tone, code }) {
  const tones = {
    danger: "border-aegis-danger/40 text-aegis-danger",
    safe: "border-aegis-safe/40 text-aegis-safe",
  };
  return (
    <div className={`border rounded-lg overflow-hidden ${tones[tone]}`}>
      <div className="px-3 py-1.5 bg-aegis-bg border-b border-aegis-border text-xs uppercase">
        {label}
      </div>
      <pre className="bg-aegis-bg p-3 text-xs font-mono whitespace-pre-wrap text-slate-100">
        {code}
      </pre>
    </div>
  );
}
