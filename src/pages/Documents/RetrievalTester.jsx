import { useState } from "react";
import { Send } from "lucide-react";
import Button from "@/components/ui/Button";
import Badge from "@/components/ui/Badge";
import Skeleton from "@/components/ui/Skeleton";
import { RETRIEVAL_SAMPLE } from "@/mocks";
import { isUrduText } from "@/lib/format";

/**
 * Ask what a student would ask and see which chunks come back.
 *
 * Worth running against every new circular: §5.2 warns that a model being
 * fluent in Roman Urdu chat says nothing about whether retrieval finds the
 * right chunk for a Roman Urdu query.
 */
export default function RetrievalTester() {
  const [query, setQuery] = useState("BS CS ki semester fees kitni hai");
  const [testing, setTesting] = useState(false);
  const [hits, setHits] = useState(null);

  // ↯ API SEAM — POST /v1/admin/retrieval/test
  const run = () => {
    setTesting(true);
    setHits(null);
    setTimeout(() => {
      setHits(RETRIEVAL_SAMPLE);
      setTesting(false);
    }, 900);
  };

  return (
    <div className="ua-card" style={{ alignSelf: "start" }}>
      <div className="ua-card-h">
        <div>
          <h3>Test retrieval</h3>
          <p>Ask what a student would ask and see which chunks come back</p>
        </div>
      </div>

      <div style={{ padding: 15, display: "grid", gap: 11 }}>
        <div style={{ display: "flex", gap: 8 }}>
          <input
            className="ua-input"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && run()}
            placeholder="Type a query in Urdu or Roman Urdu"
          />
          <Button variant="primary" onClick={run} loading={testing} icon={Send}>
            Run
          </Button>
        </div>

        {testing && <Skeleton height={62} rows={3} />}

        {hits &&
          hits.map((h, i) => (
            <div
              key={i}
              style={{
                padding: "11px 13px",
                borderRadius: 11,
                border: "1px solid var(--line)",
                background: "var(--panel-2)",
              }}
            >
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  gap: 10,
                  marginBottom: 6,
                  alignItems: "center",
                }}
              >
                <span style={{ fontSize: 11.5, color: "var(--t2)" }}>
                  {h.doc} · {h.section}
                </span>
                <Badge tone={h.score > 0.8 ? "jade" : h.score > 0.65 ? "amber" : "grey"}>
                  <span className="ua-num">{h.score.toFixed(2)}</span>
                </Badge>
              </div>
              <div
                className={isUrduText(h.text) ? "ur" : ""}
                style={{ fontSize: 12.5, lineHeight: 1.65 }}
              >
                {h.text}
              </div>
            </div>
          ))}

        {!hits && !testing && (
          <p style={{ fontSize: 12.5, color: "var(--t3)", lineHeight: 1.6, margin: "4px 2px" }}>
            Nothing tested yet. Retrieval quality in Roman Urdu is worth checking every time a new
            document lands — fluency in chat is not the same as retrieval accuracy.
          </p>
        )}
      </div>
    </div>
  );
}
