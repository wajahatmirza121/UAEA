/**
 * Source documents ingested into the RAG store (§5.3).
 * Deliberately includes a processing, a superseded and a failed record so
 * every ingestion state renders without editing anything.
 */
export const DOCUMENTS = [
  { id: "doc-01", title: "Prospectus 2026–27", lang: "English", version: "v3", pages: 412, chunks: 1842, status: "indexed", uploaded: "2026-08-18", by: "Farah Nadeem" },
  { id: "doc-02", title: "Fee Tariff Circular — Autumn 2026", lang: "English", version: "v2", pages: 24, chunks: 96, status: "indexed", uploaded: "2026-08-19", by: "Imran Shafiq" },
  { id: "doc-03", title: "Admission Procedure Manual", lang: "English", version: "v1", pages: 58, chunks: 214, status: "indexed", uploaded: "2026-08-24", by: "Farah Nadeem" },
  { id: "doc-04", title: "طلبہ ہینڈ بک", lang: "Urdu", version: "v2", pages: 136, chunks: 508, status: "indexed", uploaded: "2026-08-30", by: "Sana Yousuf" },
  { id: "doc-05", title: "Scholarship Policy 2026", lang: "English", version: "v1", pages: 31, chunks: 0, status: "processing", uploaded: "2026-09-01", by: "Imran Shafiq", progress: 63 },
  { id: "doc-06", title: "Examination Rules & Regulations 2025", lang: "English", version: "v4", pages: 77, chunks: 289, status: "superseded", uploaded: "2025-09-14", by: "Bilal Ahmed" },
  { id: "doc-07", title: "Migration & NOC Guidelines", lang: "English", version: "v1", pages: 19, chunks: 0, status: "failed", uploaded: "2026-08-29", by: "Sana Yousuf", error: "Scanned pages below OCR confidence threshold" },
];

/** Canned result for the retrieval tester. Phase 2 calls the real endpoint. */
export const RETRIEVAL_SAMPLE = [
  { score: 0.91, doc: "Fee Tariff Circular — Autumn 2026", section: "§3.1 Undergraduate programmes", text: "Semester dues for BS Computer Science, first enrolment, are payable in full before the challan deadline." },
  { score: 0.84, doc: "Prospectus 2026–27", section: "§4.2 Fee structure", text: "Programme dues are revised each academic year and published in the accompanying fee circular." },
  { score: 0.71, doc: "طلبہ ہینڈ بک", section: "§3 فیس اور چالان", text: "فیس چالان پورٹل سے حاصل کیا جا سکتا ہے اور مقررہ تاریخ تک بینک میں جمع کروانا لازم ہے۔" },
  { score: 0.58, doc: "Admission Procedure Manual", section: "§6 Payment", text: "Applications remain provisional until the fee receipt is attached to the enrolment record." },
];
