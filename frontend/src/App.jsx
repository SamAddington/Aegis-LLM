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
import HealthBadge from "./components/HealthBadge.jsx";
import UserMenu from "./components/UserMenu.jsx";
import ProtectedRoute from "./components/ProtectedRoute.jsx";

const NAV = [
  { to: "/", label: "Attack Lab", end: true },
  { to: "/education", label: "Education Hub" },
  { to: "/agentic", label: "Agentic Sandbox" },
  { to: "/stress", label: "Stress Lab" },
  { to: "/multimodal", label: "Multi-Modal" },
  { to: "/dashboard", label: "Dashboard" },
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
                <Route path="/multimodal" element={<MultiModalHub />} />
                <Route path="/dashboard" element={<Dashboard />} />
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
          <nav className="flex items-center gap-1 text-sm overflow-x-auto">
            {NAV.map((item) => (
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
