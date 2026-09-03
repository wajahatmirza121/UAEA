import { Bot, User, ThumbsUp, ThumbsDown } from "lucide-react";
import RoutingCard from "./RoutingCard";
import SourceChip from "./SourceChip";
import ToolTrace from "./ToolTrace";
import EscalationCard from "./EscalationCard";

/** One turn. Student messages are plain; assistant turns carry their evidence. */
export default function MessageBubble({ message, onFeedback, onSuggest }) {
  const isMe = message.role === "user";
  const rtl = message.lang === "ur";

  return (
    <div className={`st-msg ${isMe ? "me" : "bot"}`}>
      <span className={`st-avatar${isMe ? "" : " bot"}`}>
        {isMe ? <User size={15} color="var(--t2)" /> : <Bot size={15} color="var(--brass)" />}
      </span>

      <div className="st-body">
        {!isMe && message.classification && <RoutingCard classification={message.classification} />}

        <div className={`st-said${rtl ? " ur" : ""}`}>
          {message.lines.map((line, i) =>
            typeof line === "string" ? (
              line ? <p key={i} style={{ margin: i ? "9px 0 0" : 0 }}>{line}</p> : null
            ) : (
              <ul key={i}>
                {line.list.map((item, j) => (
                  <li key={j}>{item}</li>
                ))}
              </ul>
            )
          )}

          {message.options && (
            <div className="st-chips" style={{ justifyContent: "flex-start", marginTop: 14 }}>
              {message.options.map((o) => (
                <button key={o} className="st-chip" onClick={() => onSuggest(o)}>
                  {o}
                </button>
              ))}
            </div>
          )}
        </div>

        {!isMe && (
          <>
            <SourceChip source={message.source} verified={message.verified} trust={message.trust} />
            <ToolTrace toolCalls={message.toolCalls} />
            {!message.resolved && (
              <EscalationCard department={message.classification?.department} reason={message.reason} />
            )}

            {message.source && (
              <div style={{ display: "flex", gap: 4, marginTop: 9, alignItems: "center" }}>
                <span style={{ fontSize: 11.5, color: "var(--t3)", marginRight: 4 }}>
                  Was this right?
                </span>
                <button
                  className="ua-mini"
                  onClick={() => onFeedback(message.id, "up")}
                  aria-label="Helpful"
                  style={{ color: message.feedback === "up" ? "var(--jade)" : undefined }}
                >
                  <ThumbsUp size={13} />
                </button>
                <button
                  className="ua-mini"
                  onClick={() => onFeedback(message.id, "down")}
                  aria-label="Not helpful"
                  style={{ color: message.feedback === "down" ? "var(--rose)" : undefined }}
                >
                  <ThumbsDown size={13} />
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
