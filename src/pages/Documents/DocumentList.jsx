import { FileText, Check, Loader2, AlertTriangle } from "lucide-react";
import Badge from "@/components/ui/Badge";
import { fmtDate, nfmt } from "@/lib/format";

function StatusBadge({ status }) {
  if (status === "indexed")
    return (
      <Badge tone="jade">
        <Check size={11} />
        Indexed
      </Badge>
    );
  if (status === "processing")
    return (
      <Badge tone="sky">
        <Loader2 size={11} className="ua-spin" />
        Processing
      </Badge>
    );
  if (status === "superseded") return <Badge tone="grey">Superseded</Badge>;
  return (
    <Badge tone="rose">
      <AlertTriangle size={11} />
      Failed
    </Badge>
  );
}

/**
 * The indexed library.
 *
 * Superseded is a first-class state rather than a deletion: §5.3 calls stale
 * and current answers coexisting a real failure mode, so an old circular is
 * retired visibly instead of vanishing.
 */
export default function DocumentList({ documents }) {
  const liveChunks = documents
    .filter((d) => d.status === "indexed")
    .reduce((s, d) => s + d.chunks, 0);

  return (
    <div className="ua-card">
      <div className="ua-card-h">
        <div>
          <h3>Indexed library</h3>
          <p className="ua-num">{nfmt(liveChunks)} chunks live</p>
        </div>
      </div>

      <div className="ua-list">
        {documents.map((d) => (
          <div key={d.id} className="ua-listitem" style={{ alignItems: "center" }}>
            <span className="ua-icontile" style={{ width: 32, height: 32, flex: "0 0 32px" }}>
              <FileText size={14} color="var(--t2)" />
            </span>

            <span style={{ flex: 1, minWidth: 0 }}>
              <span style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                <span
                  className={d.lang === "Urdu" ? "ur" : ""}
                  style={{ fontSize: 13, fontWeight: 500 }}
                >
                  {d.title}
                </span>
                <Badge tone="grey">{d.version}</Badge>
              </span>

              <span
                className="ua-num"
                style={{ fontSize: 11.5, color: "var(--t3)", display: "block", marginTop: 3 }}
              >
                {d.pages} pages · {d.chunks ? `${nfmt(d.chunks)} chunks` : "not indexed"} · added{" "}
                {fmtDate(d.uploaded)} by {d.by}
              </span>

              {d.status === "processing" && (
                <span style={{ display: "block", marginTop: 7 }}>
                  <span className="ua-progress">
                    <i style={{ width: `${d.progress}%` }} />
                  </span>
                </span>
              )}

              {d.error && (
                <span
                  style={{ fontSize: 11.5, color: "var(--rose)", display: "block", marginTop: 5 }}
                >
                  {d.error} — re-upload a text PDF or run OCR first.
                </span>
              )}
            </span>

            <StatusBadge status={d.status} />
          </div>
        ))}
      </div>
    </div>
  );
}
