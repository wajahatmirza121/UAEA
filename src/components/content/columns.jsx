import { Phone } from "lucide-react";
import Badge from "@/components/ui/Badge";
import Ladder from "@/components/ui/Ladder";
import { fmtDate, fmtPKR, nfmt, daysSince } from "@/lib/format";

/**
 * Column definitions for each content table.
 *
 * Kept out of the page so the table itself stays a rendering concern and
 * adding a tab is a data change rather than a new screen. Every table ends
 * with the verification ladder, deliberately: it is the column the person is
 * actually here to act on.
 */

const verifiedCol = (withWho) => ({
  key: "verified",
  label: "Last verified",
  sortable: true,
  render: (r) =>
    withWho ? (
      <div style={{ display: "flex", flexDirection: "column", gap: 3 }}>
        <Ladder verified={r.verified} />
        <span style={{ fontSize: 11, color: "var(--t3)" }}>{r.by}</span>
      </div>
    ) : (
      <Ladder verified={r.verified} />
    ),
});

const sourceCol = {
  key: "src",
  label: "Source",
  render: (r) => <span style={{ fontSize: 12, color: "var(--t2)" }}>{r.src}</span>,
};

const bilingualName = (label) => ({
  key: "en",
  label,
  sortable: true,
  render: (r) => (
    <div>
      <div style={{ fontWeight: 500 }}>{r.en}</div>
      <div className="ur" style={{ fontSize: 12, color: "var(--t3)" }}>
        {r.ur}
      </div>
    </div>
  ),
});

export const COLUMNS = {
  services: [
    bilingualName("Service"),
    { key: "cat", label: "Category", sortable: true, render: (r) => <Badge>{r.cat}</Badge> },
    {
      key: "queries",
      label: "Queries / 90d",
      sortable: true,
      render: (r) => <span className="ua-num">{nfmt(r.queries)}</span>,
    },
    {
      key: "checklist",
      label: "Checklist",
      render: (r) => (
        <span className="ua-num" style={{ color: "var(--t2)" }}>
          {(r.checklist || []).length} items
        </span>
      ),
    },
    sourceCol,
    verifiedCol(true),
  ],

  fees: [
    {
      key: "program",
      label: "Programme",
      sortable: true,
      render: (r) => <span style={{ fontWeight: 500 }}>{r.program}</span>,
    },
    { key: "cat", label: "Basis", sortable: true, render: (r) => <Badge>{r.cat}</Badge> },
    {
      key: "amount",
      label: "Amount",
      sortable: true,
      render: (r) => (
        <span className="ua-num" style={{ fontWeight: 600 }}>
          {fmtPKR(r.amount)}
        </span>
      ),
    },
    {
      key: "from",
      label: "Effective from",
      sortable: true,
      render: (r) => (
        <span className="ua-num" style={{ color: "var(--t2)" }}>
          {fmtDate(r.from)}
        </span>
      ),
    },
    sourceCol,
    verifiedCol(false),
  ],

  deadlines: [
    {
      key: "service",
      label: "Deadline",
      sortable: true,
      render: (r) => <span style={{ fontWeight: 500 }}>{r.service}</span>,
    },
    { key: "semester", label: "Semester", sortable: true, render: (r) => <Badge>{r.semester}</Badge> },
    {
      key: "date",
      label: "Date",
      sortable: true,
      render: (r) => {
        // Negative days means the date is still ahead of us.
        const d = daysSince(r.date);
        return (
          <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span className="ua-num">{fmtDate(r.date)}</span>
            {d > 0 ? (
              <Badge tone="grey">passed</Badge>
            ) : d > -14 ? (
              <Badge tone="amber">in {Math.abs(d)}d</Badge>
            ) : (
              <Badge tone="jade">in {Math.abs(d)}d</Badge>
            )}
          </span>
        );
      },
    },
    sourceCol,
    verifiedCol(false),
  ],

  departments: [
    bilingualName("Department"),
    {
      key: "campus",
      label: "Campus",
      sortable: true,
      render: (r) => <span style={{ color: "var(--t2)" }}>{r.campus}</span>,
    },
    {
      key: "phone",
      label: "Phone",
      render: (r) => (
        <span className="ua-num" style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <Phone size={12} color="var(--t3)" />
          {r.phone}
        </span>
      ),
    },
    {
      key: "hours",
      label: "Office hours",
      render: (r) => (
        <span className="ua-num" style={{ color: "var(--t2)" }}>
          {r.hours}
        </span>
      ),
    },
    verifiedCol(false),
  ],
};

/** Human name for a record from any of the four tables. */
export const nameOf = (r) => r?.en || r?.program || r?.service || "";
