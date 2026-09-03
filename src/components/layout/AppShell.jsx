import { useState, useCallback } from "react";
import { Outlet, useLocation } from "react-router-dom";
import Sidebar from "./Sidebar";
import Topbar from "./Topbar";
import CommandPalette from "./CommandPalette";
import { useHotkey } from "@/hooks/useHotkey";
import { useApp } from "@/context/AppContext";

/**
 * The frame every page renders inside.
 * Owns only chrome state — sidebar, palette, mobile drawer. Page state stays
 * in the page.
 */
export default function AppShell() {
  const { theme } = useApp();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [cmdOpen, setCmdOpen] = useState(false);
  const location = useLocation();

  useHotkey("k", useCallback(() => setCmdOpen((v) => !v), []));

  return (
    <div className="uaea" data-theme={theme}>
      <div className="ua-shell">
        <div className="ua-glow" />
        {mobileOpen && <div className="ua-backdrop" onClick={() => setMobileOpen(false)} />}

        <Sidebar
          collapsed={collapsed}
          setCollapsed={setCollapsed}
          mobileOpen={mobileOpen}
          onNavigate={() => setMobileOpen(false)}
        />

        <div className="ua-main">
          <Topbar onOpenNav={() => setMobileOpen(true)} onOpenCommand={() => setCmdOpen(true)} />
          {/* key on pathname resets scroll and local state between pages */}
          <main className="ua-scroll" key={location.pathname}>
            <Outlet />
          </main>
        </div>
      </div>

      <CommandPalette open={cmdOpen} onClose={() => setCmdOpen(false)} />
    </div>
  );
}
