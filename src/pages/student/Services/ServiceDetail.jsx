import { Link, useParams, useNavigate } from "react-router-dom";
import { ArrowLeft, MessageSquare, Phone, Calendar, Banknote, ShieldCheck } from "lucide-react";
import Badge from "@/components/ui/Badge";
import Ladder from "@/components/ui/Ladder";
import Button from "@/components/ui/Button";
import Note from "@/components/ui/Note";
import EmptyState from "@/components/ui/EmptyState";
import { CATEGORY_DEPARTMENT } from "@/mocks/routing";
import { fmtDate, fmtPKR, daysSince } from "@/lib/format";
import { freshness } from "@/lib/freshness";
import { useApp } from "@/context/AppContext";

/**
 * Everything a student needs before they travel to a campus counter.
 *
 * The original-versus-copy flag on each document is the detail that saves a
 * second trip, so it gets its own badge rather than being buried in prose.
 */
export default function ServiceDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { store, urdu } = useApp();

  const service = store.services.find((s) => s.id === id);

  if (!service) {
    return (
      <div className="st-wrap st-section">
        <div className="st-card">
          <EmptyState
            title="That service is not listed"
            body="It may have been renamed. Browse the full list, or ask the assistant in your own words."
            action={<Link to="/services" className="ua-btn">All services</Link>}
          />
        </div>
      </div>
    );
  }

  const department = store.departments.find((d) => d.id === CATEGORY_DEPARTMENT[service.cat]);
  const fee = store.fees.find((f) => f.program === service.en.split(" ")[0] || f.program === service.en);
  const deadline = store.deadlines.find((d) => d.service === service.en);
  const stale = freshness(service.verified).tone !== "jade";
  const procedure = urdu ? service.procedure_ur : service.procedure_en;

  return (
    <div className="st-wrap st-section">
      <Link
        to="/services"
        style={{ display: "inline-flex", alignItems: "center", gap: 7, fontSize: 13, color: "var(--t2)", marginBottom: 18 }}
      >
        <ArrowLeft size={14} />
        All services
      </Link>

      <div style={{ marginBottom: 24 }}>
        <Badge tone="grey">{service.cat}</Badge>
        <h1 className="st-h2" style={{ fontSize: 30, margin: "12px 0 4px" }}>
          {urdu ? service.ur : service.en}
        </h1>
        <p className={urdu ? "" : "ur"} style={{ fontSize: 18, color: "var(--t3)", margin: 0 }}>
          {urdu ? service.en : service.ur}
        </p>
      </div>

      <div className="st-detail">
        <div style={{ display: "grid", gap: 20 }}>
          {procedure && (
            <div className="st-card">
              <h3 style={{ marginBottom: 10 }}>{urdu ? "طریقۂ کار" : "How it works"}</h3>
              <p className={urdu ? "ur" : ""} style={{ fontSize: 14.5, lineHeight: 1.75 }}>
                {procedure}
              </p>
            </div>
          )}

          <div>
            <h3 style={{ fontSize: 16, fontWeight: 600, margin: "0 0 4px" }}>
              {urdu ? "درکار دستاویزات" : "What to bring"}
            </h3>
            <p style={{ fontSize: 13, color: "var(--t3)", margin: "0 0 14px" }}>
              {(service.checklist || []).length} items. Bring originals where marked — copies alone
              will be turned away at the counter.
            </p>

            <ul className="st-checklist">
              {(service.checklist || []).map((c, i) => (
                <li key={c.id} className="st-checkitem">
                  <span className="n">{i + 1}</span>
                  <span style={{ flex: 1, minWidth: 0 }}>
                    <span style={{ display: "block", fontSize: 14 }}>{c.en}</span>
                    <span className="ur" style={{ display: "block", fontSize: 13, color: "var(--t3)" }}>
                      {c.ur}
                    </span>
                  </span>
                  <Badge tone={c.copy ? "grey" : "brass"}>{c.copy ? "Attested copy" : "Original"}</Badge>
                </li>
              ))}
            </ul>
          </div>

          {stale && (
            <Note tone="amber" icon={ShieldCheck}>
              These details were last confirmed on {fmtDate(service.verified)}. Please ring the
              department before travelling, in case anything has changed since.
            </Note>
          )}
        </div>

        <aside style={{ display: "grid", gap: 12 }}>
          <div className="st-panel">
            <h4>At a glance</h4>
            {fee && (
              <div className="st-row">
                <Banknote size={14} color="var(--t3)" />
                <span style={{ flex: 1 }}>Fee</span>
                <span className="ua-num" style={{ fontWeight: 600 }}>{fmtPKR(fee.amount)}</span>
              </div>
            )}
            {deadline && (
              <div className="st-row">
                <Calendar size={14} color="var(--t3)" />
                <span style={{ flex: 1 }}>Deadline</span>
                <span className="ua-num">{fmtDate(deadline.date)}</span>
              </div>
            )}
            {deadline && daysSince(deadline.date) < 0 && (
              <div className="st-row">
                <span style={{ flex: 1, color: "var(--t3)" }}>Days left</span>
                <Badge tone={Math.abs(daysSince(deadline.date)) <= 21 ? "amber" : "jade"}>
                  <span className="ua-num">{Math.abs(daysSince(deadline.date))}</span>
                </Badge>
              </div>
            )}
            <div className="st-row">
              <span style={{ flex: 1, color: "var(--t3)" }}>Last checked</span>
              <Ladder verified={service.verified} />
            </div>
            <div className="st-row">
              <span style={{ flex: 1, color: "var(--t3)" }}>Source</span>
              <span style={{ fontSize: 12 }}>{service.src}</span>
            </div>
          </div>

          {department && (
            <div className="st-panel">
              <h4>Who handles this</h4>
              <div className="st-panel-b" style={{ paddingBottom: 10 }}>
                <div style={{ fontSize: 13.5, color: "var(--t1)", marginBottom: 3 }}>{department.en}</div>
                <div className="ua-num" style={{ fontSize: 12.5 }}>{department.hours}</div>
              </div>
              <a href={`tel:${department.phone}`} className="st-row" style={{ color: "var(--brass)" }}>
                <Phone size={14} />
                <span className="ua-num">{department.phone}</span>
              </a>
            </div>
          )}

          <Button
            variant="primary"
            className="block"
            icon={MessageSquare}
            onClick={() =>
              navigate("/chat", { state: { question: `${service.en} ke liye kya chahiye?` } })
            }
          >
            Ask about this
          </Button>
        </aside>
      </div>
    </div>
  );
}
