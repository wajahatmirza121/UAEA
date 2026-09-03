/**
 * Dashboard analytics.
 *
 * Volume is generated rather than hand-written so the 7/30/90 day ranges all
 * look plausible. The ramp in the last fortnight is the Autumn 2026 admission
 * season, which is the story the dashboard copy refers to.
 */
export const VOLUME_90 = Array.from({ length: 90 }, (_, i) => {
  const base = 620 + i * 6.4;
  const wave = Math.sin(i / 4.1) * 68 + Math.sin(i / 11) * 110;
  const spike = i > 74 ? (i - 74) * 46 : 0;
  const wa = Math.round(base + wave + spike);
  const web = Math.round((base + wave * 0.6 + spike * 0.5) * 0.44);
  return { wa, web };
});

export const INTENTS = [
  { key: "result", label: "Result enquiry", ur: "نتیجہ", n: 8730 },
  { key: "fee_challan", label: "Fee & challan", ur: "فیس و چالان", n: 6140 },
  { key: "assignments", label: "Assignments", ur: "اسائنمنٹس", n: 5210 },
  { key: "admission", label: "Admission", ur: "داخلہ", n: 4820 },
  { key: "eligibility", label: "Eligibility", ur: "اہلیت", n: 3910 },
  { key: "roll_slip", label: "Roll number slip", ur: "رول نمبر سلپ", n: 3340 },
  { key: "degree", label: "Degree application", ur: "ڈگری", n: 2970 },
  { key: "date_sheet", label: "Date sheet", ur: "ڈیٹ شیٹ", n: 2560 },
];

/** Success metrics from §13. Deltas are period over period. */
export const METRICS = [
  { key: "containment", label: "Containment rate", ur: "خود حل شدہ", value: 78.4, unit: "%", delta: 4.2, note: "resolved without a human" },
  { key: "accuracy", label: "Factual accuracy", ur: "درستگی", value: 96.2, unit: "%", delta: 0.9, note: "spot-audited, 250 answers" },
  { key: "coverage", label: "Intent coverage", ur: "احاطہ", value: 91.7, unit: "%", delta: -1.4, note: "matched to a known intent" },
  { key: "escalations", label: "Escalations", ur: "ایسکلیشن", value: 342, unit: "", delta: 12.6, note: "handed to staff this period" },
];

/** Guardrail interventions (§4.3.5) — what never reached a student. */
export const GUARDRAIL_EVENTS = [
  { id: "g1", kind: "ungrounded_number", text: "Model produced a fee amount with no matching tool result", conv: "cnv-8824", at: "12 min ago", tone: "rose" },
  { id: "g2", kind: "injection", text: "Retrieved chunk contained instruction-like text; ignored", conv: "cnv-8819", at: "48 min ago", tone: "amber" },
  { id: "g3", kind: "outcome_promise", text: "Blocked a guaranteed-completion-date phrasing", conv: "cnv-8811", at: "1 h ago", tone: "amber" },
  { id: "g4", kind: "ungrounded_number", text: "Model produced a deadline with no matching tool result", conv: "cnv-8804", at: "2 h ago", tone: "rose" },
  { id: "g5", kind: "out_of_scope", text: "Declined an assignment-writing request", conv: "cnv-8798", at: "3 h ago", tone: "sky" },
];
