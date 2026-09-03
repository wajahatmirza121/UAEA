import { Link } from "react-router-dom";
import { Calendar, ArrowRight } from "lucide-react";
import Badge from "@/components/ui/Badge";
import { fmtDate, daysSince } from "@/lib/format";
import { useApp } from "@/context/AppContext";

/**
 * Upcoming dates, pulled live from the same deadline table the assistant
 * quotes. Anyone landing here in admission season wants this before anything
 * else on the page.
 */
export default function DeadlineStrip() {
  const { store } = useApp();

  const upcoming = store.deadlines
    .filter((d) => daysSince(d.date) < 0)
    .sort((a, b) => new Date(a.date) - new Date(b.date))
    .slice(0, 4);

  if (upcoming.length === 0) return null;

  return (
    <section className="st-section tight" style={{ borderTop: "1px solid var(--line)" }}>
      <div className="st-wrap">
        <div
          style={{
            display: "flex",
            alignItems: "flex-end",
            justifyContent: "space-between",
            gap: 16,
            marginBottom: 18,
            flexWrap: "wrap",
          }}
        >
          <div>
            <p className="st-eyebrow">Autumn 2026</p>
            <h2 className="st-h2" style={{ marginBottom: 0 }}>
              Dates coming up
            </h2>
          </div>
          <Link to="/services" className="ua-btn">
            All services
            <ArrowRight size={14} />
          </Link>
        </div>

        <div className="st-grid two">
          {upcoming.map((d) => {
            const left = Math.abs(daysSince(d.date));
            return (
              <div key={d.id} className="st-card" style={{ display: "flex", gap: 14, alignItems: "center" }}>
                <span className="st-card-icon" style={{ marginBottom: 0, flex: "0 0 36px" }}>
                  <Calendar size={17} color="var(--brass)" />
                </span>
                <span style={{ flex: 1, minWidth: 0 }}>
                  <h3 style={{ marginBottom: 3 }}>{d.service}</h3>
                  <p className="ua-num">
                    {fmtDate(d.date)} · {d.semester}
                  </p>
                </span>
                <Badge tone={left <= 21 ? "amber" : "jade"}>
                  <span className="ua-num">{left} days</span>
                </Badge>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
