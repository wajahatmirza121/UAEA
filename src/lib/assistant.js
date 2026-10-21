import { normalise } from "./classify";
import { fmtDate, fmtPKR } from "./format";
import { freshness } from "./freshness";

/**
 * Answer composer — a working stand-in for §4.3.4.
 *
 * The rule the whole architecture rests on: the assistant may only state a
 * fee, a date or a document requirement that a tool call returned. Every
 * function below therefore builds its reply FROM tool results, and if the
 * lookup comes back empty it says so and offers a human rather than filling
 * the gap from anywhere else.
 *
 * Replies are templated in three languages because a student who writes in
 * Roman Urdu should not be answered in English.
 */

/* ── phrase book ──────────────────────────────────────────────────────── */

const T = {
  en: {
    feeIs: (p, a) => `The fee for ${p} is ${a}.`,
    effective: (d) => `This rate has applied since ${d}.`,
    whichProgramme: "Which programme are you asking about? Fees differ by programme and by whether it is a new enrolment or a repeat.",
    deadlineIs: (s, d) => `The deadline for ${s} is ${d}.`,
    deadlinePassed: (d) => `That date, ${d}, has already passed.`,
    daysLeft: (n) => `That is ${n} days from today.`,
    checklistIntro: (n) => `You will need these ${n} documents:`,
    original: "original",
    copy: "attested copy",
    noData: "I do not have that recorded, so I would rather not guess.",
    talkToHuman: (d, p) => `You can reach ${d} on ${p}.`,
    lastChecked: (d) => `Last checked ${d}.`,
    procedure: "How it works:",
    resultWhere: "Results are published on the University results portal once the gazette is notified. Enter your roll number there to see the provisional result.",
    contactIs: (d, p, h) => `${d} — ${p}. Office hours ${h}.`,
    whichCampus: "Which campus or department do you need? I can give you the number and office hours.",
    processing: (s) => `Published processing time: ${s}.`,
  },
  roman: {
    feeIs: (p, a) => `${p} ki fee ${a} hai.`,
    effective: (d) => `Ye rate ${d} se lagoo hai.`,
    whichProgramme: "Aap kis programme ke baare mein pooch rahe hain? Fees har programme ki alag hai, aur naye daakhle aur repeat course ki bhi alag hoti hai.",
    deadlineIs: (s, d) => `${s} ki aakhri tareekh ${d} hai.`,
    deadlinePassed: (d) => `Ye tareekh, ${d}, guzar chuki hai.`,
    daysLeft: (n) => `Aaj se ${n} din baaqi hain.`,
    checklistIntro: (n) => `Aapko ye ${n} cheezein darkaar hongi:`,
    original: "asal",
    copy: "tasdeeq shuda copy",
    noData: "Ye mere record mein darj nahi hai, is liye main andaaza nahi lagana chahta.",
    talkToHuman: (d, p) => `Aap ${d} se ${p} par raabta kar sakte hain.`,
    lastChecked: (d) => `Aakhri baar ${d} ko tasdeeq hui.`,
    procedure: "Tareeqa kaar:",
    resultWhere: "Gazette ke ijra ke baad nataij University ke results portal par shaya hote hain. Wahan apna roll number daal kar aarzi nateeja dekh sakte hain.",
    contactIs: (d, p, h) => `${d} — ${p}. Office hours ${h}.`,
    whichCampus: "Aapko kaunsa campus ya shoba chahiye? Main number aur office hours de sakta hoon.",
    processing: (s) => `Elaan shuda muddat: ${s}.`,
  },
  ur: {
    feeIs: (p, a) => `${p} کی فیس ${a} ہے۔`,
    effective: (d) => `یہ نرخ ${d} سے لاگو ہے۔`,
    whichProgramme: "آپ کس پروگرام کے بارے میں پوچھ رہے ہیں؟ ہر پروگرام کی فیس مختلف ہے، اور نئے داخلے اور دوبارہ کورس کی بھی الگ ہے۔",
    deadlineIs: (s, d) => `${s} کی آخری تاریخ ${d} ہے۔`,
    deadlinePassed: (d) => `یہ تاریخ، ${d}، گزر چکی ہے۔`,
    daysLeft: (n) => `آج سے ${n} دن باقی ہیں۔`,
    checklistIntro: (n) => `آپ کو یہ ${n} چیزیں درکار ہوں گی:`,
    original: "اصل",
    copy: "تصدیق شدہ نقل",
    noData: "یہ میرے ریکارڈ میں درج نہیں، اس لیے میں اندازہ نہیں لگانا چاہتا۔",
    talkToHuman: (d, p) => `آپ ${d} سے ${p} پر رابطہ کر سکتے ہیں۔`,
    lastChecked: (d) => `آخری بار ${d} کو تصدیق ہوئی۔`,
    procedure: "طریقۂ کار:",
    resultWhere: "گزٹ کے اجرا کے بعد نتائج یونیورسٹی کے پورٹل پر شائع ہوتے ہیں۔ وہاں اپنا رول نمبر درج کر کے عارضی نتیجہ دیکھ سکتے ہیں۔",
    contactIs: (d, p, h) => `${d} — ${p}۔ اوقاتِ کار ${h}۔`,
    whichCampus: "آپ کو کون سا کیمپس یا شعبہ چاہیے؟ میں نمبر اور اوقاتِ کار بتا سکتا ہوں۔",
    processing: (s) => `اعلان شدہ مدت: ${s}۔`,
  },
};

