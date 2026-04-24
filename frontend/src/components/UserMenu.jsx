import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../auth/AuthContext.jsx";

export default function UserMenu() {
  const { user, isAdmin, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    const onClick = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener("click", onClick);
    return () => document.removeEventListener("click", onClick);
  }, []);

  if (!user) return null;

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-2 aegis-btn text-sm"
      >
        <span className="w-7 h-7 rounded-full bg-aegis-accent/20 text-aegis-accent grid place-items-center font-semibold">
          {user.username.charAt(0).toUpperCase()}
        </span>
        <span className="hidden sm:inline">{user.username}</span>
        <span
          className={`aegis-pill text-[10px] ${
            isAdmin ? "bg-aegis-warn/20 text-aegis-warn" : "bg-aegis-border text-slate-300"
          }`}
        >
          {user.role}
        </span>
      </button>
      {open && (
        <div className="absolute right-0 mt-2 w-56 aegis-card py-2 z-30">
          <div className="px-4 py-2 border-b border-aegis-border">
            <div className="text-sm font-medium text-slate-100">{user.username}</div>
            {user.email && (
              <div className="text-xs text-aegis-muted">{user.email}</div>
            )}
          </div>
          <Link
            to="/settings"
            onClick={() => setOpen(false)}
            className="block px-4 py-2 text-sm hover:bg-aegis-border"
          >
            Settings
          </Link>
          <Link
            to="/account"
            onClick={() => setOpen(false)}
            className="block px-4 py-2 text-sm hover:bg-aegis-border"
          >
            Account
          </Link>
          <button
            onClick={() => {
              setOpen(false);
              logout();
            }}
            className="block w-full text-left px-4 py-2 text-sm hover:bg-aegis-border text-aegis-danger"
          >
            Sign out
          </button>
        </div>
      )}
    </div>
  );
}
