/**
 * Fee tariff — the deterministic table get_fee_tariff() reads from (§6).
 * The assistant never paraphrases these numbers; it looks them up.
 */
export const FEES = [
  { id: "fee-01", program: "BS Computer Science", cat: "Semester (new)", amount: 28500, from: "2026-07-01", src: "Fee Circular A-26 §3.1", verified: "2026-08-24", by: "Imran Shafiq" },
  { id: "fee-02", program: "BS Computer Science", cat: "Per credit hour (repeat)", amount: 2150, from: "2026-07-01", src: "Fee Circular A-26 §3.2", verified: "2026-08-24", by: "Imran Shafiq" },
  { id: "fee-03", program: "B.Ed (1.5 Year)", cat: "Semester (new)", amount: 18600, from: "2026-07-01", src: "Fee Circular A-26 §3.4", verified: "2026-08-24", by: "Imran Shafiq" },
  { id: "fee-04", program: "Matric (SSC)", cat: "Annual", amount: 6900, from: "2026-07-01", src: "Fee Circular A-26 §2.1", verified: "2026-08-19", by: "Imran Shafiq" },
  { id: "fee-05", program: "Intermediate (HSSC)", cat: "Annual", amount: 8400, from: "2026-07-01", src: "Fee Circular A-26 §2.2", verified: "2026-08-19", by: "Imran Shafiq" },
  { id: "fee-06", program: "MA Urdu", cat: "Semester (new)", amount: 16200, from: "2026-07-01", src: "Fee Circular A-26 §3.6", verified: "2026-06-30", by: "Imran Shafiq" },
  { id: "fee-07", program: "MSc Mathematics", cat: "Semester (new)", amount: 19800, from: "2026-07-01", src: "Fee Circular A-26 §3.7", verified: "2026-06-30", by: "Imran Shafiq" },
  { id: "fee-08", program: "MPhil Education", cat: "Semester (new)", amount: 44000, from: "2026-07-01", src: "Fee Circular A-26 §3.9", verified: "2026-02-14", by: "Imran Shafiq" },
  { id: "fee-09", program: "Transcript", cat: "Urgent service", amount: 3500, from: "2026-01-01", src: "Degree Manual §4.2", verified: "2026-07-02", by: "Ayesha Tariq" },
  { id: "fee-10", program: "Degree", cat: "Normal service", amount: 2000, from: "2026-01-01", src: "Degree Manual §3.5", verified: "2026-07-02", by: "Ayesha Tariq" },
  { id: "fee-11", program: "Rechecking", cat: "Per paper", amount: 1500, from: "2026-01-01", src: "Exam Regs 2026 §9.2", verified: "2026-08-05", by: "Bilal Ahmed" },
  { id: "fee-12", program: "Migration Certificate", cat: "Normal service", amount: 2500, from: "2025-09-01", src: "Migration Guidelines §5.1", verified: "2026-06-14", by: "Sana Yousuf" },
  { id: "fee-13", program: "NOC", cat: "Normal service", amount: 1200, from: "2025-09-01", src: "Migration Guidelines §2.3", verified: "2026-06-14", by: "Sana Yousuf" },
  { id: "fee-14", program: "Record Correction", cat: "Normal service", amount: 1000, from: "2025-09-01", src: "Records SOP v4 §5", verified: "2026-02-27", by: "Sana Yousuf" },
];
