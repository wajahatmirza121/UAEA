import { useState, useEffect, useRef, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { Search, CornerDownLeft, Banknote, Upload, RefreshCw, History } from "lucide-react";
import { NAV } from "./nav";
import { can } from "@/lib/rbac";
import { useEscape } from "@/hooks/useEscape";
import { useApp } from "@/context/AppContext";
import { useToast } from "@/context/ToastContext";

/** ⌘K palette. Actions the current role cannot perform are filtered out. */
export default function CommandPalette({ open, onClose }) {
  const [query, setQuery] = useState("");
  const [index, setIndex] = useState(0);
  const inputRef = useRef(null);
  const navigate = useNavigate();
  const toast = useToast();
  const { role } = useApp();

  useEscape(open, onClose);

  useEffect(() => {
    if (!open) return;
    setQuery("");
    setIndex(0);
    const t = setTimeout(() => inputRef.current?.focus(), 40);
    return () => clearTimeout(t);
  }, [open]);

  const commands = useMemo(() => {
    const pages = NAV.flatMap((g) =>
      g.items.map((item) => ({
        label: `Go to ${item.en}`,
        icon: item.icon,
        hint: g.group,
        run: () => navigate(item.to),
      }))
    );

    const actions = [
      { label: "Add a fee tariff record", icon: Banknote, hint: "Content", perm: "content.write", run: () => navigate("/admin/content") },
      { label: "Upload a source document", icon: Upload, hint: "Knowledge", perm: "documents.write", run: () => navigate("/admin/documents") },
      {
        label: "Reindex the knowledge base",
        icon: RefreshCw,
        hint: "Knowledge",
        perm: "documents.write",
        run: () => toast("Reindex started", "1,842 chunks queued for re-embedding."),
      },
      { label: "Review who changed what", icon: History, hint: "System", run: () => navigate("/admin/audit") },
    ];

    return [...pages, ...actions.filter((a) => !a.perm || can(role, a.perm))];
  }, [navigate, toast, role]);

  const results = commands.filter((c) => c.label.toLowerCase().includes(query.toLowerCase()));

  const onKeyDown = (e) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setIndex((p) => (p + 1) % Math.max(results.length, 1));
    }
    if (e.key === "ArrowUp") {
      e.preventDefault();
      setIndex((p) => (p - 1 + results.length) % Math.max(results.length, 1));
    }
    if (e.key === "Enter" && results[index]) {
      results[index].run();
      onClose();
    }
  };

  if (!open) return null;

  return (
    <div className="ua-overlay" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div className="ua-cmd" role="dialog" aria-label="Command palette">
        <div className="ua-cmd-in">
          <Search size={16} color="var(--t3)" />
          <input
            ref={inputRef}
            value={query}
            placeholder="Search commands and pages"
            onChange={(e) => {
              setQuery(e.target.value);
              setIndex(0);
            }}
            onKeyDown={onKeyDown}
          />
          <span className="ua-kbd" style={{ margin: 0 }}>
            Esc
          </span>
        </div>

        <div className="ua-cmd-list">
          {results.length === 0 ? (
            <div style={{ padding: "26px 14px", textAlign: "center", fontSize: 12.5, color: "var(--t3)" }}>
              No command matches that. Try “fee”, “upload” or a page name.
            </div>
          ) : (
            results.map((c, i) => (
              <button
                key={c.label}
                className={`ua-cmd-row${i === index ? " on" : ""}`}
                onMouseEnter={() => setIndex(i)}
                onClick={() => {
                  c.run();
                  onClose();
                }}
              >
                <c.icon size={15} />
                <span>{c.label}</span>
                <span className="hint">{c.hint}</span>
                {i === index && <CornerDownLeft size={13} style={{ marginLeft: 6, opacity: 0.6 }} />}
              </button>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