/* ── helpers ──────────────────────────────────────────────────────────── */

const daysUntil = (iso) => Math.ceil((new Date(iso) - new Date("2026-09-01")) / 86400000);

/** Pull a programme name out of free text by matching the tariff table. */
function findProgramme(text, fees) {
  const t = normalise(text);
  const hit = fees.find((f) => {
    const words = normalise(f.program).split(" ").filter((w) => w.length > 2);
    return words.length > 0 && words.every((w) => t.includes(w));
  });
  if (hit) return hit;

  // Common shorthands students actually use.
  const aliases = [
    [/\bbs ?cs\b|computer science|\bcs\b/, "BS Computer Science"],
    [/\bb ?ed\b|bed\b/, "B.Ed (1.5 Year)"],
    [/matric|ssc/, "Matric (SSC)"],
    [/inter|hssc|fa\b|fsc/, "Intermediate (HSSC)"],
    [/\bma urdu\b|urdu/, "MA Urdu"],
    [/msc math|mathematics/, "MSc Mathematics"],
    [/mphil|m\.phil/, "MPhil Education"],
  ];
  for (const [re, name] of aliases) {
    if (re.test(t)) return fees.find((f) => f.program === name) || null;
  }
  return null;
}

/** Find the campus or department a student named. */
function findDepartment(text, departments) {
  const t = normalise(text);
  return (
    departments.find((d) => {
      const key = normalise(d.en).replace("regional campus ", "");
      return key.length > 3 && t.includes(key);
    }) || null
  );
}

const checklistLines = (service, lang) =>
  (service.checklist || []).map((c) => {
    const name = lang === "ur" ? c.ur || c.en : c.en;
    return `${name} (${c.copy ? T[lang].copy : T[lang].original})`;
  });

/* ── the engine ───────────────────────────────────────────────────────── */

/**
 * Build a grounded reply.
 *
 * Returns the tool calls that were made, the answer text, the source citation
 * and its verification date, plus follow-ups. `resolved: false` means no tool
 * produced an answer, and the UI should offer a human.
 */
