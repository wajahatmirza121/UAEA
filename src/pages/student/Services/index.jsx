import { useState, useMemo } from "react";
import { useSearchParams } from "react-router-dom";
import { Search } from "lucide-react";
import ServiceCard from "@/components/student/ServiceCard";
import EmptyState from "@/components/ui/EmptyState";
import Button from "@/components/ui/Button";
import { CATEGORIES, CATEGORY_DEPARTMENT } from "@/mocks/routing";
import { useDebounced } from "@/hooks/useDebounced";
import { useApp } from "@/context/AppContext";

/**
 * Service directory, filtered by the department that owns each area.
 *
 * The category lives in the URL so a student can send "the fees page" to a
 * friend and have it open on the same filter.
 */
export default function Services() {
  const { store, urdu } = useApp();
  const [params, setParams] = useSearchParams();
  const category = params.get("category") || "all";

  const [rawQuery, setRawQuery] = useState("");
  const query = useDebounced(rawQuery);

  const setCategory = (id) => {
    if (id === "all") setParams({});
    else setParams({ category: id });
  };

  const results = useMemo(
    () =>
      store.services.filter((s) => {
        if (category !== "all" && s.cat !== category) return false;
        if (!query) return true;
        const hay = `${s.en} ${s.ur} ${s.cat} ${(s.checklist || []).map((c) => c.en).join(" ")}`;
        return hay.toLowerCase().includes(query.toLowerCase());
      }),
    [store.services, category, query]
  );

  const feeFor = (s) => store.fees.find((f) => f.program === s.en || f.program === s.en.split(" ")[0]);
  const deadlineFor = (s) => store.deadlines.find((d) => d.service === s.en);
  const activeDept = category !== "all" ? store.departments.find((d) => d.id === CATEGORY_DEPARTMENT[category]) : null;

  return (
    <div className="st-wrap st-section">
      <p className="st-eyebrow">Services</p>
      <h1 className="st-h2" style={{ fontSize: 28 }}>
        {urdu ? "تمام خدمات" : "What do you need to do?"}
      </h1>
      <p className="st-lede" style={{ marginBottom: 22 }}>
        Every service shows what it costs, what documents you must bring, and which office handles
        it — with the date staff last confirmed those details.
      </p>

      <div className="st-ask" style={{ margin: "0 0 18px", maxWidth: 480 }}>
        <Search size={17} color="var(--t3)" style={{ flex: "0 0 17px" }} />
        <input
          value={rawQuery}
          onChange={(e) => setRawQuery(e.target.value)}
          placeholder={urdu ? "خدمت تلاش کریں" : "Search services"}
          aria-label="Search services"
        />
      </div>

      <div className="st-chips" style={{ justifyContent: "flex-start", marginBottom: 26 }}>
        <button
          className="st-chip"
          onClick={() => setCategory("all")}
          style={
            category === "all"
              ? { borderColor: "var(--brass-line)", background: "var(--brass-soft)", color: "var(--brass)" }
              : undefined
          }
        >
          All ({store.services.length})
        </button>
        {CATEGORIES.map((c) => {
          const n = store.services.filter((s) => s.cat === c.id).length;
          const on = category === c.id;
          return (
            <button
              key={c.id}
              className="st-chip"
              onClick={() => setCategory(c.id)}
              style={
                on
                  ? { borderColor: "var(--brass-line)", background: "var(--brass-soft)", color: "var(--brass)" }
                  : undefined
              }
            >
              {urdu ? c.ur : c.en} ({n})
            </button>
          );
        })}
      </div>

      {activeDept && (
        <div className="ua-note brass" style={{ marginBottom: 20 }}>
          <span>
            Everything below is handled by <b style={{ color: "var(--t1)" }}>{activeDept.en}</b> —{" "}
            <span className="ua-num">{activeDept.phone}</span>, {activeDept.hours}.
          </span>
        </div>
      )}

      {results.length === 0 ? (
        <div className="st-card">
          <EmptyState
            title="Nothing matches that"
            body="Try a different word, or ask in your own words instead — the assistant understands Roman Urdu."
            action={<Button onClick={() => setRawQuery("")}>Clear search</Button>}
          />
        </div>
      ) : (
        <div className="st-grid two">
          {results.map((s) => (
            <ServiceCard key={s.id} service={s} fee={feeFor(s)} deadline={deadlineFor(s)} />
          ))}
        </div>
      )}
    </div>
  );
}
