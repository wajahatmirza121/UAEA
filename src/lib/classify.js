import { SERVICES } from "@/mocks/services";
import { CATEGORY_DEPARTMENT } from "@/mocks/routing";

/**
 * Intent router — a working stand-in for §4.3.2.
 *
 * The real system uses a small trained classifier. This is deterministic
 * keyword scoring, which is enough to demonstrate the behaviour that matters:
 * a query is classified BEFORE anything is answered, it carries a confidence
 * score, and below the threshold the assistant routes to a human instead of
 * guessing. Swapping this file for an API call is the only change needed.
 *
 * Roman Urdu is the hard part. Students do not spell consistently, so the
 * normaliser folds the common variants before scoring rather than trying to
 * list every spelling in every rule.
 */

/** Spelling folds for Roman Urdu, applied before scoring. */
const VARIANTS = [
  [/\b(fees|fis|phees|faees|feez)\b/g, "fee"],
  [/\b(admision|admisn|admishan|admissn|dakhla|dakhila|dakhle)\b/g, "admission"],
  [/\b(tareekh|tarikh|tarik|tareek)\b/g, "date"],
  [/\b(kitna|kitne|kitni)\b/g, "kitni"],
  [/\b(chalan|challaan|chalaan)\b/g, "challan"],
  [/\b(rizalt|rizult|natija|nateeja)\b/g, "result"],
  [/\b(transkript|transcrip|transcipt)\b/g, "transcript"],
  [/\b(degri|digree|digri)\b/g, "degree"],
  [/\b(asignment|assigment|asaainment)\b/g, "assignment"],
  [/\b(sertificate|certifcate|certificat)\b/g, "certificate"],
  [/\b(skolarship|wazifa|wazaif)\b/g, "scholarship"],
  [/\b(migreshan|migresion)\b/g, "migration"],
  [/\b(kaise|kesay|kese|kaisay)\b/g, "kaise"],
  [/\b(kahan|kahaan|kidhar)\b/g, "kahan"],
  [/\b(chahiye|chahye|chahiyay|chahie)\b/g, "chahiye"],
];

export function normalise(text) {
  let t = String(text || "").toLowerCase().trim();
  t = t.replace(/[?!.،؟,]/g, " ").replace(/\s+/g, " ");
  VARIANTS.forEach(([re, to]) => {
    t = t.replace(re, to);
  });
  return t;
}

/**
 * Which language to answer in.
 * Urdu script is unambiguous. Roman Urdu is detected from function words that
 * almost never appear in an English sentence.
 */
export function detectLanguage(text) {
  if (/[\u0600-\u06FF]/.test(text)) return "ur";
  const romanMarkers =
    /\b(kya|kitni|kaise|kahan|hai|hain|ka|ki|ke|mujhe|mera|meri|chahiye|nahi|kab|kar|karna|se|ko|par|bhi)\b/;
  if (romanMarkers.test(normalise(text))) return "roman";
  return "en";
}

/**
 * Rules. `strong` terms are worth 3 points, `weak` 1. Both scripts are listed
 * because a student may type either, or mix them in one sentence.
 */
