import { useState, useMemo } from "react";
import { Download } from "lucide-react";
import AuditRow, { ACTION_META } from "./AuditRow";
import TableToolbar from "@/components/data/TableToolbar";
import Button from "@/components/ui/Button";
import EmptyState from "@/components/ui/EmptyState";
import { useDebounced } from "@/hooks/useDebounced";
import { exportCSV } from "@/lib/csv";
import { ISO_TODAY } from "@/lib/constants";
import { useApp } from "@/context/AppContext";
import { useToast } from "@/context/ToastContext";

/**
 * Who changed which fee, deadline or procedure, and when (§9).
 *
 * Append-only by construction: the console has no path to edit or remove an
 * entry, because the first thing anyone asks after a student is quoted the
 * wrong number is who changed it and on what authority.
 */
export default function AuditLog() {
  const { audit } = useApp();
  const toast = useToast();

  const [action, setAction] = useState("all");
  const [actor, setActor] = useState("all");
  const [rawQuery, setRawQuery] = useState("");
  const query = useDebounced(rawQuery);

  const actors = useMemo(() => [...new Set(audit.map((a) => a.actor))], [audit]);

  const rows = useMemo(
    () =>
      audit.filter((a) => {
        if (action !== "all" && a.action !== action) return false;
        if (actor !== "all" && a.actor !== actor) return false;
        if (query && !`${a.record} ${a.actor} ${a.table}`.toLowerCase().includes(query.toLowerCase()))
          return false;
        return true;
      }),
    [audit, action, actor, query]
  );

  const onExport = () => {
    const ok = exportCSV(
      `uaea-audit-${ISO_TODAY}.csv`,
      [
        { label: "Timestamp", value: (r) => r.at },
        { label: "Actor", value: (r) => r.actor },
        { label: "Role", value: (r) => r.role },
        { label: "Action", value: (r) => r.action },
        { label: "Table", value: (r) => r.table },
        { label: "Record", value: (r) => r.record },
        {
          label: "Changes",
          value: (r) => r.changes.map((c) => `${c.field}: ${c.from} to ${c.to}`).join("; "),
        },
      ],
      rows
    );
    toast(
      ok ? "Audit log exported" : "Export blocked",
      ok
        ? `${rows.length} entries saved as CSV.`
        : "Your browser blocked the download. Try again outside a sandboxed frame.",
      ok ? "jade" : "rose"
    );
  };

  return (
    <div className="ua-page">
      <div className="ua-head">
        <div>
          <h1 className="ua-h1">Audit log</h1>
          <p className="ua-sub">
            Who changed which fee, deadline or procedure, and when. Required for a university-facing
            product, and the first thing anyone asks for when a student is quoted the wrong number.
          </p>
        </div>
        <Button icon={Download} onClick={onExport}>
          Export CSV
        </Button>
      </div>

      <div className="ua-card">
        <TableToolbar
          query={rawQuery}
          onQuery={setRawQuery}
          searchPlaceholder="Search records and people"
          filters={[
            {
              key: "action",
              label: "Action",
              width: 138,
              value: action,
              onChange: setAction,
              options: [
                { value: "all", label: "Every action" },
                ...Object.entries(ACTION_META).map(([k, m]) => ({ value: k, label: m.label })),
              ],
            },
            {
              key: "actor",
              label: "Person",
              width: 150,
              value: actor,
              onChange: setActor,
              options: [
                { value: "all", label: "Everyone" },
                ...actors.map((a) => ({ value: a, label: a })),
              ],
            },
          ]}
        />

        {rows.length === 0 ? (
          <EmptyState
            title="No entries match those filters"
            body="Try a different person or action, or clear the search to see the full history."
            action={
              <Button
                onClick={() => {
                  setAction("all");
                  setActor("all");
                  setRawQuery("");
                }}
              >
                Reset filters
              </Button>
            }
          />
        ) : (
          <>
            <div className="ua-list">
              {rows.map((entry) => (
                <AuditRow key={entry.id} entry={entry} />
              ))}
            </div>
            <div className="ua-tfoot">
              <span>Entries are append-only. Nothing here can be edited or removed from the console.</span>
              <span className="ua-num">
                {rows.length} of {audit.length}
              </span>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
