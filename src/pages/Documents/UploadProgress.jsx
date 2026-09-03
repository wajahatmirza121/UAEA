/** Ingestion stages, shown while a new source document is processed (§5.3). */
export const UPLOAD_STAGES = [
  "Uploading file",
  "Splitting into chunks",
  "Generating embeddings",
  "Writing to the index",
  "Ready",
];

export default function UploadProgress({ stage }) {
  return (
    <div className="ua-card" style={{ padding: 17, marginBottom: 14 }}>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12.5, marginBottom: 9 }}>
        <span>{UPLOAD_STAGES[stage]}</span>
        <span className="ua-num" style={{ color: "var(--t3)" }}>
          Step {stage + 1} of {UPLOAD_STAGES.length}
        </span>
      </div>
      <div className="ua-progress">
        <i style={{ width: `${((stage + 1) / UPLOAD_STAGES.length) * 100}%` }} />
      </div>
    </div>
  );
}
