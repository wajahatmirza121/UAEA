import { NavLink, Link } from "react-router-dom";
import { Sun, Moon, ShieldCheck } from "lucide-react";
import { useApp } from "@/context/AppContext";

const LINKS = [
  { to: "/chat", en: "Ask", ur: "سوال" },
  { to: "/services", en: "Services", ur: "خدمات" },
  { to: "/directory", en: "Departments", ur: "شعبے" },
];

export default function StudentHeader() {
  const { theme, setTheme, urdu, setUrdu } = useApp();

  return (
    <header className="st-head">
      <div className="st-head-in">
        <Link to="/" className="st-logo">
          <span className="ua-mark">اُ</span>
          <span>
            <b>UAEA</b>
            <span>{urdu ? "طلبہ معاون" : "Student assistant"}</span>
          </span>
        </Link>

        <nav className="st-links">
          {LINKS.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              className={({ isActive }) => `st-link${isActive ? " on" : ""}`}
            >
              <span className={urdu ? "ur" : ""}>{urdu ? l.ur : l.en}</span>
            </NavLink>
          ))}

          <div className="ua-langtoggle" style={{ marginLeft: 6 }} role="group" aria-label="Language">
            <button className={!urdu ? "on" : ""} onClick={() => setUrdu(false)}>
              EN
            </button>
            <button className={urdu ? "on" : ""} onClick={() => setUrdu(true)}>
              اردو
            </button>
          </div>

          <button
            className="ua-iconbtn"
            onClick={() => setTheme(theme === "light" ? "dark" : "light")}
            aria-label={`Switch to ${theme === "light" ? "dark" : "light"} theme`}
          >
            {theme === "light" ? <Moon size={16} /> : <Sun size={16} />}
          </button>

          <Link to="/admin" className="st-link hide-sm" title="Staff only">
            <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
              <ShieldCheck size={14} />
              Staff
            </span>
          </Link>
        </nav>
      </div>
    </header>
  );
}
