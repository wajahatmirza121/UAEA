import { TODAY } from "./constants";

/** Whole days between an ISO date and TODAY. Negative means future. */
export const daysSince = (iso) => Math.floor((TODAY - new Date(iso)) / 86400000);

/** 24 Aug 2026 — the format Pakistani university notices use. */
export const fmtDate = (iso) =>
  iso
    ? new Date(iso).toLocaleDateString("en-GB", {
        day: "numeric",
        month: "short",
        year: "numeric",
      })
    : "—";

/** Rupee amounts. Null renders as an em dash rather than "Rs 0". */
export const fmtPKR = (n) =>
  n === null || n === undefined || n === "" ? "—" : "Rs " + Number(n).toLocaleString("en-PK");

export const nfmt = (n) => Number(n).toLocaleString("en-US");

/** True when a string contains Arabic-script characters (so, Urdu here). */
export const isUrduText = (s) => /[\u0600-\u06FF]/.test(String(s || ""));

/** Timestamp for new audit entries, pinned to the mock TODAY. */
export const auditStamp = () => {
  const d = new Date();
  const hh = String(d.getHours()).padStart(2, "0");
  const mm = String(d.getMinutes()).padStart(2, "0");
  return `2026-09-01 ${hh}:${mm}`;
};