const RULES = [
  // Ordered most-specific first. "fee challan" must beat the generic "fee".
  {
    intent: "fee_challan",
    label: "Fee challan",
    serviceId: "svc-03",
    deptId: "dep-10",
    strong: ["challan", "fee challan", "چالان"],
    weak: ["bank", "jama", "deposit", "payment", "pay", "kahan", "banega", "bana", "form", "بینک", "جمع", "ادائیگی"],
  },
  {
    intent: "fee_tariff",
    label: "Fee amount",
    serviceId: "svc-02",
    deptId: "dep-10",
    strong: ["fee", "tariff", "فیس"],
    weak: ["kitni", "semester", "amount", "rupay", "paisa", "cost", "charges", "رقم", "سمسٹر"],
  },
  {
    intent: "admission",
    label: "Admission",
    serviceId: "svc-01",
    strong: ["admission", "enrol", "enroll", "داخل", "اندراج"],
    weak: ["apply", "form", "last date", "date", "eligible", "eligibility", "درخواست", "اہلیت", "تاریخ", "آخری"],
  },
  {
    intent: "scholarships",
    label: "Scholarships",
    serviceId: "svc-04",
    strong: ["scholarship", "وظیف", "وظائف"],
    weak: ["financial aid", "need based", "merit", "امداد"],
  },
  {
    intent: "result",
    label: "Result",
    serviceId: "svc-05",
    strong: ["result", "نتیج", "نتائج", "gazette", "gazzette"],
    weak: ["marks", "grade", "gpa", "announce", "نمبر", "اعلان", "چیک"],
  },
  {
    intent: "date_sheet",
    label: "Date sheet",
    serviceId: "svc-06",
    strong: ["date sheet", "datesheet", "ڈیٹ شیٹ", "exam schedule"],
    weak: ["paper", "exam", "clash", "schedule", "امتحان", "پرچ"],
  },
  {
    intent: "roll_number_slip",
    label: "Roll number slip",
    serviceId: "svc-07",
    strong: ["roll number", "roll no", "roll slip", "رول نمبر"],
    weak: ["slip", "download", "centre", "center", "سلپ", "ڈاؤن لوڈ"],
  },
  {
    intent: "assignments",
    label: "Assignments",
    serviceId: "svc-08",
    strong: ["assignment", "اسائنمنٹ", "tutor", "ٹیوٹر"],
    weak: ["submit", "jama", "late", "fine", "post", "جمع", "جرمان"],
  },
  {
    intent: "degree",
    label: "Degree application",
    serviceId: "svc-09",
    strong: ["degree", "ڈگری"],
    weak: ["apply", "issue", "convocation", "graduate", "درخواست", "اجرا"],
  },
  {
    intent: "transcript",
    label: "Transcript",
    serviceId: "svc-10",
    strong: ["transcript", "prc", "ٹرانسکرپٹ"],
    weak: ["urgent", "normal", "copy", "record", "ارجنٹ", "نقل"],
  },
  {
    intent: "verification",
    label: "Verification",
    serviceId: "svc-11",
    strong: ["verification", "verify", "attest", "تصدیق", "hec"],
    weak: ["attestation", "genuine", "confirm"],
  },
  {
    intent: "rechecking",
    label: "Rechecking",
    serviceId: "svc-12",
    strong: ["recheck", "rechecking", "re-check", "دوبارہ جانچ", "revaluation"],
    weak: ["marks wrong", "totalling", "unmarked", "غلط نمبر"],
  },
  {
    intent: "correction",
    label: "Record correction",
    serviceId: "svc-13",
    strong: ["correction", "spelling", "تصحیح", "name change"],
    weak: ["wrong name", "date of birth", "dob", "affidavit", "نام", "درست"],
  },
  {
    intent: "noc",
    label: "NOC",
    serviceId: "svc-14",
    strong: ["noc", "no objection", "این او سی"],
    weak: ["clearance", "leaving", "کلیئرنس"],
  },
  {
    intent: "migration",
    label: "Migration",
    serviceId: "svc-15",
    strong: ["migration", "مائیگریشن", "transfer university"],
    weak: ["another university", "shift", "منتقل"],
  },
  {
    intent: "bonafide",
    label: "Bonafide / MOI",
    serviceId: "svc-16",
    strong: ["bonafide", "medium of instruction", "moi", "بونافائیڈ", "ذریعۂ تعلیم"],
    weak: ["visa", "letter", "proof"],
  },
  {
    intent: "department_lookup",
    label: "Contact a department",
    serviceId: null,
    deptId: "dep-01",
    strong: ["contact", "phone", "number", "campus", "office", "رابط", "کیمپس"],
    weak: [
      "islamabad", "rawalpindi", "lahore", "karachi", "peshawar", "multan",
      "timing", "hours", "address", "پت", "اوقات", "نمبر",
    ],
  },
];

const STRONG = 3;
const WEAK = 1;

/**
 * Classify a student message.
 *
 * Returns the intent, a confidence score, the service it maps to, and — the
 * part students actually care about — which department owns it.
 */
export function classify(text, departments = []) {
  const t = normalise(text);
  if (!t) return null;

  const scored = RULES.map((rule) => {
    let score = 0;
    const matched = [];

    rule.strong.forEach((k) => {
      if (t.includes(k)) {
        score += STRONG;
        matched.push(k);
      }
    });
    rule.weak.forEach((k) => {
      if (t.includes(k)) {
        score += WEAK;
        matched.push(k);
      }
    });

    const strongHits = rule.strong.filter((k) => t.includes(k)).length;
    return { ...rule, score, strongHits, matched };
  }).sort((a, b) => b.score - a.score || b.strongHits - a.strongHits);

  const top = scored[0];
  const runnerUp = scored[1];

  if (!top || top.score === 0) {
    return {
      intent: null,
      label: "Not recognised",
      confidence: 0,
      service: null,
      category: null,
      department: null,
      matched: [],
      alternatives: [],
    };
  }

  // Six points is two strong hits, or one strong plus three supporting terms.
  const confidence = Math.min(0.96, top.score / 6);

  const service = top.serviceId ? SERVICES.find((s) => s.id === top.serviceId) : null;
  const category = service?.cat || (top.intent === "department_lookup" ? "Admissions" : null);
  // A rule may override the category default: a fee question belongs with
  // Finance even though the service sits under Admissions.
  const deptId = top.deptId || (category ? CATEGORY_DEPARTMENT[category] : null);
  const department = departments.find((d) => d.id === deptId) || null;

  return {
    intent: top.intent,
    label: top.label,
    confidence,
    service,
    category,
    department,
    matched: [...new Set(top.matched)],
    // Offered to the student when the top two are close and we might be wrong.
    alternatives:
      runnerUp && runnerUp.score > 0 && top.score - runnerUp.score <= 2
        ? [{ intent: runnerUp.intent, label: runnerUp.label }]
        : [],
  };
}

/** Below this, the assistant offers a human instead of answering. */
export const CONFIDENCE_FLOOR = 0.5;
