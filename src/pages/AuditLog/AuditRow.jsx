import Badge from "@/components/ui/Badge";
import DiffRow from "@/components/ui/DiffRow";

export const ACTION_META = {
  create: { label: "Added", tone: "jade" },
  update: { label: "Edited", tone: "sky" },
  verify: { label: "Verified", tone: "jade" },
  delete: { label: "Deleted", tone: "rose" },
  publish: { label: "Published", tone: "violet" },
  guardrail: { label: "Guardrail", tone: "amber" },
};

const NO_CHANGE_TEXT = {
  verify: "Confirmed against the source document, no values changed.",
  delete: "Record removed from the catalogue.",
};

/**
 * One audit entry. Shared by the audit page and the per-record history drawer
 * so a change reads identically in both places.
 */
export default function AuditRow({ entry, compact }) {
  const meta = ACTION_META[entry.action] || { label: entry.action, tone: "grey" };

  return (
    <div className="ua-listitem" style={{ alignItems: "flex-start" }}>
      <span style={{ flex: 1, minWidth: 0 }}>
        <span
          style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap", marginBottom: 4 }}
        >
          <Badge tone={meta.tone}>{meta.label}</Badge>
          {!compact && <span style={{ fontSize: 13, fontWeight: 500 }}>{entry.record}</span>}
          <span className="ua-num" style={{ fontSize: 11.5, color: "var(--t3)" }}>
            {entry.at}
          </span>
        </span>

        {entry.changes.length > 0 ? (
          <span style={{ display: "block" }}>
            {entry.changes.map((c) => (
              <DiffRow key={c.field} field={c.field} from={c.from} to={c.to} />
            ))}
          </span>
        ) : (
          <span style={{ fontSize: 12, color: "var(--t3)" }}>
            {NO_CHANGE_TEXT[entry.action] || "No field changes recorded."}
          </span>
        )}

        <span style={{ fontSize: 11.5, color: "var(--t3)", display: "block", marginTop: 5 }}>
          {entry.actor} · {entry.role}
        </span>
      </span>
    </div>
  );
}
