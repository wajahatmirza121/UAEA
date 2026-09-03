import { daysSince } from "./format";

/**
 * The governance rule this console exists to enforce.
 *
 * A record is only as trustworthy as the last time a human checked it against
 * the source document. Four rungs, draining as the record ages:
 *
 *   0–30 days    four rungs, jade    checked this month
 *   31–90 days   three rungs, jade   still within the semester
 *   91–180 days  two rungs, amber    ageing, worth a look
 *   181+ days    one rung, rose      stale, do not trust the number
 *
 * Thresholds are tied to the academic cycle, not arbitrary. A fee circular is
 * reissued each semester, so anything past six months predates the current one.
 */
export function freshness(iso) {
  const d = daysSince(iso);
  if (d <= 30) return { rungs: 4, tone: "jade", label: "Verified", days: d };
  if (d <= 90) return { rungs: 3, tone: "jade", label: "Verified", days: d };
  if (d <= 180) return { rungs: 2, tone: "amber", label: "Ageing", days: d };
  return { rungs: 1, tone: "rose", label: "Stale", days: d };
}

/** Counts records per freshness tone, for the dashboard ring. */
export function freshnessBuckets(records) {
  const b = { jade: 0, amber: 0, rose: 0 };
  records.forEach((r) => {
    b[freshness(r.verified).tone] += 1;
  });
  return [
    { tone: "jade", label: "Verified this cycle", n: b.jade },
    { tone: "amber", label: "Ageing, 3–6 months", n: b.amber },
    { tone: "rose", label: "Stale, past 6 months", n: b.rose },
  ];
}
