import { useState, useEffect, useMemo } from "react";
import { fmtDate, fmtPKR } from "@/lib/format";

const BLANK = {
  en: "", ur: "", cat: "", program: "", service: "", semester: "",
  campus: "", phone: "", email: "", hours: "09:00 – 16:30",
  amount: "", date: "", from: "", src: "", queries: 0,
  checklist: [], procedure_en: "", procedure_ur: "",
};

/** Field labels used by both validation messages and the save-time diff. */
const LABELS = {
  en: "Name (English)", ur: "Name (Urdu)", cat: "Category", program: "Programme",
  service: "Deadline", semester: "Semester", amount: "Amount", from: "Effective from",
  date: "Date", phone: "Phone", email: "Email", campus: "Campus", hours: "Office hours",
  src: "Source", procedure_en: "Procedure (English)", procedure_ur: "Procedure (Urdu)",
};

const show = (key, value) => {
  if (key === "amount") return fmtPKR(value);
  if (key === "from" || key === "date") return value ? fmtDate(value) : "—";
  if (value === "" || value === null || value === undefined) return "—";
  const s = String(value);
  return s.length > 60 ? `${s.slice(0, 57)}…` : s;
};

/**
 * Form state, validation and change tracking for the record modal.
 *
 * Validation runs on every keystroke but only surfaces on a field the person
 * has already left, so the form does not shout at someone halfway through
 * typing their first character.
 */
export function useRecordForm({ open, record, tab }) {
  const [values, setValues] = useState(BLANK);
  const [touched, setTouched] = useState({});

  useEffect(() => {
    if (!open) return;
    setValues(
      record
        ? { ...BLANK, ...record, amount: record.amount ?? "", checklist: record.checklist || [] }
        : BLANK
    );
    setTouched({});
  }, [open, record]);

  const set = (key) => (e) =>
    setValues((p) => ({ ...p, [key]: e?.target ? e.target.value : e }));
  const setValue = (key, value) => setValues((p) => ({ ...p, [key]: value }));
  const blur = (key) => () => setTouched((p) => ({ ...p, [key]: true }));

  const errors = useMemo(() => {
    const e = {};
    if (tab === "fees") {
      if (!String(values.program).trim()) e.program = "Programme name is required";
      if (String(values.amount) === "") e.amount = "Enter the amount in rupees";
      else if (!/^\d+$/.test(String(values.amount)))
        e.amount = "Digits only, no commas or currency symbol";
      else if (Number(values.amount) > 500000)
        e.amount = "Above the Rs 500,000 ceiling — check the circular";
      if (!/^\d{4}-\d{2}-\d{2}$/.test(values.from || "")) e.from = "Use the date picker";
    } else if (tab === "deadlines") {
      if (!String(values.service).trim())
        e.service = "Name it the way a student would search for it";
      if (!/^\d{4}-\d{2}-\d{2}$/.test(values.date || "")) e.date = "Use the date picker";
      if (!String(values.semester).trim()) e.semester = "Which semester does this apply to?";
    } else if (tab === "departments") {
      if (!String(values.en).trim()) e.en = "English name is required";
      if (!/^\d{3,4}-\d{6,8}$/.test(values.phone || "")) e.phone = "Format as 051-9250101";
      if (values.email && !/^[^@\s]+@[^@\s]+\.[a-z]{2,}$/i.test(values.email))
        e.email = "That does not look like an email address";
    } else {
      if (!String(values.en).trim()) e.en = "English name is required";
      if (!String(values.ur).trim())
        e.ur = "Urdu name is required — students search in both scripts";
      if (!String(values.cat).trim()) e.cat = "Pick a category";
    }
    // Every record, in every table, must cite where the fact came from.
    if (!String(values.src).trim()) e.src = "Cite the document and section this came from";
    return e;
  }, [values, tab]);

  /** Plain-language diff of what a student would notice. */
  const changes = useMemo(() => {
    const fieldKeys = Object.keys(LABELS).filter((k) => k in values);

    const scalar = record
      ? fieldKeys
          .filter((k) => String(values[k] ?? "") !== String(record[k] ?? ""))
          .map((k) => ({ field: LABELS[k], from: show(k, record[k]), to: show(k, values[k]) }))
      : fieldKeys
          .filter((k) => values[k] !== "" && values[k] !== undefined)
          .map((k) => ({ field: LABELS[k], from: "—", to: show(k, values[k]) }));

    // Checklists are compared by length and content rather than by identity,
    // since reordering is a real change students will hear.
    const before = JSON.stringify((record?.checklist || []).map((c) => [c.en, c.ur, c.copy]));
    const after = JSON.stringify((values.checklist || []).map((c) => [c.en, c.ur, c.copy]));
    if (before !== after) {
      scalar.push({
        field: "Checklist",
        from: `${(record?.checklist || []).length} items`,
        to: `${(values.checklist || []).length} items`,
      });
    }

    return scalar;
  }, [values, record]);

  return {
    values,
    set,
    setValue,
    blur,
    errors,
    changes,
    valid: Object.keys(errors).length === 0,
    error: (key) => (touched[key] ? errors[key] : undefined),
    touchAll: () => setTouched(Object.fromEntries(Object.keys(errors).map((k) => [k, true]))),
  };
}
