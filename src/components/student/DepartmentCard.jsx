import { Phone, Mail, Clock, MapPin } from "lucide-react";
import Ladder from "@/components/ui/Ladder";
import { useApp } from "@/context/AppContext";

/** Contact card. Phone is a tel: link — most students are on a phone. */
export default function DepartmentCard({ department: d }) {
  const { urdu } = useApp();

  return (
    <div className="st-card">
      <h3>{urdu ? d.ur : d.en}</h3>
      <span className={urdu ? "" : "ur"} style={{ fontSize: 13, color: "var(--t3)" }}>
        {urdu ? d.en : d.ur}
      </span>

      <div style={{ display: "grid", gap: 8, marginTop: 14, fontSize: 13 }}>
        <a href={`tel:${d.phone}`} style={{ display: "flex", alignItems: "center", gap: 9, color: "var(--brass)" }}>
          <Phone size={14} />
          <span className="ua-num">{d.phone}</span>
        </a>
        <a href={`mailto:${d.email}`} style={{ display: "flex", alignItems: "center", gap: 9, color: "var(--t2)" }}>
          <Mail size={14} />
          {d.email}
        </a>
        <span style={{ display: "flex", alignItems: "center", gap: 9, color: "var(--t2)" }}>
          <MapPin size={14} />
          {d.campus}
        </span>
        <span className="ua-num" style={{ display: "flex", alignItems: "center", gap: 9, color: "var(--t2)" }}>
          <Clock size={14} />
          {d.hours}
        </span>
      </div>

      <div className="st-meta" style={{ marginTop: 14 }}>
        <span>Checked</span>
        <Ladder verified={d.verified} />
      </div>
    </div>
  );
}
