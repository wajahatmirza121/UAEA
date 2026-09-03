import { ShieldCheck, Clock } from "lucide-react";
import Badge from "@/components/ui/Badge";
import Ladder from "@/components/ui/Ladder";

/**
 * Source citation and freshness under an answer.
 *
 * When the record is ageing the student is told outright. Quietly serving a
 * six-month-old fee as though it were current is the failure this whole
 * system is built to avoid.
 */
export default function SourceChip({ source, verified, trust }) {
  if (!source && !verified) return null;

  return (
    <>
      <div className="st-source">
        {source && (
          <Badge tone="grey">
            <ShieldCheck size={11} />
            {source}
          </Badge>
        )}
        {verified && <Ladder verified={verified} />}
        {trust && <span>{trust.text}</span>}
      </div>

      {trust?.stale && (
        <div className="ua-note amber" style={{ marginTop: 9 }}>
          <Clock size={15} color="var(--amber)" />
          <span>
            This record has not been checked recently. Please confirm with the department before you
            rely on it for a payment or a deadline.
          </span>
        </div>
      )}
    </>
  );
}
