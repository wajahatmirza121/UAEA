import Drawer from "@/components/ui/Drawer";
import Ladder from "@/components/ui/Ladder";
import EmptyState from "@/components/ui/EmptyState";
import AuditRow from "@/pages/AuditLog/AuditRow";
import { fmtDate } from "@/lib/format";
import { nameOf } from "./columns";

/**
 * Per-record change history, read from the same append-only audit trail that
 * backs the audit page (§9). Same rows, filtered — so the two views can never
 * disagree about what happened.
 */
export default function RecordHistory({ record, audit, onClose }) {
  const entries = record ? audit.filter((a) => a.recordId === record.id) : [];

  return (
    <Drawer
      open={Boolean(record)}
      onClose={onClose}
      title={record ? nameOf(record) : ""}
      desc="Every change to this record, most recent first."
    >
      {record && (
        <>
          <div
            style={{
              padding: "15px 20px",
              borderBottom: "1px solid var(--line)",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              gap: 12,
            }}
          >
            <span style={{ fontSize: 12.5, color: "var(--t2)" }}>
              Last verified by {record.by} on {fmtDate(record.verified)}
            </span>
            <Ladder verified={record.verified} />
          </div>

          {entries.length === 0 ? (
            <EmptyState
              title="No changes recorded"
              body="This record has not been edited since the catalogue was first loaded. Edits and verifications will appear here."
            />
          ) : (
            <div className="ua-list">
              {entries.map((a) => (
                <AuditRow key={a.id} entry={a} compact />
              ))}
            </div>
          )}
        </>
      )}
    </Drawer>
  );
}
