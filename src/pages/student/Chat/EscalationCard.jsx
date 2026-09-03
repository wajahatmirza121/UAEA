import { Phone, Mail, Clock, MessageSquare } from "lucide-react";

/**
 * The hand-off.
 *
 * Shown whenever the assistant could not answer from the records. It gives a
 * specific office with a working number rather than a generic apology — the
 * point of admitting ignorance is to get the student to someone who knows.
 */
export default function EscalationCard({ department, reason }) {
  if (!department) return null;

  return (
    <div className="ua-note brass" style={{ marginTop: 11, display: "block" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 9 }}>
        <MessageSquare size={15} color="var(--brass)" />
        <b style={{ color: "var(--t1)", fontSize: 13 }}>Talk to a person</b>
      </div>

      <p style={{ margin: "0 0 11px", fontSize: 12.5, lineHeight: 1.6 }}>
        {reason || "This is not in my records, so I would rather put you in front of someone who knows."}{" "}
        {department.en} handles this.
      </p>

      <div style={{ display: "grid", gap: 7, fontSize: 13 }}>
        <a href={`tel:${department.phone}`} style={{ display: "flex", alignItems: "center", gap: 9, color: "var(--brass)" }}>
          <Phone size={14} />
          <span className="ua-num">{department.phone}</span>
        </a>
        <a href={`mailto:${department.email}`} style={{ display: "flex", alignItems: "center", gap: 9, color: "var(--t2)" }}>
          <Mail size={14} />
          {department.email}
        </a>
        <span className="ua-num" style={{ display: "flex", alignItems: "center", gap: 9, color: "var(--t2)" }}>
          <Clock size={14} />
          {department.hours}
        </span>
      </div>
    </div>
  );
}
