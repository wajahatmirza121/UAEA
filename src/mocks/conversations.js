/**
 * Sample transcripts.
 *
 * The `tool` messages are the point of this screen: they show the lookup that
 * grounded each answer. An answer containing a number with no tool call above
 * it is exactly what the guardrail layer exists to catch.
 */
export const CONVERSATIONS = [
  {
    id: "cnv-8841",
    channel: "whatsapp",
    lang: "Roman Urdu",
    started: "2026-09-01 11:24",
    turns: 6,
    outcome: "resolved",
    feedback: "up",
    intent: "fee_challan",
    messages: [
      { role: "user", text: "Assalam o alaikum, BS CS ki fees kitni hai autumn 2026 ke liye?" },
      { role: "tool", name: "get_fee_tariff", args: 'program="BS Computer Science", category="Semester (new)"', result: "amount=28500 PKR · effective 2026-07-01 · Fee Circular A-26 §3.1" },
      { role: "bot", text: "وعلیکم السلام! BS Computer Science ki semester fee Rs 28,500 hai (Autumn 2026). Ye Fee Circular A-26 §3.1 se li gayi hai, 24 August 2026 ko verify hui." },
      { role: "user", text: "challan kahan se banega?" },
      { role: "tool", name: "get_document_checklist", args: 'service="Fee Challan"', result: "2 items · portal-generated challan, CNIC copy" },
      { role: "bot", text: "Challan aap student portal se generate kar sakte hain. Bank mein jama karwate waqt CNIC ki copy sath rakhein. Autumn 2026 ki aakhri tareekh 20 September 2026 hai." },
    ],
  },
  {
    id: "cnv-8839",
    channel: "web",
    lang: "Urdu",
    started: "2026-09-01 10:52",
    turns: 4,
    outcome: "escalated",
    feedback: null,
    intent: "transcript",
    messages: [
      { role: "user", text: "ٹرانسکرپٹ ارجنٹ چاہیے، کتنے دن لگیں گے؟" },
      { role: "tool", name: "get_fee_tariff", args: 'program="Transcript", category="Urgent service"', result: "amount=3500 PKR · Degree Manual §4.2" },
      { role: "bot", text: "ارجنٹ ٹرانسکرپٹ کی فیس 3,500 روپے ہے۔ پروسیسنگ کا دورانیہ میرے ریکارڈ میں درج نہیں، اس لیے میں آپ کو شعبۂ ڈگری سے منسلک کر رہا ہوں۔" },
      { role: "system", text: "Escalated to Degree & Transcript Section · ticket ESC-2211" },
    ],
  },
  {
    id: "cnv-8836",
    channel: "whatsapp",
    lang: "Roman Urdu",
    started: "2026-09-01 09:41",
    turns: 5,
    outcome: "resolved",
    feedback: "up",
    intent: "admission",
    messages: [
      { role: "user", text: "admission ki last date kya hai" },
      { role: "tool", name: "get_deadline", args: 'service="Admission & Enrolment"', result: "2026-09-30 · Autumn 2026 · Admission Notice A-26/11" },
      { role: "bot", text: "Autumn 2026 ke liye admission ki aakhri tareekh 30 September 2026 hai. Late admission surcharge ke sath 15 October tak ho sakta hai." },
      { role: "user", text: "documents kya chahiye" },
      { role: "tool", name: "get_document_checklist", args: 'service="Admission & Enrolment"', result: "4 items · CNIC (copy), previous degree (copy), 2 photographs, paid challan receipt" },
      { role: "bot", text: "CNIC ki copy, pichli degree/certificate, 2 tasaweer, aur fee challan ki receipt. Ye list 24 August 2026 ko verify hui thi." },
    ],
  },
  {
    id: "cnv-8830",
    channel: "web",
    lang: "Roman Urdu",
    started: "2026-08-31 18:07",
    turns: 3,
    outcome: "unresolved",
    feedback: "down",
    intent: "assignments",
    messages: [
      { role: "user", text: "assignment late jama karwane pe kitna fine hai" },
      { role: "tool", name: "get_document_checklist", args: 'service="Assignment Submission"', result: "no penalty field in record" },
      { role: "bot", text: "Late submission ka fine mere record mein darj nahi hai. Main ye sawal review queue mein bhej raha hoon — aap Student Affairs se 051-9250177 par bhi puchh sakte hain." },
    ],
  },
  {
    id: "cnv-8827",
    channel: "whatsapp",
    lang: "Roman Urdu",
    started: "2026-08-31 16:33",
    turns: 4,
    outcome: "resolved",
    feedback: "up",
    intent: "department_lookup",
    messages: [
      { role: "user", text: "Rawalpindi campus ka number chahiye" },
      { role: "tool", name: "get_department", args: 'region="Rawalpindi"', result: "Regional Campus Rawalpindi · 051-4567890 · Satellite Town · 08:30–16:00" },
      { role: "bot", text: "Regional Campus Rawalpindi, Satellite Town — phone 051-4567890. Office hours 08:30 se 16:00 tak. Ye maloomat 11 August 2026 ko verify hui." },
    ],
  },
  {
    id: "cnv-8819",
    channel: "web",
    lang: "Urdu",
    started: "2026-08-31 14:02",
    turns: 3,
    outcome: "resolved",
    feedback: null,
    intent: "degree",
    messages: [
      { role: "user", text: "ڈگری کے لیے کون کون سے کاغذات چاہییں؟" },
      { role: "tool", name: "get_document_checklist", args: 'service="Degree Application"', result: "6 items · form, all result cards (copy), CNIC (copy), 2 photographs, paid challan, no-dues clearance" },
      { role: "bot", text: "ڈگری کی درخواست کے لیے چھ چیزیں درکار ہیں: درخواست فارم، تمام سمسٹر کے رزلٹ کارڈ کی کاپیاں، شناختی کارڈ کی کاپی، دو تصاویر، ادا شدہ چالان، اور کیمپس سے واجبات کی کلیئرنس۔ یہ فہرست 2 جولائی 2026 کو تصدیق شدہ ہے۔" },
    ],
  },
];
