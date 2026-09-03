import { useState } from "react";
import Badge from "@/components/ui/Badge";
import ReadOnlyNotice from "@/components/ui/ReadOnlyNotice";
import { ESCALATIONS } from "@/mocks";
import { can } from "@/lib/rbac";
import { useApp } from "@/context/AppContext";
import { useToast } from "@/context/ToastContext";

const STATUS_TABS = [
  ["all", "All"],
  ["open", "Open"],
  ["in_progress", "In progress"],
  ["resolved", "Resolved"],
];

const STATUS_OPTIONS = [
  ["open", "Open"],
  ["in_progress", "In progress"],
  ["waiting", "Waiting on student"],
  ["resolved", "Resolved"],
];

function StatusPill({ status }) {
  if (status === "open") return <Badge tone="rose">Open</Badge>;
  if (status === "in_progress") return <Badge tone="sky">In progress</Badge>;
  if (status === "waiting") return <Badge tone="amber">Waiting on student</Badge>;
  return <Badge tone="jade">Resolved</Badge>;
}

/**
 * Tickets the assistant handed to staff because it could not answer safely.
 * Worth reading as a to-do list for the catalogue: most of these close by
 * adding a field that was missing, not by replying to the student.
 */
export default function Escalations() {
  const { role } = useApp();
  const toast = useToast();
  const [rows, setRows] = useState(ESCALATIONS);
  const [status, setStatus] = useState("all");

  const mayWrite = can(role, "escalations.write");
  const shown = rows.filter((r) => status === "all" || r.status === status);

  // ↯ API SEAM — PATCH /v1/admin/escalations/{id}
  const setRowStatus = (id, next) => {
    setRows((prev) => prev.map((r) => (r.id === id ? { ...r, status: next } : r)));
    toast("Ticket updated", `${id} is now ${next.replace("_", " ")}.`);
  };

  return (
    <div className="ua-page">
      <div className="ua-head">
        <div>
          <h1 className="ua-h1">Escalations</h1>
          <p className="ua-sub">
            Handed to staff because the assistant could not answer safely. Clearing a ticket usually
            means a record needs adding.
          </p>
        </div>
        <div className="ua-tabs">
          {STATUS_TABS.map(([key, label]) => (
            <button
              key={key}
              className={`ua-tab${status === key ? " on" : ""}`}
              onClick={() => setStatus(key)}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      <div className="ua-card">
        {!mayWrite && <ReadOnlyNotice role={role} />}

        <div className="ua-tablewrap">
          <table className="ua-table">
            <thead>
              <tr>
                <th style={{ width: 104 }}>Ticket</th>
                <th>Reason</th>
                <th style={{ width: 160 }}>Department</th>
                <th style={{ width: 150 }}>Assigned to</th>
                <th style={{ width: 152 }}>Opened</th>
                <th style={{ width: 176 }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {shown.map((r) => (
                <tr key={r.id}>
                  <td>
                    <span className="ua-num" style={{ fontWeight: 500 }}>
                      {r.id}
                    </span>
                    <div className="ua-num" style={{ fontSize: 11, color: "var(--t3)" }}>
                      {r.conv}
                    </div>
                  </td>
                  <td>
                    <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      {r.priority === "high" && (
                        <span
                          title="High priority"
                          style={{
                            width: 5,
                            height: 5,
                            borderRadius: 5,
                            background: "var(--rose-bright)",
                            flex: "0 0 5px",
                          }}
                        />
                      )}
                      {r.reason}
                    </span>
                  </td>
                  <td style={{ color: "var(--t2)" }}>{r.dept}</td>
                  <td style={{ color: r.assigned === "Unassigned" ? "var(--t3)" : "var(--t1)" }}>
                    {r.assigned}
                  </td>
                  <td className="ua-num" style={{ color: "var(--t2)", fontSize: 12 }}>
                    {r.opened}
                  </td>
                  <td>
                    {mayWrite ? (
                      <select
                        className="ua-select"
                        style={{ height: 30, fontSize: 12 }}
                        value={r.status}
                        onChange={(e) => setRowStatus(r.id, e.target.value)}
                        aria-label={`Status for ${r.id}`}
                      >
                        {STATUS_OPTIONS.map(([value, label]) => (
                          <option key={value} value={value}>
                            {label}
                          </option>
                        ))}
                      </select>
                    ) : (
                      <StatusPill status={r.status} />
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="ua-tfoot">
          <span style={{ display: "flex", alignItems: "center", gap: 9, flexWrap: "wrap" }}>
            {STATUS_OPTIONS.map(([key]) => key)
              .filter((key) => rows.some((r) => r.status === key))
              .map((key) => (
                <span key={key} style={{ display: "inline-flex", alignItems: "center", gap: 5 }}>
                  <StatusPill status={key} />
                  <span className="ua-num">{rows.filter((r) => r.status === key).length}</span>
                </span>
              ))}
          </span>
          <span className="ua-num">
            {shown.length} of {rows.length} tickets
          </span>
        </div>
      </div>
    </div>
  );
}
