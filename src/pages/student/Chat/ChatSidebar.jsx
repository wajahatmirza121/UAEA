import { Link } from "react-router-dom";
import { Phone, ArrowRight, Calendar, Trash2 } from "lucide-react";
import Badge from "@/components/ui/Badge";
import Ladder from "@/components/ui/Ladder";
import { fmtDate, daysSince } from "@/lib/format";
import { useApp } from "@/context/AppContext";

/**
 * Context beside the thread: what the conversation is currently about, the
 * office that owns it, and the dates attached to it. Keeps the answer itself
 * short while the supporting detail stays one glance away.
 */
export default function ChatSidebar({ classification, onReset }) {
  const { store } = useApp();
  const service = classification?.service;
  const department = classification?.department;

  const related = service
    ? store.deadlines.filter((d) => d.service.includes(service.en.split(" ")[0])).slice(0, 3)
    : store.deadlines
        .filter((d) => daysSince(d.date) < 0)
        .sort((a, b) => new Date(a.date) - new Date(b.date))
        .slice(0, 3);

  return (
    <aside className="st-aside">
      {service && (
        <div className="st-panel">
          <h4>This is about</h4>
          <div className="st-panel-b">
            <div style={{ fontSize: 14, color: "var(--t1)", fontWeight: 500, marginBottom: 3 }}>
              {service.en}
            </div>
            <div className="ur" style={{ fontSize: 13, color: "var(--t3)", marginBottom: 10 }}>
              {service.ur}
            </div>
            <Badge tone="grey">{service.cat}</Badge>
          </div>
          <Link to={`/services/${service.id}`} className="st-row" style={{ color: "var(--brass)" }}>
            <span style={{ flex: 1 }}>See full requirements</span>
            <ArrowRight size={14} />
          </Link>
        </div>
      )}

      {department && (
        <div className="st-panel">
          <h4>Handled by</h4>
          <div className="st-panel-b" style={{ paddingBottom: 10 }}>
            <div style={{ fontSize: 13.5, color: "var(--t1)", marginBottom: 3 }}>{department.en}</div>
            <div className="ua-num" style={{ fontSize: 12.5 }}>{department.hours}</div>
            <div style={{ marginTop: 10 }}>
              <Ladder verified={department.verified} />
            </div>
          </div>
          <a href={`tel:${department.phone}`} className="st-row" style={{ color: "var(--brass)" }}>
            <Phone size={14} />
            <span className="ua-num">{department.phone}</span>
          </a>
        </div>
      )}

      <div className="st-panel">
        <h4>{service ? "Related dates" : "Coming up"}</h4>
        {related.length === 0 ? (
          <div className="st-panel-b">No upcoming dates recorded for this service.</div>
        ) : (
          related.map((d) => {
            const left = daysSince(d.date);
            return (
              <div key={d.id} className="st-row">
                <Calendar size={14} color="var(--t3)" />
                <span style={{ flex: 1, minWidth: 0 }}>
                  <span style={{ display: "block", fontSize: 13 }}>{d.service}</span>
                  <span className="ua-num" style={{ fontSize: 11.5, color: "var(--t3)" }}>
                    {fmtDate(d.date)}
                  </span>
                </span>
                {left < 0 && (
                  <Badge tone={Math.abs(left) <= 21 ? "amber" : "grey"}>
                    <span className="ua-num">{Math.abs(left)}d</span>
                  </Badge>
                )}
              </div>
            );
          })
        )}
      </div>

      <button className="ua-btn block" onClick={onReset}>
        <Trash2 size={14} />
        Start over
      </button>
    </aside>
  );
}
