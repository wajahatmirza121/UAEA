import { useState } from "react";
import { Plus, Database, X, User, Bot } from "lucide-react";
import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";
import Field from "@/components/ui/Field";
import ReadOnlyNotice from "@/components/ui/ReadOnlyNotice";
import { fmtDate } from "@/lib/format";

/**
 * Right pane: why the assistant stopped, what it said instead, and the two
 * ways to close the gap — write an answer, or fix the record that was missing
 * a field. The second is usually the right one.
 */
export default function QueueDetail({ item, mayWrite, role, onPublish, onDismiss, onFixRecord }) {
  const [drafting, setDrafting] = useState(false);
  const [draft, setDraft] = useState("");
  const [saving, setSaving] = useState(false);

  const publish = () => {
    setSaving(true);
    setTimeout(() => {
      onPublish(item.id);
      setSaving(false);
      setDrafting(false);
      setDraft("");
    }, 800);
  };

  return (
    <div className="ua-card" style={{ alignSelf: "start" }}>
      <div className="ua-card-h">
        <div>
          <h3>Why this was flagged</h3>
          <p>
            {item.reason} · {item.channel === "whatsapp" ? "WhatsApp" : "Web chat"} · last asked{" "}
            {fmtDate(item.last)}
          </p>
        </div>
        <Badge tone={item.intent ? "violet" : "grey"}>{item.intent || "no intent match"}</Badge>
      </div>

      {!mayWrite && <ReadOnlyNotice role={role} />}

      <div style={{ padding: 17, display: "grid", gap: 13 }}>
        <div style={{ display: "flex", gap: 10 }}>
          <span className="ua-icontile" style={{ width: 26, height: 26, flex: "0 0 26px" }}>
            <User size={13} color="var(--t2)" />
          </span>
          <div
            className={`ua-bubble u${item.script === "urdu" ? " ur" : ""}`}
            style={{ marginLeft: 0, maxWidth: "100%" }}
          >
            {item.text}
          </div>
        </div>

        <div style={{ display: "flex", gap: 10 }}>
          <span
            className="ua-icontile"
            style={{
              width: 26,
              height: 26,
              flex: "0 0 26px",
              background: "var(--brass-soft)",
              borderColor: "var(--brass-line)",
            }}
          >
            <Bot size={13} color="var(--brass)" />
          </span>
          <div className="ua-bubble b" style={{ maxWidth: "100%" }}>
            {item.answer}{" "}
            <span style={{ color: "var(--t3)" }}>
              Would you like me to connect you to the department?
            </span>
          </div>
        </div>

        {!mayWrite ? null : drafting ? (
          <>
            <Field label="Answer students will see" hint={`${draft.length}/600`}>
              <textarea
                className="ua-textarea"
                maxLength={600}
                autoFocus
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                placeholder="Write the answer in plain Urdu or Roman Urdu. Quote the fee, date or checklist exactly as it appears in the source."
              />
            </Field>
            <Field label="Source citation">
              <input
                className="ua-input"
                placeholder="Fee Circular A-26 §3.2"
                defaultValue={item.intent === "fee_tariff" ? "Fee Circular A-26 §3.2" : ""}
              />
            </Field>
            <div style={{ display: "flex", gap: 9, justifyContent: "flex-end" }}>
              <Button variant="ghost" onClick={() => setDrafting(false)}>
                Cancel
              </Button>
              <Button
                variant="primary"
                loading={saving}
                disabled={draft.trim().length < 12}
                onClick={publish}
              >
                {saving ? "Publishing" : "Publish answer"}
              </Button>
            </div>
          </>
        ) : (
          <div style={{ display: "flex", gap: 9, flexWrap: "wrap" }}>
            <Button variant="primary" icon={Plus} onClick={() => setDrafting(true)}>
              Write an answer
            </Button>
            <Button icon={Database} onClick={onFixRecord}>
              Fix the record
            </Button>
            <Button variant="ghost" icon={X} onClick={() => onDismiss(item.id)}>
              Dismiss
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
