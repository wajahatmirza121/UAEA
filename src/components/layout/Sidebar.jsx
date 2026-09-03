import { useState } from "react";
import { NavLink, Link } from "react-router-dom";
import { ChevronLeft, ChevronDown, Check, ExternalLink } from "lucide-react";
import { NAV } from "./nav";
import { ROLES } from "@/lib/rbac";
import { useApp } from "@/context/AppContext";
import { useToast } from "@/context/ToastContext";

export default function Sidebar({ collapsed, setCollapsed, mobileOpen, onNavigate }) {
  const { urdu, role, setRole, user } = useApp();
  const toast = useToast();
  const [popOpen, setPopOpen] = useState(false);

  return (
    <aside className={`ua-side${collapsed ? " collapsed" : ""}${mobileOpen ? " open" : ""}`}>
      <div className="ua-brand">
        <div className="ua-mark">اُ</div>
        <div className="ua-brandtext">
          <b>UAEA Console</b>
          <span>Content governance</span>
        </div>
      </div>

      <nav className="ua-nav">
        {NAV.map((group) => (
          <div key={group.group}>
            <div className="ua-navgroup">{group.group}</div>
            {group.items.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                onClick={onNavigate}
                title={collapsed ? item.en : undefined}
                className={({ isActive }) => `ua-item${isActive ? " on" : ""}`}
              >
                <item.icon size={16} />
                <span className={`lbl${urdu ? " ur" : ""}`}>{urdu ? item.ur : item.en}</span>
                {item.count ? <span className="ua-count ua-num">{item.count}</span> : null}
              </NavLink>
            ))}
          </div>
        ))}
      </nav>

      <div className="ua-sidefoot">
        {popOpen && (
          <>
            {/* Click-away catcher, sits under the popover but over the page. */}
            <div
              style={{ position: "fixed", inset: 0, zIndex: 45 }}
              onClick={() => setPopOpen(false)}
            />
            <div className="ua-pop">
              <div className="ua-pop-h">
                Signed in as {user.name}. Switch role to preview what each level of access can see.
              </div>
              {Object.entries(ROLES).map(([key, r]) => (
                <button
                  key={key}
                  className={`ua-pop-row${role === key ? " on" : ""}`}
                  onClick={() => {
                    setRole(key);
                    setPopOpen(false);
                    toast("Role switched", `Console is now showing ${r.label} access.`);
                  }}
                >
                  <span style={{ flex: 1 }}>
                    <b>{r.label}</b>
                    <span>{r.note}</span>
                  </span>
                  {role === key && <Check size={14} style={{ marginTop: 2, color: "var(--brass)" }} />}
                </button>
              ))}
            </div>
          </>
        )}

        <button className="ua-user" onClick={() => setPopOpen((v) => !v)}>
          <span className="ua-av">{user.initials}</span>
          <span className="ua-userinfo">
            <b>{user.name}</b>
            <span>{ROLES[role].label}</span>
          </span>
          <ChevronDown
            size={14}
            className="ua-userchev"
            color="var(--t3)"
            style={{ transform: popOpen ? "rotate(180deg)" : "none", transition: "transform .2s" }}
          />
        </button>

        <Link to="/" className="ua-item" style={{ marginTop: 4 }} title="Open the student site">
          <ExternalLink size={16} />
          <span className="lbl">Student site</span>
        </Link>

        <button className="ua-item" onClick={() => setCollapsed(!collapsed)}>
          <ChevronLeft
            size={16}
            style={{ transform: collapsed ? "rotate(180deg)" : "none", transition: "transform .26s" }}
          />
          <span className="lbl">Collapse</span>
        </button>
      </div>
    </aside>
  );
}
