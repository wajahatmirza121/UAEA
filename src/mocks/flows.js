/**
 * Guided flows (§4.3.3).
 *
 * The architecture doc is explicit that multi-turn journeys must be modelled
 * as an explicit state machine per flow rather than letting the LLM improvise
 * the sequence. That is what stops the assistant skipping a required document
 * or asking for the campus after it has already answered.
 *
 * Step types
 *   ask      collect a value into a named slot before continuing
 *   lookup   call a grounding tool; the answer must come from its result
 *   inform   state something already known, no tool needed
 *   confirm  read the checklist or summary back to the student
 *   handoff  hand to a human; always terminal
 *
 * A flow is only publishable when every path ends in `confirm` or `handoff`.
 * The editor checks that and refuses to promote a draft otherwise.
 */
export const FLOWS = [
  {
    id: "flow-admission",
    en: "Admission & Enrolment",
    ur: "داخلہ و اندراج",
    intent: "admission",
    serviceId: "svc-01",
    status: "live",
    updated: "2026-08-24",
    by: "Farah Nadeem",
    completions: 3120,
    dropOff: 0.14,
    steps: [
      { id: "s1", type: "ask", label: "Which programme", slot: "programme", prompt_en: "Which programme are you applying for?", prompt_ur: "آپ کس پروگرام میں داخلہ لینا چاہتے ہیں؟", validation: "must match a programme in the fee tariff" },
      { id: "s2", type: "ask", label: "Which campus", slot: "campus", prompt_en: "Which regional campus is closest to you?", prompt_ur: "آپ کے قریب کون سا علاقائی کیمپس ہے؟", validation: "must match a campus record" },
      { id: "s3", type: "lookup", label: "Check eligibility", tool: "get_eligibility", toolArgs: "programme", prompt_en: "", prompt_ur: "" },
      { id: "s4", type: "lookup", label: "Fetch the deadline", tool: "get_deadline", toolArgs: 'service="Admission & Enrolment"', prompt_en: "", prompt_ur: "" },
      { id: "s5", type: "lookup", label: "Fetch the fee", tool: "get_fee_tariff", toolArgs: "programme, category", prompt_en: "", prompt_ur: "" },
      { id: "s6", type: "confirm", label: "Read back the checklist", tool: "get_document_checklist", toolArgs: 'service="Admission & Enrolment"', prompt_en: "Here is what you need and by when.", prompt_ur: "آپ کو یہ چیزیں درکار ہیں اور یہ آخری تاریخ ہے۔" },
      { id: "s7", type: "handoff", label: "Offer a human", prompt_en: "Would you like me to connect you to the admissions office?", prompt_ur: "کیا میں آپ کو شعبۂ داخلہ سے ملاؤں؟", terminal: true },
    ],
  },
  {
    id: "flow-challan",
    en: "Fee Challan",
    ur: "فیس چالان",
    intent: "fee_challan",
    serviceId: "svc-03",
    status: "live",
    updated: "2026-08-19",
    by: "Imran Shafiq",
    completions: 4860,
    dropOff: 0.09,
    steps: [
      { id: "s1", type: "ask", label: "Which programme", slot: "programme", prompt_en: "Which programme are you enrolled in?", prompt_ur: "آپ کس پروگرام میں داخل ہیں؟", validation: "must match a programme in the fee tariff" },
      { id: "s2", type: "ask", label: "New or repeat", slot: "enrolment_type", prompt_en: "Is this a new enrolment or a repeat course?", prompt_ur: "کیا یہ نیا داخلہ ہے یا دوبارہ کورس؟", validation: "one of: new, repeat" },
      { id: "s3", type: "lookup", label: "Fetch the amount", tool: "get_fee_tariff", toolArgs: "programme, enrolment_type", prompt_en: "", prompt_ur: "" },
      { id: "s4", type: "lookup", label: "Fetch the due date", tool: "get_deadline", toolArgs: 'service="Fee Challan"', prompt_en: "", prompt_ur: "" },
      { id: "s5", type: "confirm", label: "Explain how to pay", tool: "get_document_checklist", toolArgs: 'service="Fee Challan"', prompt_en: "Generate the challan from the portal and deposit before the due date.", prompt_ur: "پورٹل سے چالان بنائیں اور مقررہ تاریخ سے پہلے جمع کروائیں۔" },
      { id: "s6", type: "handoff", label: "Offer a human", prompt_en: "If the portal shows a different amount, I can connect you to Finance.", prompt_ur: "اگر پورٹل مختلف رقم دکھائے تو میں آپ کو شعبۂ مالیات سے ملا سکتا ہوں۔", terminal: true },
    ],
  },
  {
    id: "flow-result",
    en: "Result Enquiry",
    ur: "نتیجہ",
    intent: "result",
    serviceId: "svc-05",
    status: "live",
    updated: "2026-08-28",
    by: "Bilal Ahmed",
    completions: 7420,
    dropOff: 0.06,
    steps: [
      { id: "s1", type: "ask", label: "Which semester", slot: "semester", prompt_en: "Which semester's result do you need?", prompt_ur: "آپ کو کس سمسٹر کا نتیجہ چاہیے؟", validation: "must match an announced semester" },
      { id: "s2", type: "inform", label: "Explain where results appear", prompt_en: "Results are published on the results portal once the gazette is notified.", prompt_ur: "گزٹ کے اجرا کے بعد نتائج پورٹل پر شائع ہوتے ہیں۔" },
      { id: "s3", type: "confirm", label: "Point to the portal", prompt_en: "Enter your roll number on the results portal to see the provisional result.", prompt_ur: "عارضی نتیجہ دیکھنے کے لیے پورٹل پر اپنا رول نمبر درج کریں۔" },
      { id: "s4", type: "handoff", label: "Offer a human", prompt_en: "If your result is missing or looks wrong, I can raise it with Examinations.", prompt_ur: "اگر نتیجہ موجود نہیں یا غلط لگے تو میں شعبۂ امتحانات کو اطلاع دے سکتا ہوں۔", terminal: true },
    ],
  },
  {
    id: "flow-degree",
    en: "Degree Application",
    ur: "ڈگری کی درخواست",
    intent: "degree",
    serviceId: "svc-09",
    status: "live",
    updated: "2026-07-02",
    by: "Ayesha Tariq",
    completions: 1980,
    dropOff: 0.27,
    steps: [
      { id: "s1", type: "ask", label: "Graduating semester", slot: "semester", prompt_en: "Which semester did you complete your programme in?", prompt_ur: "آپ نے پروگرام کس سمسٹر میں مکمل کیا؟", validation: "must be a past semester" },
      { id: "s2", type: "lookup", label: "Fetch the deadline", tool: "get_deadline", toolArgs: 'service="Degree Application"', prompt_en: "", prompt_ur: "" },
      { id: "s3", type: "lookup", label: "Fetch the fee", tool: "get_fee_tariff", toolArgs: 'program="Degree", category="Normal service"', prompt_en: "", prompt_ur: "" },
      { id: "s4", type: "confirm", label: "Read back the six documents", tool: "get_document_checklist", toolArgs: 'service="Degree Application"', prompt_en: "You will need all six of these before the section will accept the file.", prompt_ur: "فائل جمع کروانے سے پہلے یہ چھ چیزیں لازمی ہیں۔" },
      { id: "s5", type: "inform", label: "State the processing range", prompt_en: "Published processing time is 6 to 8 weeks. I cannot promise a specific date.", prompt_ur: "اعلان شدہ دورانیہ 6 سے 8 ہفتے ہے۔ میں کوئی مخصوص تاریخ نہیں دے سکتا۔" },
      { id: "s6", type: "handoff", label: "Offer a human", prompt_en: "Shall I connect you to the Degree Section?", prompt_ur: "کیا میں آپ کو شعبۂ ڈگری سے ملاؤں؟", terminal: true },
    ],
  },
  {
    id: "flow-transcript",
    en: "Transcript / PRC",
    ur: "ٹرانسکرپٹ / پی آر سی",
    intent: "transcript",
    serviceId: "svc-10",
    status: "draft",
    updated: "2026-08-31",
    by: "Ayesha Tariq",
    completions: 0,
    dropOff: 0,
    steps: [
      { id: "s1", type: "ask", label: "Normal or urgent", slot: "urgency", prompt_en: "Do you need normal or urgent issuance?", prompt_ur: "آپ کو عام یا ارجنٹ اجرا چاہیے؟", validation: "one of: normal, urgent" },
      { id: "s2", type: "lookup", label: "Fetch the fee", tool: "get_fee_tariff", toolArgs: 'program="Transcript", category=urgency', prompt_en: "", prompt_ur: "" },
      { id: "s3", type: "ask", label: "Collection campus", slot: "campus", prompt_en: "Which campus will you collect it from?", prompt_ur: "آپ کس کیمپس سے وصول کریں گے؟", validation: "must match a campus record" },
    ],
  },
];

/** Step type metadata, shared by the canvas and the editor. */
export const STEP_TYPES = {
  ask: { label: "Ask", tone: "sky", note: "Collects a value into a slot" },
  lookup: { label: "Look up", tone: "violet", note: "Calls a grounding tool" },
  inform: { label: "Inform", tone: "grey", note: "States something already known" },
  confirm: { label: "Confirm", tone: "jade", note: "Reads the checklist or summary back" },
  handoff: { label: "Hand off", tone: "amber", note: "Passes to a human, always terminal" },
};

/** Tools the orchestrator exposes to the model (§4.3.4). */
export const TOOLS = [
  "get_fee_tariff",
  "get_deadline",
  "get_document_checklist",
  "get_department",
  "get_eligibility",
  "search_knowledge_base",
  "create_escalation_ticket",
];
