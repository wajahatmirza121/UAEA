import Switch from "@/components/ui/Switch";
import ReadOnlyNotice from "@/components/ui/ReadOnlyNotice";

/** The rule set from §5.4, in the order of how much damage each prevents. */
export const RULES = [
  {
    key: "blockUngrounded",
    label: "Block numbers that no tool returned",
    desc: "Fees, dates and amounts must trace back to a successful lookup. This is the rule that keeps a wrong deadline from reaching a student.",
  },
  {
    key: "requireCitation",
    label: "Require a source citation on knowledge answers",
    desc: "Replies drawn from the prospectus name the document and section.",
  },
  {
    key: "blockPromises",
    label: "Block outcome promises",
    desc: "The assistant quotes published processing ranges rather than guaranteeing a completion date.",
  },
  {
    key: "blockAcademicDishonesty",
    label: "Decline assignment and exam writing requests",
    desc: "Students asking for work to be written for them are pointed to tutor support instead.",
  },
  {
    key: "blockUnauthenticated",
    label: "Refuse personal record lookups without verification",
    desc: "Until OTP auth lands in Phase 2, the assistant will not read out anything tied to an individual roll number.",
  },
  {
    key: "showVerifiedDate",
    label: "Show the verification date beside every fact",
    desc: "“Last checked 24 August 2026” appears with fees, deadlines and checklists.",
  },
];

export default function AnswerRules({ config, onChange, mayWrite, role }) {
  return (
    <div className="ua-card">
      <div className="ua-card-h">
        <div>
          <h3>Answer rules</h3>
          <p>Applied before any reply leaves the system</p>
        </div>
      </div>

      {!mayWrite && <ReadOnlyNotice role={role} />}

      <div style={{ padding: "4px 17px 14px" }}>
        {RULES.map((rule, i) => (
          <div key={rule.key}>
            <Switch
              on={config[rule.key]}
              onChange={(v) => onChange(rule.key, v)}
              label={rule.label}
              desc={rule.desc}
              disabled={!mayWrite}
            />
            {i < RULES.length - 1 && <div className="ua-hairline" />}
          </div>
        ))}
      </div>
    </div>
  );
}
