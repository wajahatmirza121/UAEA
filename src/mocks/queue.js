/**
 * Unanswered and low-confidence queries — the content growth loop (§4.6).
 * Real phrasing matters here: this is how students actually type, mixed
 * Roman Urdu and Urdu script, unpunctuated, often mid-thought.
 */
export const QUEUE = [
  { id: "q-01", text: "BS CS ki fees per semester kitni hai agar main repeat course le raha hoon", script: "roman", channel: "whatsapp", intent: "fee_tariff", conf: 0.41, count: 34, last: "2026-09-01", reason: "Low classifier confidence", answer: "I could not confirm a repeat-course rate for this programme." },
  { id: "q-02", text: "داخلے کی آخری تاریخ میں توسیع ہوئی ہے یا نہیں؟", script: "urdu", channel: "web", intent: null, conf: 0.22, count: 61, last: "2026-09-01", reason: "No matching intent", answer: "I do not have information about a deadline extension." },
  { id: "q-03", text: "transcript urgent chahiye kitne din lagenge Rawalpindi campus se", script: "roman", channel: "whatsapp", intent: "transcript", conf: 0.68, count: 22, last: "2026-08-31", reason: "Tool returned no data", answer: "Processing time for the Rawalpindi campus is not recorded." },
  { id: "q-04", text: "assignment late jama karwane pe kitna fine hai", script: "roman", channel: "whatsapp", intent: "assignments", conf: 0.55, count: 47, last: "2026-08-31", reason: "Tool returned no data", answer: "No late-submission penalty is listed for this service." },
  { id: "q-05", text: "کیا میں ایک ہی سمسٹر میں دو پروگرام میں داخلہ لے سکتا ہوں؟", script: "urdu", channel: "web", intent: "admission", conf: 0.49, count: 18, last: "2026-08-30", reason: "Policy question, no source", answer: "Dual-enrolment policy is not covered in my sources." },
  { id: "q-06", text: "roll number slip download nahi ho rahi error aa raha hai", script: "roman", channel: "whatsapp", intent: "roll_number_slip", conf: 0.71, count: 39, last: "2026-08-30", reason: "Needs system integration", answer: "I cannot check the portal status yet." },
  { id: "q-07", text: "degree verification HEC ke liye kaise karwaen", script: "roman", channel: "web", intent: "verification", conf: 0.52, count: 28, last: "2026-08-29", reason: "Out-of-scope external body", answer: "HEC attestation is handled outside the University." },
  { id: "q-08", text: "scholarship ka result kab announce hoga Autumn 2026", script: "roman", channel: "whatsapp", intent: "scholarships", conf: 0.63, count: 25, last: "2026-08-29", reason: "Stale source document", answer: "The scholarship policy on file is from May 2026." },
  { id: "q-09", text: "challan bank se jama ho gaya lekin status update nahi hua", script: "roman", channel: "whatsapp", intent: "fee_challan", conf: 0.74, count: 52, last: "2026-08-28", reason: "Needs system integration", answer: "I cannot look up individual payment status yet." },
  { id: "q-10", text: "میٹرک کا رزلٹ کہاں سے چیک کروں؟", script: "urdu", channel: "web", intent: "result", conf: 0.81, count: 16, last: "2026-08-28", reason: "Thumbs-down on answer", answer: "Results are published on the University results portal." },
  { id: "q-11", text: "NOC ke liye original documents jama karwane parenge kya", script: "roman", channel: "whatsapp", intent: "noc", conf: 0.58, count: 21, last: "2026-08-27", reason: "Checklist ambiguity", answer: "The checklist does not specify original versus attested copies." },
  { id: "q-12", text: "migration certificate ka fee refund ho sakti hai", script: "roman", channel: "web", intent: "migration", conf: 0.44, count: 12, last: "2026-08-27", reason: "No matching intent", answer: "Refund policy for migration fees is not documented." },
  { id: "q-13", text: "date sheet clash ho gayi hai do papers ek din", script: "roman", channel: "whatsapp", intent: "date_sheet", conf: 0.47, count: 19, last: "2026-08-26", reason: "Escalation-only path", answer: "Paper clashes must be reported to the Examinations Department." },
  { id: "q-14", text: "kya B.Ed ke liye 2 saal ka teaching experience zaroori hai", script: "roman", channel: "web", intent: "eligibility", conf: 0.53, count: 27, last: "2026-08-26", reason: "Eligibility rule not in DB", answer: "Experience requirements for B.Ed are not recorded." },
];
