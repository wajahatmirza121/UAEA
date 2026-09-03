import { useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { Clock } from "lucide-react";
import FreshnessRing from "@/components/charts/FreshnessRing";
import Ladder from "@/components/ui/Ladder";
import Button from "@/components/ui/Button";
import { freshness, freshnessBuckets } from "@/lib/freshness";
import { fmtDate } from "@/lib/format";
import { nameOf } from "@/components/content/columns";
import { useApp } from "@/context/AppContext";

/**
 * How much of the catalogue a human has vouched for recently, plus the five
 * records most overdue for a check. Clicking one goes to the catalogue.
 */
export default function FreshnessPanel() {
  const { store } = useApp();
  const navigate = useNavigate();

  const all = useMemo(
    () => [...store.services, ...store.fees, ...store.deadlines, ...store.departments],
    [store]
  );

  const buckets = useMemo(() => freshnessBuckets(all), [all]);

  const stale = useMemo(
    () =>
      all
        .filter((r) => freshness(r.verified).tone !== "jade")
        .sort((a, b) => new Date(a.verified) - new Date(b.verified))
        .slice(0, 5),
    [all]
  );

  return (
    <div className="ua-card">
      <div className="ua-card-h">
        <div>
          <h3>Catalogue freshness</h3>
          <p>Every fact a student sees carries its verification date</p>
        </div>
        <Button size="sm" variant="ghost" onClick={() => navigate("/admin/content")}>
          Open catalogue
        </Button>
      </div>

      <FreshnessRing buckets={buckets} />
      <div className="ua-hairline" />

      <div className="ua-list">
        {stale.length === 0 ? (
          <div style={{ padding: "22px 16px", fontSize: 12.5, color: "var(--t3)", textAlign: "center" }}>
            Nothing is overdue. Every record has been checked within the last three months.
          </div>
        ) : (
          stale.map((r) => (
            <button key={r.id} className="ua-listitem" onClick={() => navigate("/admin/content")}>
              <Clock size={14} color="var(--amber)" style={{ marginTop: 2, flex: "0 0 14px" }} />
              <span style={{ flex: 1, minWidth: 0 }}>
                <span style={{ fontSize: 13, display: "block" }}>{nameOf(r)}</span>
                <span style={{ fontSize: 11.5, color: "var(--t3)" }}>
                  Last checked by {r.by} · {fmtDate(r.verified)}
                </span>
              </span>
              <Ladder verified={r.verified} />
            </button>
          ))
        )}
      </div>
    </div>
  );
}
