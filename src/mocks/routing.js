/**
 * Query routing configuration.
 *
 * Which department owns which kind of question. This is deliberately a lookup
 * table rather than something the model decides: a student who is told to ring
 * the wrong office has been failed just as badly as one told the wrong fee.
 *
 * Categories mirror the `cat` field on services, so adding a service to a
 * category routes it automatically.
 */
export const CATEGORY_DEPARTMENT = {
  Admissions: "dep-01",
  Finance: "dep-10",
  Examinations: "dep-02",
  Academics: "dep-09",
  Certification: "dep-03",
  Records: "dep-11",
};

/** Human-facing description of each category, shown on the landing page. */
export const CATEGORIES = [
  {
    id: "Admissions",
    en: "Admissions",
    ur: "داخلہ",
    blurb: "Applying, eligibility, enrolment and what the programme costs.",
    blurb_ur: "درخواست، اہلیت، اندراج اور پروگرام کی فیس۔",
  },
  {
    id: "Finance",
    en: "Fees & Finance",
    ur: "فیس و مالیات",
    blurb: "Challan forms, payment, dues and scholarship support.",
    blurb_ur: "چالان فارم، ادائیگی، واجبات اور وظائف۔",
  },
  {
    id: "Examinations",
    en: "Examinations",
    ur: "امتحانات",
    blurb: "Results, date sheets, roll number slips and rechecking.",
    blurb_ur: "نتائج، ڈیٹ شیٹ، رول نمبر سلپ اور دوبارہ جانچ۔",
  },
  {
    id: "Academics",
    en: "Academics",
    ur: "تعلیمی امور",
    blurb: "Assignments, tutors and study support.",
    blurb_ur: "اسائنمنٹس، ٹیوٹر اور تعلیمی معاونت۔",
  },
  {
    id: "Certification",
    en: "Degree & Transcript",
    ur: "ڈگری و ٹرانسکرپٹ",
    blurb: "Applying for your degree, transcripts and verification.",
    blurb_ur: "ڈگری کی درخواست، ٹرانسکرپٹ اور تصدیق۔",
  },
  {
    id: "Records",
    en: "Records",
    ur: "ریکارڈ",
    blurb: "NOC, migration, corrections and bonafide letters.",
    blurb_ur: "این او سی، مائیگریشن، تصحیح اور بونافائیڈ خط۔",
  },
];

/** Starter questions, in the way students actually type them. */
export const QUICK_ASKS = [
  { text: "Admission ki last date kya hai?", intent: "admission" },
  { text: "BS Computer Science ki fees kitni hai?", intent: "fee_tariff" },
  { text: "Fee challan kahan se banega?", intent: "fee_challan" },
  { text: "ڈگری کے لیے کون سے کاغذات چاہییں؟", intent: "degree" },
  { text: "Result kab announce hoga?", intent: "result" },
  { text: "Transcript apply karne ka tareeqa?", intent: "transcript" },
  { text: "Rawalpindi campus ka number chahiye", intent: "department_lookup" },
  { text: "NOC ke liye kya documents chahiye?", intent: "noc" },
];
