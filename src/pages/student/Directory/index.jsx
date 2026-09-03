import { useState, useMemo } from "react";
import { Search } from "lucide-react";
import DepartmentCard from "@/components/student/DepartmentCard";
import EmptyState from "@/components/ui/EmptyState";
import Button from "@/components/ui/Button";
import { useDebounced } from "@/hooks/useDebounced";
import { useApp } from "@/context/AppContext";

const GROUPS = [
  { id: "campus", label: "Regional campuses", test: (d) => d.en.startsWith("Regional Campus") },
  { id: "main", label: "Main campus departments", test: (d) => !d.en.startsWith("Regional Campus") },
];

/**
 * Contact locator — a deterministic database lookup, not model output.
 * Wrong phone numbers are their own kind of harm.
 */
export default function Directory() {
  const { store, urdu } = useApp();
  const [rawQuery, setRawQuery] = useState("");
  const query = useDebounced(rawQuery);

  const results = useMemo(
    () =>
      store.departments.filter((d) => {
        if (!query) return true;
        return `${d.en} ${d.ur} ${d.campus} ${d.phone}`.toLowerCase().includes(query.toLowerCase());
      }),
    [store.departments, query]
  );

  return (
    <div className="st-wrap st-section">
      <p className="st-eyebrow">Departments</p>
      <h1 className="st-h2" style={{ fontSize: 28 }}>
        {urdu ? "شعبے اور کیمپس" : "Who to call"}
      </h1>
      <p className="st-lede" style={{ marginBottom: 22 }}>
        Numbers and office hours for every campus and section, taken from the same records the
        assistant reads from.
      </p>

      <div className="st-ask" style={{ margin: "0 0 26px", maxWidth: 480 }}>
        <Search size={17} color="var(--t3)" style={{ flex: "0 0 17px" }} />
        <input
          value={rawQuery}
          onChange={(e) => setRawQuery(e.target.value)}
          placeholder={urdu ? "شہر یا شعبہ تلاش کریں" : "Search by city or department"}
          aria-label="Search departments"
        />
      </div>

      {results.length === 0 ? (
        <div className="st-card">
          <EmptyState
            title="No department matches that"
            body="Try a city name such as Lahore or Peshawar, or the name of the section."
            action={<Button onClick={() => setRawQuery("")}>Clear search</Button>}
          />
        </div>
      ) : (
        GROUPS.map((g) => {
          const items = results.filter(g.test);
          if (items.length === 0) return null;
          return (
            <div key={g.id} style={{ marginBottom: 32 }}>
              <h2 style={{ fontSize: 15, fontWeight: 600, margin: "0 0 14px" }}>{g.label}</h2>
              <div className="st-grid three">
                {items.map((d) => (
                  <DepartmentCard key={d.id} department={d} />
                ))}
              </div>
            </div>
          );
        })
      )}
    </div>
  );
}
