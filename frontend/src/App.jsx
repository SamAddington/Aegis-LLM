import { Link, NavLink, Route, Routes, useLocation } from "react-router-dom";
import AttackLab from "./pages/AttackLab.jsx";
import EducationHub from "./pages/EducationHub.jsx";
import AgenticSandbox from "./pages/AgenticSandbox.jsx";
import StressLab from "./pages/StressLab.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import MultiModalHub from "./pages/MultiModalHub.jsx";
import Login from "./pages/Login.jsx";
import Register from "./pages/Register.jsx";
import Settings from "./pages/Settings.jsx";
import Account from "./pages/Account.jsx";
import ComplianceHub from "./pages/ComplianceHub.jsx";
import AuditHub from "./pages/AuditHub.jsx";
import OutputSinksLab from "./pages/OutputSinksLab.jsx";
import SupplyChainLab from "./pages/SupplyChainLab.jsx";
import VectorEmbeddingLab from "./pages/VectorEmbeddingLab.jsx";
import MisinformationLab from "./pages/MisinformationLab.jsx";
import MultiAgentLab from "./pages/MultiAgentLab.jsx";
import BeaverTailsEvalLab from "./pages/BeaverTailsEvalLab.jsx";
import PrivacyLab from "./pages/PrivacyLab.jsx";
import PoisoningLab from "./pages/PoisoningLab.jsx";
import HealthBadge from "./components/HealthBadge.jsx";
import UserMenu from "./components/UserMenu.jsx";
import ProtectedRoute from "./components/ProtectedRoute.jsx";

const NAV_PRIMARY = [
  { to: "/", label: "Attack Lab", end: true },
  { to: "/education", label: "Education Hub" },
  { to: "/dashboard", label: "Dashboard" },
];

const NAV_LABS = [
  { to: "/agentic", label: "Agentic Sandbox" },
  { to: "/stress", label: "Stress Lab" },
  { to: "/sinks", label: "Output Sinks" },
  { to: "/supply-chain", label: "Supply Chain" },
  { to: "/vector", label: "Vector/Embedding" },
  { to: "/privacy", label: "Privacy / Secrets" },
  { to: "/poisoning", label: "Poisoning" },
  { to: "/misinfo", label: "Misinformation" },
  { to: "/multi-agent", label: "Multi-agent" },
  { to: "/beavertails", label: "BeaverTails Eval" },
  { to: "/multimodal", label: "Multi-Modal" },
];

const NAV_ADMIN = [
  { to: "/compliance", label: "Compliance Hub" },
  { to: "/audit", label: "Audit" },
  { to: "/settings", label: "Settings" },
];

const STANDALONE_PATHS = ["/login", "/register"];

export default function App() {
  const location = useLocation();
  const standalone = STANDALONE_PATHS.includes(location.pathname);

  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route
        path="*"
        element={
          <ProtectedRoute>
            <Shell>
              <Routes>
                <Route path="/" element={<AttackLab />} />
                <Route path="/education" element={<EducationHub />} />
                <Route path="/education/:vulnId" element={<EducationHub />} />
                <Route path="/agentic" element={<AgenticSandbox />} />
                <Route path="/stress" element={<StressLab />} />
                <Route path="/sinks" element={<OutputSinksLab />} />
                <Route path="/supply-chain" element={<SupplyChainLab />} />
                <Route path="/vector" element={<VectorEmbeddingLab />} />
                <Route path="/privacy" element={<PrivacyLab />} />
                <Route path="/poisoning" element={<PoisoningLab />} />
                <Route path="/misinfo" element={<MisinformationLab />} />
                <Route path="/multi-agent" element={<MultiAgentLab />} />
                <Route path="/beavertails" element={<BeaverTailsEvalLab />} />
                <Route path="/multimodal" element={<MultiModalHub />} />
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/compliance" element={<ComplianceHub />} />
                <Route path="/audit" element={<AuditHub />} />
                <Route path="/settings" element={<Settings />} />
                <Route path="/account" element={<Account />} />
              </Routes>
            </Shell>
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}

function Shell({ children }) {
  const location = useLocation();
  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-aegis-border bg-aegis-panel/70 backdrop-blur sticky top-0 z-20">
        <div className="max-w-[1400px] mx-auto px-6 py-3 flex items-center gap-6">
          <Link to="/" className="flex items-center gap-2">
            <span className="text-xl font-bold tracking-tight">
              <span className="text-aegis-accent">Aegis</span>-LLM
            </span>
            <span className="aegis-pill bg-aegis-border text-slate-300">
              Pentesting Lab
            </span>
          </Link>
          <nav className="flex items-center gap-1 text-sm">
            {NAV_PRIMARY.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  `px-3 py-1.5 rounded-md transition-colors whitespace-nowrap ${
                    isActive
                      ? "bg-aegis-accent/10 text-aegis-accent"
                      : "text-slate-400 hover:text-slate-100 hover:bg-aegis-border"
                  }`
                }
              >
                {item.label}
              </NavLink>
            ))}

            <NavDropdown
              label="Labs"
              items={NAV_LABS}
              currentPath={location.pathname}
            />
            <NavDropdown
              label="Admin"
              items={NAV_ADMIN}
              currentPath={location.pathname}
            />
          </nav>
          <div className="ml-auto flex items-center gap-3">
            <HealthBadge />
            <UserMenu />
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-[1400px] mx-auto w-full px-6 py-6">{children}</main>

      <footer className="border-t border-aegis-border py-4 text-center text-xs text-aegis-muted space-y-1">
        <div>
          <span className="font-semibold text-slate-300">Aegis-LLM</span>
          {" · "}Research artifact by{" "}
          <span className="text-slate-300">Samuel Addington</span>
          {" · "}Author &amp; maintainer
        </div>
        <div>
          Designed and developed as an artifact of research into LLM security.
          For isolated research and classroom use only — do not deploy against
          systems you do not own.
        </div>
      </footer>
    </div>
  );
}

function NavDropdown({ label, items, currentPath }) {
  const active = items.some((i) => currentPath === i.to || currentPath.startsWith(i.to + "/"));
  return (
    <details className="relative">
      <summary
        className={`list-none cursor-pointer select-none px-3 py-1.5 rounded-md transition-colors whitespace-nowrap ${
          active
            ? "bg-aegis-accent/10 text-aegis-accent"
            : "text-slate-400 hover:text-slate-100 hover:bg-aegis-border"
        }`}
      >
        {label}
      </summary>
      <div className="absolute left-0 mt-2 min-w-56 bg-aegis-panel border border-aegis-border rounded-lg overflow-hidden z-30">
        <div className="py-1">
          {items.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `block px-3 py-2 text-sm transition-colors ${
                  isActive
                    ? "bg-aegis-accent/10 text-aegis-accent"
                    : "text-slate-300 hover:bg-aegis-border hover:text-slate-100"
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </div>
      </div>
    </details>
  );
}
