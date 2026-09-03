/**
 * Seed audit trail.
 *
 * §9 makes a full record of who changed which fee, deadline or procedure a
 * compliance requirement rather than a nice-to-have. Entries are append-only:
 * the console has no path to edit or delete one.
 */
export const AUDIT_SEED = [
  { id: "a-12", at: "2026-08-30 14:12", actor: "Sana Yousuf", role: "Content editor", action: "verify", table: "services", recordId: "svc-08", record: "Assignment Submission", changes: [] },
  { id: "a-11", at: "2026-08-30 11:48", actor: "Sana Yousuf", role: "Content editor", action: "update", table: "deadlines", recordId: "dl-04", record: "Assignment 1 · Autumn 2026", changes: [{ field: "Date", from: "5 Oct 2026", to: "12 Oct 2026" }, { field: "Source", from: "Academic Calendar 26-27 draft", to: "Academic Calendar 26-27" }] },
  { id: "a-10", at: "2026-08-28 16:02", actor: "Bilal Ahmed", role: "Content editor", action: "verify", table: "services", recordId: "svc-05", record: "Result Enquiry", changes: [] },
  { id: "a-09", at: "2026-08-28 15:55", actor: "Bilal Ahmed", role: "Content editor", action: "update", table: "deadlines", recordId: "dl-08", record: "Date Sheet publication · Autumn 2026", changes: [{ field: "Date", from: "8 Nov 2026", to: "15 Nov 2026" }] },
  { id: "a-08", at: "2026-08-24 10:31", actor: "Imran Shafiq", role: "Content editor", action: "update", table: "fees", recordId: "fee-01", record: "BS Computer Science · Semester (new)", changes: [{ field: "Amount", from: "Rs 26,400", to: "Rs 28,500" }, { field: "Effective from", from: "1 Jan 2026", to: "1 Jul 2026" }] },
  { id: "a-07", at: "2026-08-24 10:24", actor: "Imran Shafiq", role: "Content editor", action: "update", table: "fees", recordId: "fee-02", record: "BS Computer Science · Per credit hour (repeat)", changes: [{ field: "Amount", from: "Rs 1,980", to: "Rs 2,150" }] },
  { id: "a-06", at: "2026-08-24 09:40", actor: "Farah Nadeem", role: "Content editor", action: "verify", table: "services", recordId: "svc-01", record: "Admission & Enrolment", changes: [] },
  { id: "a-05", at: "2026-08-19 13:17", actor: "Ayesha Tariq", role: "Super admin", action: "guardrail", table: "settings", recordId: "cfg", record: "Handover threshold", changes: [{ field: "Threshold", from: "58%", to: "65%" }] },
  { id: "a-04", at: "2026-08-19 12:02", actor: "Imran Shafiq", role: "Content editor", action: "create", table: "deadlines", recordId: "dl-03", record: "Fee Challan · Autumn 2026", changes: [{ field: "Date", from: "—", to: "20 Sep 2026" }] },
  { id: "a-03", at: "2026-08-18 17:31", actor: "Farah Nadeem", role: "Content editor", action: "publish", table: "documents", recordId: "doc-01", record: "Prospectus 2026–27 (v3)", changes: [{ field: "Status", from: "v2 indexed", to: "v3 indexed, v2 superseded" }] },
  { id: "a-02", at: "2026-08-12 09:08", actor: "Bilal Ahmed", role: "Content editor", action: "verify", table: "services", recordId: "svc-07", record: "Roll Number Slip", changes: [] },
  { id: "a-01", at: "2026-08-11 14:45", actor: "Farah Nadeem", role: "Content editor", action: "update", table: "departments", recordId: "dep-04", record: "Regional Campus Rawalpindi", changes: [{ field: "Phone", from: "051-4567123", to: "051-4567890" }] },
];