export function answer({ text, classification, lang, store }) {
  const t = T[lang];
  const toolCalls = [];
  const call = (name, args, result) => {
    toolCalls.push({ name, args, result });
    return result;
  };

  const { intent, service, department } = classification;
  const { fees, deadlines, departments } = store;

  const withMeta = (body, src, verified, extra = {}) => ({
    toolCalls,
    body,
    source: src,
    verified,
    resolved: true,
    ...extra,
  });

  const unresolved = (body) => ({
    toolCalls,
    body,
    source: null,
    verified: null,
    resolved: false,
  });

  /* — fees — */
  if (intent === "fee_tariff") {
    const fee = findProgramme(text, fees);
    if (!fee) {
      return {
        toolCalls,
        body: [t.whichProgramme],
        source: null,
        verified: null,
        resolved: true,
        needsSlot: "programme",
        options: [...new Set(fees.map((f) => f.program))].slice(0, 7),
      };
    }
    call(
      "get_fee_tariff",
      `program="${fee.program}", category="${fee.cat}"`,
      `amount=${fee.amount} PKR · effective ${fee.from} · ${fee.src}`
    );
    return withMeta(
      [t.feeIs(fee.program, fmtPKR(fee.amount)), t.effective(fmtDate(fee.from))],
      fee.src,
      fee.verified
    );
  }

  /* What is the student actually asking for? A rechecking question that says
     "fees" wants the amount, not the application window, and a degree question
     that says "kaghzaat" wants the checklist before anything else. */
  const nt = normalise(text);
  const wantsFee = /\b(fee|kitni|cost|charges|amount|rupay)\b/.test(nt) || /فیس|رقم/.test(text);
  const wantsDocs =
    /\b(document|documents|kaghzaat|kagzat|dastavez|chahiye|checklist|papers|lagenge)\b/.test(nt) ||
    /دستاویز|کاغذ|چاہی/.test(text);

  /* Service charges that live in the tariff table under their own name. */
  const SERVICE_FEE = {
    rechecking: ["Rechecking", "Per paper"],
    transcript: ["Transcript", "Urgent service"],
    degree: ["Degree", "Normal service"],
    migration: ["Migration Certificate", "Normal service"],
    noc: ["NOC", "Normal service"],
    correction: ["Record Correction", "Normal service"],
  };

  /* — deadline-led intents — */
  const DEADLINE_FOR = {
    admission: "Admission & Enrolment",
    fee_challan: "Fee Challan",
    assignments: "Assignment 1",
    degree: "Degree Application",
    date_sheet: "Date Sheet publication",
    rechecking: "Paper Rechecking window",
    scholarships: "Scholarship applications",
  };

  const lines = [];
  const docLines = [];
  let source = null;
  let verified = null;

  if (SERVICE_FEE[intent]) {
    const [program, cat] = SERVICE_FEE[intent];
    const row = fees.find((f) => f.program === program && f.cat === cat);
    if (row) {
      call(
        "get_fee_tariff",
        `program="${row.program}", category="${row.cat}"`,
        `amount=${row.amount} PKR · ${row.src}`
      );
      lines.push(t.feeIs(lang === "ur" && service ? service.ur : row.program, fmtPKR(row.amount)));
      source = row.src;
      verified = row.verified;
    }
  }

  if (DEADLINE_FOR[intent] && !(wantsFee && lines.length)) {
    const dl = deadlines.find((d) => d.service === DEADLINE_FOR[intent]);
    if (dl) {
      call("get_deadline", `service="${dl.service}"`, `${dl.date} · ${dl.semester} · ${dl.src}`);
      const left = daysUntil(dl.date);
      const dlName = lang === "ur" && service ? service.ur : dl.service;
      lines.push(t.deadlineIs(dlName, fmtDate(dl.date)));
      lines.push(left < 0 ? t.deadlinePassed(fmtDate(dl.date)) : t.daysLeft(left));
      source = dl.src;
      verified = dl.verified;
    }
  }

  if (intent === "result") {
    lines.push(t.resultWhere);
    call("search_knowledge_base", 'query="where are results published"', "1 chunk · Exam Regs 2026 §7");
    source = "Exam Regs 2026 §7";
    verified = store.services.find((s) => s.id === "svc-05")?.verified;
  }

  if (intent === "department_lookup") {
    const dept = findDepartment(text, departments);
    if (!dept) {
      return {
        toolCalls,
        body: [t.whichCampus],
        source: null,
        verified: null,
        resolved: true,
        needsSlot: "campus",
        options: departments.slice(0, 8).map((d) => d.en),
      };
    }
    call(
      "get_department",
      `name="${dept.en}"`,
      `${dept.en} · ${dept.phone} · ${dept.campus} · ${dept.hours}`
    );
    return withMeta(
      [t.contactIs(lang === "ur" ? dept.ur : dept.en, dept.phone, dept.hours)],
      `${dept.en} record`,
      dept.verified,
      { department: dept }
    );
  }

  /* — service-backed intents: checklist and procedure — */
  if (service) {
    const items = checklistLines(service, lang);
    if (items.length) {
      call(
        "get_document_checklist",
        `service="${service.en}"`,
        `${items.length} items · ${service.checklist.map((c) => c.en).join(", ")}`
      );
      docLines.push(t.checklistIntro(items.length));
      docLines.push({ list: items });
    }

    // Documents lead when they were what was asked for; otherwise they follow
    // the date or the amount, which is what most students open with.
    if (wantsDocs) lines.unshift(...docLines);
    else lines.push(...docLines);

    const proc = lang === "ur" ? service.procedure_ur : service.procedure_en;
    if (proc) {
      lines.push(`${t.procedure} ${proc}`);
    }

    source = source || service.src;
    verified = verified || service.verified;
  }

  if (lines.length === 0) {
    return unresolved([t.noData, department ? t.talkToHuman(department.en, department.phone) : ""]);
  }

  return withMeta(lines, source, verified);
}

