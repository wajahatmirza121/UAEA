import { useState } from "react";
import { ShieldCheck } from "lucide-react";
import Modal from "@/components/ui/Modal";
import Button from "@/components/ui/Button";
import Field from "@/components/ui/Field";
import Note from "@/components/ui/Note";
import DiffRow from "@/components/ui/DiffRow";
import ChecklistEditor from "./ChecklistEditor";
import { useRecordForm } from "./useRecordForm";
import { ISO_TODAY, TABLE_IMPACT, CURRENT_USER } from "@/lib/constants";
import { fmtDate, nfmt } from "@/lib/format";

/**
 * Add or edit a catalogue record.
 *
 * The part that matters is at the bottom: before saving an edit, the editor
 * sees a plain-language diff plus how many students asked about this record
 * in the last 90 days. Someone changing a fee from Rs 28,500 to Rs 31,000
 * should see the number of conversations that will quote it.
 */
export default function RecordModal({ open, record, tab, onClose, onSave }) {
  const [saving, setSaving] = useState(false);
  const form = useRecordForm({ open, record, tab });
  const { values: v, set, setValue, blur, error, valid, changes } = form;

  const save = () => {
    setSaving(true);
    // Simulated round-trip so the spinner is a real state, not decoration.
    setTimeout(() => {
      onSave(
        {
          ...v,
          amount: v.amount === "" ? null : Number(v.amount),
          verified: ISO_TODAY,
          by: CURRENT_USER.name,
        },
        changes
      );
      setSaving(false);
    }, 700);
  };

  const attempt = () => {
    form.touchAll();
    if (valid) save();
  };

  const dateField = (key, label) => (
    <Field label={label} error={error(key)}>
      <input
        type="date"
        className={`ua-input${error(key) ? " bad" : ""}`}
        value={v[key] || ""}
        onChange={set(key)}
        onBlur={blur(key)}
      />
    </Field>
  );

  return (
    <Modal
      open={open}
      onClose={onClose}
      wide={tab === "services"}
      title={record ? "Edit record" : "Add record"}
      desc="Every record needs a source citation. Students see it, and so does the assistant when it answers."
      footer={
        <>
          <Button variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button
            variant="primary"
            loading={saving}
            disabled={!valid || (record && changes.length === 0)}
            onClick={attempt}
          >
            {saving ? "Saving" : record ? "Save changes" : "Add record"}
          </Button>
        </>
      }
    >
      {tab === "fees" && (
        <>
          <div className="ua-grid2">
            <Field label="Programme" error={error("program")}>
              <input
                className={`ua-input${error("program") ? " bad" : ""}`}
                placeholder="BS Computer Science"
                value={v.program}
                onChange={set("program")}
                onBlur={blur("program")}
              />
            </Field>
            <Field label="Basis">
              <select className="ua-select" value={v.cat} onChange={set("cat")}>
                <option value="">Select a basis</option>
                <option>Semester (new)</option>
                <option>Per credit hour (repeat)</option>
                <option>Annual</option>
                <option>Per paper</option>
                <option>Normal service</option>
                <option>Urgent service</option>
              </select>
            </Field>
          </div>
          <div className="ua-grid2">
            <Field label="Amount" hint="PKR" error={error("amount")}>
              <input
                className={`ua-input ua-num${error("amount") ? " bad" : ""}`}
                inputMode="numeric"
                placeholder="28500"
                value={v.amount}
                onChange={set("amount")}
                onBlur={blur("amount")}
              />
            </Field>
            {dateField("from", "Effective from")}
          </div>
        </>
      )}

      {tab === "deadlines" && (
        <>
          <Field label="Deadline name" error={error("service")}>
            <input
              className={`ua-input${error("service") ? " bad" : ""}`}
              placeholder="Assignment 1 submission"
              value={v.service}
              onChange={set("service")}
              onBlur={blur("service")}
            />
          </Field>
          <div className="ua-grid2">
            <Field label="Semester" error={error("semester")}>
              <input
                className={`ua-input${error("semester") ? " bad" : ""}`}
                placeholder="Autumn 2026"
                value={v.semester}
                onChange={set("semester")}
                onBlur={blur("semester")}
              />
            </Field>
            {dateField("date", "Date")}
          </div>
        </>
      )}

      {tab === "departments" && (
        <>
          <div className="ua-grid2">
            <Field label="Name in English" error={error("en")}>
              <input
                className={`ua-input${error("en") ? " bad" : ""}`}
                placeholder="Regional Campus Sukkur"
                value={v.en}
                onChange={set("en")}
                onBlur={blur("en")}
              />
            </Field>
            <Field label="Name in Urdu">
              <input
                className="ua-input ur"
                placeholder="علاقائی کیمپس سکھر"
                value={v.ur}
                onChange={set("ur")}
              />
            </Field>
          </div>
          <div className="ua-grid2">
            <Field label="Phone" error={error("phone")}>
              <input
                className={`ua-input ua-num${error("phone") ? " bad" : ""}`}
                placeholder="071-9310220"
                value={v.phone}
                onChange={set("phone")}
                onBlur={blur("phone")}
              />
            </Field>
            <Field label="Email" error={error("email")}>
              <input
                className={`ua-input${error("email") ? " bad" : ""}`}
                placeholder="skr@uni.edu.pk"
                value={v.email}
                onChange={set("email")}
                onBlur={blur("email")}
              />
            </Field>
          </div>
          <div className="ua-grid2">
            <Field label="Campus or address">
              <input
                className="ua-input"
                placeholder="Airport Road"
                value={v.campus}
                onChange={set("campus")}
              />
            </Field>
            <Field label="Office hours">
              <input className="ua-input ua-num" value={v.hours} onChange={set("hours")} />
            </Field>
          </div>
        </>
      )}

      {tab === "services" && (
        <>
          <div className="ua-grid2">
            <Field label="Name in English" error={error("en")}>
              <input
                className={`ua-input${error("en") ? " bad" : ""}`}
                placeholder="Degree Application"
                value={v.en}
                onChange={set("en")}
                onBlur={blur("en")}
              />
            </Field>
            <Field label="Name in Urdu" error={error("ur")}>
              <input
                className={`ua-input ur${error("ur") ? " bad" : ""}`}
                placeholder="ڈگری کی درخواست"
                value={v.ur}
                onChange={set("ur")}
                onBlur={blur("ur")}
              />
            </Field>
          </div>

          <Field label="Category" error={error("cat")}>
            <select
              className={`ua-select${error("cat") ? " bad" : ""}`}
              value={v.cat}
              onChange={set("cat")}
              onBlur={blur("cat")}
            >
              <option value="">Select a category</option>
              <option>Admissions</option>
              <option>Finance</option>
              <option>Examinations</option>
              <option>Academics</option>
              <option>Certification</option>
              <option>Records</option>
            </select>
          </Field>

          <Field
            label="Document checklist"
            hint="read out verbatim by get_document_checklist()"
          >
            <ChecklistEditor
              items={v.checklist}
              onChange={(items) => setValue("checklist", items)}
            />
          </Field>

          <div className="ua-grid2">
            <Field label="Procedure in English">
              <textarea
                className="ua-textarea"
                placeholder="How the student completes this, in plain language."
                value={v.procedure_en}
                onChange={set("procedure_en")}
              />
            </Field>
            <Field label="Procedure in Urdu">
              <textarea
                className="ua-textarea ur"
                placeholder="طالبعلم یہ کام کیسے مکمل کرے"
                value={v.procedure_ur}
                onChange={set("procedure_ur")}
              />
            </Field>
          </div>
        </>
      )}

      <Field label="Source citation" error={error("src")}>
        <input
          className={`ua-input${error("src") ? " bad" : ""}`}
          placeholder="Prospectus 2026-27 §2.1"
          value={v.src}
          onChange={set("src")}
          onBlur={blur("src")}
        />
      </Field>

      {record && changes.length > 0 && (
        <div>
          <div className="ua-label" style={{ marginBottom: 4 }}>
            What changes for students
          </div>
          <div style={{ border: "1px solid var(--line)", borderRadius: 10, padding: "8px 12px" }}>
            {changes.map((c) => (
              <DiffRow key={c.field} field={c.field} from={c.from} to={c.to} />
            ))}
          </div>
          <div style={{ marginTop: 9 }}>
            <Note tone="brass" icon={ShieldCheck}>
              Students asked about this roughly {nfmt(TABLE_IMPACT[tab](record))} times in the last
              90 days. Saving stamps the record with today&apos;s date and your name, and writes the
              change to the audit log.
            </Note>
          </div>
        </div>
      )}

      {!record && (
        <Note tone="brass" icon={ShieldCheck}>
          Saving stamps this record with today&apos;s date and your name. Students will see “last
          checked {fmtDate(ISO_TODAY)}” beside any answer that uses it.
        </Note>
      )}
    </Modal>
  );
}
