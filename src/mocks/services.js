/**
 * Service catalogue — the top-15 journeys that ship in Phase 1 (§2).
 *
 * `checklist` and `procedure` matter more than they look: they are what
 * get_document_checklist() returns, so the assistant reads these items out
 * to students verbatim. "copy" distinguishes an attested photocopy from an
 * original, which is the single most common follow-up question at the
 * counter.
 */
export const SERVICES = [
  {
    id: "svc-01",
    en: "Admission & Enrolment",
    ur: "داخلہ و اندراج",
    cat: "Admissions",
    verified: "2026-08-24",
    by: "Farah Nadeem",
    src: "Prospectus 2026-27 §2.1",
    queries: 4820,
    checklist: [
      { id: "c1", en: "CNIC or B-Form", ur: "شناختی کارڈ یا ب فارم", copy: true },
      { id: "c2", en: "Previous degree or certificate", ur: "پچھلی ڈگری یا سرٹیفکیٹ", copy: true },
      { id: "c3", en: "Two passport-size photographs", ur: "دو پاسپورٹ سائز تصاویر", copy: false },
      { id: "c4", en: "Paid fee challan receipt", ur: "ادا شدہ فیس چالان کی رسید", copy: false },
    ],
    procedure_en:
      "Apply online through the admission portal during the announced window. Attach scanned documents, generate the challan, pay at any designated bank branch, then upload the stamped receipt. Enrolment is provisional until the receipt is verified.",
    procedure_ur:
      "اعلان شدہ مدت کے دوران داخلہ پورٹل سے آن لائن درخواست دیں۔ دستاویزات منسلک کریں، چالان بنائیں، مقررہ بینک میں فیس جمع کروائیں اور مہر شدہ رسید اپلوڈ کریں۔",
  },
  {
    id: "svc-02",
    en: "Eligibility & Fee Tariff",
    ur: "اہلیت و فیس ٹیرف",
    cat: "Admissions",
    verified: "2026-08-24",
    by: "Farah Nadeem",
    src: "Fee Circular A-26 §1",
    queries: 3910,
    checklist: [
      { id: "c1", en: "Previous result card", ur: "پچھلا رزلٹ کارڈ", copy: true },
      { id: "c2", en: "Equivalence certificate, if foreign qualification", ur: "مساوات سرٹیفکیٹ", copy: true },
    ],
    procedure_en:
      "Eligibility is checked against the minimum marks and prerequisite qualification listed per programme in the prospectus. Fee amounts come from the current semester circular, not the prospectus.",
    procedure_ur:
      "اہلیت پروگرام کے مطابق کم از کم نمبروں اور پیشگی قابلیت سے جانچی جاتی ہے۔ فیس کی رقم موجودہ سمسٹر کے سرکلر سے لی جاتی ہے۔",
  },
  {
    id: "svc-03",
    en: "Fee Challan",
    ur: "فیس چالان",
    cat: "Finance",
    verified: "2026-08-19",
    by: "Imran Shafiq",
    src: "Fee Circular A-26 §4",
    queries: 6140,
    checklist: [
      { id: "c1", en: "Portal-generated challan form", ur: "پورٹل سے بنایا گیا چالان فارم", copy: false },
      { id: "c2", en: "CNIC for bank counter", ur: "بینک کاؤنٹر کے لیے شناختی کارڈ", copy: true },
    ],
    procedure_en:
      "Generate the challan from the student portal, print all three copies, and deposit at a designated branch before the due date. Portal status updates within two working days of the bank posting the payment.",
    procedure_ur:
      "پورٹل سے چالان بنائیں، تینوں کاپیاں پرنٹ کریں اور مقررہ تاریخ سے پہلے بینک میں جمع کروائیں۔ پورٹل کا اسٹیٹس دو کاروباری دن میں اپ ڈیٹ ہوتا ہے۔",
  },
  {
    id: "svc-04",
    en: "Scholarships",
    ur: "وظائف",
    cat: "Finance",
    verified: "2026-05-11",
    by: "Imran Shafiq",
    src: "Scholarship Policy 2026",
    queries: 1180,
    checklist: [
      { id: "c1", en: "Completed scholarship form", ur: "مکمل شدہ وظیفہ فارم", copy: false },
      { id: "c2", en: "Income certificate of guardian", ur: "سرپرست کا آمدنی سرٹیفکیٹ", copy: true },
      { id: "c3", en: "Previous semester result", ur: "پچھلے سمسٹر کا نتیجہ", copy: true },
      { id: "c4", en: "CNIC of student and guardian", ur: "طالبعلم اور سرپرست کا شناختی کارڈ", copy: true },
      { id: "c5", en: "Bank account details", ur: "بینک اکاؤنٹ کی تفصیلات", copy: false },
    ],
    procedure_en:
      "Submit the form to the regional campus before the announced deadline. Shortlisting is on need and merit combined. Disbursement is to the student's own account only.",
    procedure_ur:
      "اعلان شدہ تاریخ سے پہلے فارم علاقائی کیمپس میں جمع کروائیں۔ انتخاب ضرورت اور میرٹ دونوں پر ہوتا ہے۔",
  },
  {
    id: "svc-05",
    en: "Result Enquiry",
    ur: "نتیجہ",
    cat: "Examinations",
    verified: "2026-08-28",
    by: "Bilal Ahmed",
    src: "Exam Regs 2026 §7",
    queries: 8730,
    checklist: [{ id: "c1", en: "Roll number", ur: "رول نمبر", copy: false }],
    procedure_en:
      "Results are published on the results portal by semester. Provisional results appear before the gazette is notified; the gazette is the official record.",
    procedure_ur:
      "نتائج سمسٹر کے حساب سے پورٹل پر شائع ہوتے ہیں۔ گزٹ کا اجرا ہی سرکاری ریکارڈ ہے۔",
  },
  {
    id: "svc-06",
    en: "Date Sheet",
    ur: "ڈیٹ شیٹ",
    cat: "Examinations",
    verified: "2026-08-28",
    by: "Bilal Ahmed",
    src: "Exam Regs 2026 §5",
    queries: 2560,
    checklist: [{ id: "c1", en: "Roll number", ur: "رول نمبر", copy: false }],
    procedure_en:
      "Published roughly four weeks before the examination window. Clashes between two papers in the same slot must be reported to the Examinations Department within seven days of publication.",
    procedure_ur:
      "امتحان سے تقریباً چار ہفتے پہلے جاری ہوتی ہے۔ دو پرچوں کے ٹکراؤ کی اطلاع سات دن کے اندر شعبۂ امتحانات کو دیں۔",
  },
  {
    id: "svc-07",
    en: "Roll Number Slip",
    ur: "رول نمبر سلپ",
    cat: "Examinations",
    verified: "2026-08-12",
    by: "Bilal Ahmed",
    src: "Exam Regs 2026 §5.3",
    queries: 3340,
    checklist: [{ id: "c1", en: "Registration number", ur: "رجسٹریشن نمبر", copy: false }],
    procedure_en:
      "Downloadable from the portal once dues are cleared and assignments are marked as received. A printed slip and CNIC are both required at the examination centre.",
    procedure_ur:
      "فیس کی ادائیگی اور اسائنمنٹس موصول ہونے کے بعد پورٹل سے ڈاؤن لوڈ کریں۔ امتحانی مرکز میں پرنٹ شدہ سلپ اور شناختی کارڈ دونوں لازمی ہیں۔",
  },
  {
    id: "svc-08",
    en: "Assignment Submission",
    ur: "اسائنمنٹ جمع کروانا",
    cat: "Academics",
    verified: "2026-08-30",
    by: "Sana Yousuf",
    src: "Student Handbook §6",
    queries: 5210,
    checklist: [
      { id: "c1", en: "Completed assignment with title page", ur: "ٹائٹل پیج کے ساتھ مکمل اسائنمنٹ", copy: false },
      { id: "c2", en: "Tutor allocation slip", ur: "ٹیوٹر الاٹمنٹ سلپ", copy: true },
    ],
    procedure_en:
      "Submit to the allocated tutor by the published date, either in person or by registered post. Keep the dispatch receipt until marks appear on the portal.",
    procedure_ur:
      "مقررہ تاریخ تک اپنے ٹیوٹر کو خود یا رجسٹرڈ ڈاک سے بھیجیں۔ نمبر پورٹل پر آنے تک رسید محفوظ رکھیں۔",
  },
  {
    id: "svc-09",
    en: "Degree Application",
    ur: "ڈگری کی درخواست",
    cat: "Certification",
    verified: "2026-07-02",
    by: "Ayesha Tariq",
    src: "Degree Manual §3",
    queries: 2970,
    checklist: [
      { id: "c1", en: "Degree application form", ur: "ڈگری درخواست فارم", copy: false },
      { id: "c2", en: "All semester result cards", ur: "تمام سمسٹر کے رزلٹ کارڈ", copy: true },
      { id: "c3", en: "CNIC", ur: "شناختی کارڈ", copy: true },
      { id: "c4", en: "Two passport-size photographs", ur: "دو پاسپورٹ سائز تصاویر", copy: false },
      { id: "c5", en: "Paid degree fee challan", ur: "ادا شدہ ڈگری فیس چالان", copy: false },
      { id: "c6", en: "No-dues clearance from the campus", ur: "کیمپس سے واجبات کی کلیئرنس", copy: false },
    ],
    procedure_en:
      "Submit the complete set to the Degree Section after the gazette is notified. Published processing time is 6 to 8 weeks for normal issuance.",
    procedure_ur:
      "گزٹ کے اجرا کے بعد مکمل دستاویزات شعبۂ ڈگری میں جمع کروائیں۔ عام اجرا میں 6 سے 8 ہفتے لگتے ہیں۔",
  },
  {
    id: "svc-10",
    en: "Transcript / PRC",
    ur: "ٹرانسکرپٹ / پی آر سی",
    cat: "Certification",
    verified: "2026-07-02",
    by: "Ayesha Tariq",
    src: "Degree Manual §4",
    queries: 2140,
    checklist: [
      { id: "c1", en: "Transcript request form", ur: "ٹرانسکرپٹ درخواست فارم", copy: false },
      { id: "c2", en: "CNIC", ur: "شناختی کارڈ", copy: true },
      { id: "c3", en: "Paid fee challan", ur: "ادا شدہ فیس چالان", copy: false },
      { id: "c4", en: "Authority letter, if collected by another person", ur: "اجازت نامہ", copy: false },
    ],
    procedure_en:
      "Normal issuance is 3 to 4 weeks; urgent is 5 working days at the higher tariff. Collection is in person or by courier at the applicant's cost.",
    procedure_ur:
      "عام اجرا 3 سے 4 ہفتے، ارجنٹ 5 کاروباری دن میں۔ وصولی بذات خود یا کورئیر کے ذریعے۔",
  },
  {
    id: "svc-11",
    en: "Document Verification",
    ur: "دستاویزات کی تصدیق",
    cat: "Certification",
    verified: "2026-03-18",
    by: "Ayesha Tariq",
    src: "Degree Manual §6",
    queries: 890,
    checklist: [
      { id: "c1", en: "Original document to be verified", ur: "اصل دستاویز", copy: false },
      { id: "c2", en: "CNIC", ur: "شناختی کارڈ", copy: true },
      { id: "c3", en: "Verification fee challan", ur: "تصدیقی فیس چالان", copy: false },
    ],
    procedure_en:
      "University verification confirms the record against the gazette. Attestation for use abroad is handled by HEC separately and is not a University service.",
    procedure_ur:
      "یونیورسٹی کی تصدیق گزٹ سے ریکارڈ کی مطابقت کرتی ہے۔ بیرون ملک استعمال کے لیے تصدیق ایچ ای سی کرتا ہے۔",
  },
  {
    id: "svc-12",
    en: "Paper Rechecking",
    ur: "پرچے کی دوبارہ جانچ",
    cat: "Examinations",
    verified: "2026-08-05",
    by: "Bilal Ahmed",
    src: "Exam Regs 2026 §9",
    queries: 1620,
    checklist: [
      { id: "c1", en: "Rechecking application form", ur: "دوبارہ جانچ کا فارم", copy: false },
      { id: "c2", en: "Paid rechecking fee, per paper", ur: "فی پرچہ ادا شدہ فیس", copy: false },
    ],
    procedure_en:
      "Rechecking confirms totalling and that no question was left unmarked. It is not a re-evaluation of answers. Applications close 30 days after the result is declared.",
    procedure_ur:
      "دوبارہ جانچ میں نمبروں کا جوڑ اور کوئی سوال بغیر نمبر تو نہیں، یہ دیکھا جاتا ہے۔ یہ دوبارہ مارکنگ نہیں۔",
  },
  {
    id: "svc-13",
    en: "Record Correction",
    ur: "ریکارڈ کی تصحیح",
    cat: "Records",
    verified: "2026-02-27",
    by: "Sana Yousuf",
    src: "Records SOP v4",
    queries: 1050,
    checklist: [
      { id: "c1", en: "Correction request on plain paper", ur: "سادہ کاغذ پر درخواست", copy: false },
      { id: "c2", en: "CNIC showing the correct spelling", ur: "درست ہجے والا شناختی کارڈ", copy: true },
      { id: "c3", en: "Matric certificate", ur: "میٹرک سرٹیفکیٹ", copy: true },
      { id: "c4", en: "Affidavit on stamp paper", ur: "اسٹامپ پیپر پر حلف نامہ", copy: false },
      { id: "c5", en: "Correction fee challan", ur: "تصحیح فیس چالان", copy: false },
    ],
    procedure_en:
      "Name and date-of-birth corrections follow the CNIC and matric certificate, which take precedence over the admission form. Corrections after degree issuance require the original degree to be surrendered.",
    procedure_ur:
      "نام اور تاریخ پیدائش کی تصحیح شناختی کارڈ اور میٹرک سرٹیفکیٹ کے مطابق کی جاتی ہے۔",
  },
  {
    id: "svc-14",
    en: "NOC Issuance",
    ur: "این او سی کا اجرا",
    cat: "Records",
    verified: "2026-06-14",
    by: "Sana Yousuf",
    src: "Migration Guidelines §2",
    queries: 760,
    checklist: [
      { id: "c1", en: "NOC request form", ur: "این او سی درخواست فارم", copy: false },
      { id: "c2", en: "No-dues clearance", ur: "واجبات کی کلیئرنس", copy: false },
      { id: "c3", en: "CNIC", ur: "شناختی کارڈ", copy: true },
    ],
    procedure_en:
      "Issued once dues are cleared and no disciplinary case is pending. Published processing time is 10 working days.",
    procedure_ur:
      "واجبات کی ادائیگی اور کوئی تادیبی کارروائی زیر التوا نہ ہونے پر جاری ہوتا ہے۔",
  },
  {
    id: "svc-15",
    en: "Migration Certificate",
    ur: "مائیگریشن سرٹیفکیٹ",
    cat: "Records",
    verified: "2026-06-14",
    by: "Sana Yousuf",
    src: "Migration Guidelines §5",
    queries: 640,
    checklist: [
      { id: "c1", en: "Migration application form", ur: "مائیگریشن فارم", copy: false },
      { id: "c2", en: "NOC from this University", ur: "اس یونیورسٹی سے این او سی", copy: false },
      { id: "c3", en: "Last result card", ur: "آخری رزلٹ کارڈ", copy: true },
      { id: "c4", en: "Migration fee challan", ur: "مائیگریشن فیس چالان", copy: false },
    ],
    procedure_en:
      "Issued to students leaving for another institution. The receiving institution normally requires the original, so no duplicate is issued without an affidavit.",
    procedure_ur:
      "دوسرے ادارے میں جانے والے طلبہ کے لیے۔ نقل صرف حلف نامے پر جاری ہوتی ہے۔",
  },
  {
    id: "svc-16",
    en: "Bonafide / MOI Letter",
    ur: "بونافائیڈ / ذریعۂ تعلیم",
    cat: "Records",
    verified: "2026-08-21",
    by: "Sana Yousuf",
    src: "Records SOP v4 §8",
    queries: 1430,
    checklist: [
      { id: "c1", en: "Written request stating the purpose", ur: "مقصد بیان کرتی درخواست", copy: false },
      { id: "c2", en: "Student card or CNIC", ur: "طالبعلم کارڈ یا شناختی کارڈ", copy: true },
    ],
    procedure_en:
      "A Medium of Instruction letter confirms that the programme was taught and examined in English. Commonly requested for visa and overseas admission files.",
    procedure_ur:
      "ذریعۂ تعلیم کا خط تصدیق کرتا ہے کہ پروگرام انگریزی میں پڑھایا گیا۔ ویزا اور بیرون ملک داخلے کے لیے درکار ہوتا ہے۔",
  },
];