/** Freshness caveat appended under every grounded answer. */
export function trustLine(verified, lang) {
  if (!verified) return null;
  const f = freshness(verified);
  return {
    text: T[lang].lastChecked(fmtDate(verified)),
    tone: f.tone,
    stale: f.tone !== "jade",
  };
}

/** Sensible next questions, so the student is not left staring at a box. */
export function followUps(intent, lang) {
  const sets = {
    en: {
      fee_tariff: ["Where do I get the challan?", "When is the last date to pay?"],
      admission: ["What does the programme cost?", "Can I still apply late?"],
      fee_challan: ["What is the fee for BS Computer Science?", "Who do I call if payment is not showing?"],
      degree: ["What is the degree fee?", "How long does it take?"],
      transcript: ["What is the urgent transcript fee?", "Where do I collect it?"],
      result: ["When is the date sheet published?", "How do I apply for rechecking?"],
      class_schedule: ["When are the mid-term exams?", "BSCS 1st semester timetable"],
      timetable: ["Who teaches these courses?", "When do classes start?"],
      hostel: ["Hostel allotment documents?", "Hostel gate timings?"],
      scholarships: ["Need-based scholarship documents?", "What is the BSCS fee?"],
      otp_verification: ["Show my attendance too", "What is my fee status?"],
      default: ["What is the admission deadline?", "Give me my campus contact"],
    },
    roman: {
      fee_tariff: ["Challan kahan se banega?", "Jama karane ki aakhri tareekh?"],
      admission: ["Is programme ki fees kitni hai?", "Late admission ho sakta hai?"],
      fee_challan: ["BS CS ki fees kitni hai?", "Payment show na ho to kis se baat karun?"],
      degree: ["Degree ki fees kitni hai?", "Kitna waqt lagta hai?"],
      transcript: ["Urgent transcript ki fees?", "Kahan se milega?"],
      result: ["Date sheet kab aayegi?", "Rechecking kaise karwaun?"],
      class_schedule: ["Mid term exams kab hain?", "BSCS 1st semester ka timetable"],
      timetable: ["Ye courses kaun parhata hai?", "Classes kab shuru hongi?"],
      hostel: ["Hostel ke liye kya documents chahiye?", "Hostel ki timings kya hain?"],
      scholarships: ["Need based scholarship ke documents?", "BSCS ki fees kitni hai?"],
      otp_verification: ["Attendance bhi dikhao", "Fee status kya hai?"],
      default: ["Admission ki last date?", "Mere campus ka number chahiye"],
    },
    ur: {
      fee_tariff: ["چالان کہاں سے بنے گا؟", "جمع کرانے کی آخری تاریخ؟"],
      admission: ["اس پروگرام کی فیس کتنی ہے؟", "کیا لیٹ داخلہ ہو سکتا ہے؟"],
      fee_challan: ["بی ایس سی ایس کی فیس کتنی ہے؟", "ادائیگی ظاہر نہ ہو تو کس سے بات کروں؟"],
      degree: ["ڈگری کی فیس کتنی ہے؟", "کتنا وقت لگتا ہے؟"],
      transcript: ["ارجنٹ ٹرانسکرپٹ کی فیس؟", "کہاں سے ملے گا؟"],
      result: ["ڈیٹ شیٹ کب آئے گی؟", "دوبارہ جانچ کیسے کروائیں؟"],
      default: ["داخلے کی آخری تاریخ؟", "میرے کیمپس کا نمبر چاہیے"],
    },
  };
  const set = sets[lang] || sets.en;
  return set[intent] || set.default;
}
