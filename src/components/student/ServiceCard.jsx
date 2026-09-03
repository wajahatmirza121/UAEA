import { Link } from "react-router-dom";
import { FileText, Banknote, Calendar } from "lucide-react";
import Badge from "@/components/ui/Badge";
import Ladder from "@/components/ui/Ladder";
import { fmtPKR, fmtDate } from "@/lib/format";
import { useApp } from "@/context/AppContext";

/**
 * One service, summarised the way a student scans it: what it costs, when it
 * closes, how many documents, and when a human last checked all three.
 */
export default function ServiceCard({ service, fee, deadline }) {
  const { urdu } = useApp();

  return (
    <Link to={`/services/${service.id}`} className="st-card">
      <div style={{ display: "flex", alignItems: "flex-start", gap: 10, marginBottom: 8 }}>
        <span style={{ flex: 1, minWidth: 0 }}>
          <h3>{urdu ? service.ur : service.en}</h3>
          <span
            className={urdu ? "" : "ur"}
            style={{ fontSize: 13, color: "var(--t3)", display: "block" }}
          >
            {urdu ? service.en : service.ur}
          </span>
        </span>
        <Badge tone="grey">{service.cat}</Badge>
      </div>

      <div className="st-meta">
        <span style={{ display: "inline-flex", alignItems: "center", gap: 5 }}>
          <FileText size={13} />
          {(service.checklist || []).length} documents
        </span>

        {fee && (
          <span className="ua-num" style={{ display: "inline-flex", alignItems: "center", gap: 5 }}>
            <Banknote size={13} />
            {fmtPKR(fee.amount)}
          </span>
        )}

        {deadline && (
          <span className="ua-num" style={{ display: "inline-flex", alignItems: "center", gap: 5 }}>
            <Calendar size={13} />
            {fmtDate(deadline.date)}
          </span>
        )}

        <span style={{ marginLeft: "auto" }}>
          <Ladder verified={service.verified} withText={false} />
        </span>
      </div>
    </Link>
  );
}
