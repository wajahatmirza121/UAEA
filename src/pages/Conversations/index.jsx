import { useState } from "react";
import { ThumbsUp, ThumbsDown } from "lucide-react";
import Transcript, { OutcomeBadge } from "./Transcript";
import { CONVERSATIONS } from "@/mocks";

const CHANNELS = [
  ["all", "All"],
  ["whatsapp", "WhatsApp"],
  ["web", "Web chat"],
];

export default function Conversations() {
  const [channel, setChannel] = useState("all");
  const [selectedId, setSelectedId] = useState(CONVERSATIONS[0].id);

  const shown = CONVERSATIONS.filter((c) => channel === "all" || c.channel === channel);
  const current = shown.find((c) => c.id === selectedId) || shown[0];

  return (
    <div className="ua-page">
      <div className="ua-head">
        <div>
          <h1 className="ua-h1">Conversations</h1>
          <p className="ua-sub">
            Every answer shows the tool call behind it. If a number appears without one, the guardrail
            layer should have caught it.
          </p>
        </div>
        <div className="ua-tabs">
          {CHANNELS.map(([key, label]) => (
            <button
              key={key}
              className={`ua-tab${channel === key ? " on" : ""}`}
              onClick={() => setChannel(key)}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      <div className="ua-split">
        <div className="ua-card" style={{ alignSelf: "start", overflow: "hidden" }}>
          <div className="ua-card-h">
            <div>
              <h3>Recent</h3>
              <p className="ua-num">{shown.length} conversations</p>
            </div>
          </div>

          <div className="ua-list">
            {shown.map((c) => (
              <button
                key={c.id}
                className={`ua-listitem${current?.id === c.id ? " on" : ""}`}
                onClick={() => setSelectedId(c.id)}
              >
                <span style={{ flex: 1, minWidth: 0 }}>
                  <span style={{ display: "flex", alignItems: "center", gap: 7, marginBottom: 4 }}>
                    <span className="ua-num" style={{ fontSize: 12.5, fontWeight: 500 }}>
                      {c.id}
                    </span>
                    <OutcomeBadge outcome={c.outcome} />
                  </span>
                  <span
                    className="ua-num"
                    style={{ fontSize: 11.5, color: "var(--t3)", display: "block" }}
                  >
                    {c.lang} · {c.turns} turns · {c.started}
                  </span>
                </span>

                {c.feedback === "up" && <ThumbsUp size={13} color="var(--jade)" />}
                {c.feedback === "down" && <ThumbsDown size={13} color="var(--rose)" />}
              </button>
            ))}
          </div>
        </div>

        {current && <Transcript conversation={current} />}
      </div>
    </div>
  );
}
