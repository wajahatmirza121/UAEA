import Badge from "@/components/ui/Badge";

/** Left pane: gaps students actually walked into, most recent first. */
export default function QueueList({ items, selectedId, onSelect }) {
  return (
    <div
      className="ua-card"
      style={{ overflow: "hidden", alignSelf: "start", maxHeight: 640, display: "flex", flexDirection: "column" }}
    >
      <div className="ua-card-h">
        <div>
          <h3>Unanswered</h3>
          <p className="ua-num">{items.length} open</p>
        </div>
      </div>

      <div className="ua-list" style={{ overflowY: "auto" }}>
        {items.map((item) => (
          <button
            key={item.id}
            className={`ua-listitem${selectedId === item.id ? " on" : ""}`}
            onClick={() => onSelect(item.id)}
          >
            <span style={{ flex: 1, minWidth: 0 }}>
              <span
                className={item.script === "urdu" ? "ur" : ""}
                style={{ fontSize: 12.8, display: "block", lineHeight: 1.55, marginBottom: 5 }}
              >
                {item.text}
              </span>
              <span style={{ display: "flex", gap: 6, alignItems: "center", flexWrap: "wrap" }}>
                <Badge tone={item.conf < 0.5 ? "rose" : item.conf < 0.7 ? "amber" : "grey"}>
                  <span className="ua-num">{Math.round(item.conf * 100)}% sure</span>
                </Badge>
                <span className="ua-num" style={{ fontSize: 11, color: "var(--t3)" }}>
                  asked {item.count}×
                </span>
              </span>
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}
