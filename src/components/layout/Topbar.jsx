import { useNavigate } from "react-router-dom";
import { Menu, Search, Bell, ScrollText, Sun, Moon } from "lucide-react";
import { useApp } from "@/context/AppContext";

export default function Topbar({ onOpenNav, onOpenCommand }) {
  const { theme, setTheme, urdu, setUrdu } = useApp();
  const navigate = useNavigate();

  return (
    <header className="ua-top">
      <button className="ua-iconbtn ua-mobonly" onClick={onOpenNav} aria-label="Open navigation">
        <Menu size={17} />
      </button>

      <button className="ua-searchbtn" onClick={onOpenCommand}>
        <Search size={14} />
        <span className="txt">Search records, pages and actions</span>
        <span className="ua-kbd">⌘K</span>
      </button>

      <div style={{ flex: 1 }} />

      <div className="ua-langtoggle" role="group" aria-label="Interface language">
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

      <button className="ua-iconbtn" onClick={() => navigate("/admin/queue")} aria-label="Review queue">
        <Bell size={16} />
        <span className="ua-dot" />
      </button>

      <button className="ua-iconbtn" onClick={() => navigate("/admin/audit")} aria-label="Audit log">
        <ScrollText size={16} />
      </button>
    </header>
  );
}
