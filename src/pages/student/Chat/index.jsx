import { useState, useRef, useEffect, useCallback } from "react";
import { useLocation } from "react-router-dom";
import MessageBubble from "./MessageBubble";
import Composer from "./Composer";
import ChatSidebar from "./ChatSidebar";
import { QUICK_ASKS } from "@/mocks/routing";
import { classify, detectLanguage, CONFIDENCE_FLOOR } from "@/lib/classify";
import { answer, trustLine, followUps } from "@/lib/assistant";
import { useApp } from "@/context/AppContext";

let seq = 0;
const nextId = () => `m${++seq}`;

const GREETING = {
  en: "Assalam o alaikum. Ask me about fees, deadlines, documents or which office handles what. I will tell you where each answer came from.",
  roman: "Assalam o alaikum. Fees, tareekhon, dastavezaat ya kisi bhi shobe ke baare mein poochein. Har jawab ke saath uska source bhi bataunga.",
  ur: "السلام علیکم۔ فیس، تاریخوں، دستاویزات یا کسی بھی شعبے کے بارے میں پوچھیں۔ ہر جواب کے ساتھ اس کا ماخذ بھی بتاؤں گا۔",
};

/**
 * The student chat.
 *
 * Flow per message: classify → route → look up → answer → cite.
 * Classification happens before any answer is composed, and the result is
 * shown to the student, so a misrouted question is obvious immediately rather
 * than three replies later. An unanswered slot question is carried to the
 * next turn, so a bare programme or campus name completes it.
 *
 * ↯ API SEAM — POST /v1/chat/message replaces the classify/answer pair below.
 */
export default function Chat() {
  const { store, urdu } = useApp();
  const location = useLocation();

  const [messages, setMessages] = useState([]);
  const [draft, setDraft] = useState("");
  const [thinking, setThinking] = useState(false);
  const [context, setContext] = useState(null);
  // The question the assistant is still waiting on an answer to, if any:
  // { slot, classification, lang, options }. A ref, not state, because it is
  // read inside the send timeout where captured state would be stale.
  const slotRef = useRef(null);
  const bottomRef = useRef(null);

  const greetLang = urdu ? "ur" : "roman";

  // Seed the thread, and pick up a question handed over from the landing page.
  useEffect(() => {
    setMessages([
      {
        id: nextId(),
        role: "bot",
        lang: greetLang,
        lines: [GREETING[greetLang]],
        resolved: true,
      },
    ]);
    const handed = location.state?.question;
    if (handed) setTimeout(() => send(handed), 260);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, thinking]);

  const send = useCallback(
    (raw) => {
      const text = String(raw ?? "").trim();
      if (!text) return;

      const lang = detectLanguage(text);
      setMessages((prev) => [
        ...prev,
        { id: nextId(), role: "user", lang, lines: [text], resolved: true },
      ]);
      setDraft("");
      setThinking(true);

      // Latency is simulated so the classify → look up → answer sequence is
      // legible rather than appearing instantaneously.
      setTimeout(() => {
        const classification = classify(text, store.departments);

        // A bare slot answer ("BS Computer Science") matches no rule on its
        // own — it completes the pending question, so it belongs to that turn
        // and its language rather than to a fresh classification.
        const pending = slotRef.current;
        if (pending && (!classification || classification.confidence < CONFIDENCE_FLOOR)) {
          const slotResult = answer({
            text,
            classification: pending.classification,
            lang: pending.lang,
            store,
          });
          const slotTrust = trustLine(slotResult.verified, pending.lang);
          // Answered: clear the slot. Not answerable: answer() re-asks the
          // question with the same options, so the flow never dead-ends.
          slotRef.current = slotResult.needsSlot
            ? { ...pending, options: slotResult.options }
            : null;

          setMessages((prev) => [
            ...prev,
            {
              id: nextId(),
              role: "bot",
              lang: pending.lang,
              classification: pending.classification,
              lines: slotResult.body,
              toolCalls: slotResult.toolCalls,
              source: slotResult.source,
              verified: slotResult.verified,
              trust: slotTrust,
              resolved: slotResult.resolved,
              options: slotResult.options,
              followUps:
                slotResult.resolved && !slotResult.needsSlot
                  ? followUps(pending.classification.intent, pending.lang)
                  : null,
            },
          ]);
          setThinking(false);
          setContext(pending.classification);
          return;
        }

        // Nothing matched at all: hand over rather than improvise.
        if (!classification || classification.confidence < CONFIDENCE_FLOOR) {
          const fallbackDept =
            classification?.department || store.departments.find((d) => d.id === "dep-01");
          setMessages((prev) => [
            ...prev,
            {
              id: nextId(),
              role: "bot",
              lang,
              classification: classification || {
                label: "Not recognised",
                confidence: 0,
                department: fallbackDept,
              },
              lines: [
                lang === "ur"
                  ? "معذرت، میں یقین سے نہیں کہہ سکتا کہ یہ سوال کس شعبے کا ہے، اس لیے اندازہ نہیں لگاؤں گا۔"
                  : lang === "roman"
                  ? "Maazrat, main yaqeen se nahi keh sakta ke ye sawal kis shobe ka hai, is liye andaaza nahi lagaunga."
                  : "I am not confident which department this belongs to, so I would rather not guess.",
              ],
              toolCalls: [],
              resolved: false,
              reason: "Nothing in my records matched this closely enough.",
              classificationDepartment: fallbackDept,
            },
          ]);
          setThinking(false);
          setContext(classification);
          return;
        }

        const result = answer({ text, classification, lang, store });
        const trust = trustLine(result.verified, lang);

        // An answer the tools could not finish becomes state: the next
        // message that names a programme or campus completes this turn.
        slotRef.current = result.needsSlot
          ? { slot: result.needsSlot, classification, lang, options: result.options }
          : null;

        setMessages((prev) => [
          ...prev,
          {
            id: nextId(),
            role: "bot",
            lang,
            classification,
            lines: result.body,
            toolCalls: result.toolCalls,
            source: result.source,
            verified: result.verified,
            trust,
            resolved: result.resolved,
            options: result.options,
            followUps: result.resolved && !result.needsSlot ? followUps(classification.intent, lang) : null,
          },
        ]);
        setThinking(false);
        setContext(classification);
      }, 620);
    },
    [store]
  );

  const onFeedback = (id, value) =>
    setMessages((prev) => prev.map((m) => (m.id === id ? { ...m, feedback: value } : m)));

  const reset = () => {
    slotRef.current = null;
    setContext(null);
    setMessages([
      { id: nextId(), role: "bot", lang: greetLang, lines: [GREETING[greetLang]], resolved: true },
    ]);
  };

  const last = messages[messages.length - 1];
  const suggestions = last?.followUps || (messages.length <= 1 ? QUICK_ASKS.slice(0, 4).map((q) => q.text) : null);

  return (
    <div className="st-chat">
      <div className="st-thread">
        <div className="st-msgs">
          {messages.map((m) => (
            <MessageBubble key={m.id} message={m} onFeedback={onFeedback} onSuggest={send} />
          ))}

          {thinking && (
            <div className="st-msg bot">
              <span className="st-avatar bot" />
              <div className="st-body">
                <div className="st-said" style={{ padding: 0 }}>
                  <div className="st-typing">
                    <i />
                    <i />
                    <i />
                  </div>
                </div>
              </div>
            </div>
          )}

          {!thinking && suggestions && (
            <div className="st-chips" style={{ justifyContent: "flex-start", paddingLeft: 41 }}>
              {suggestions.map((s) => (
                <button
                  key={s}
                  className={`st-chip${/[\u0600-\u06FF]/.test(s) ? " ur" : ""}`}
                  onClick={() => send(s)}
                >
                  {s}
                </button>
              ))}
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        <Composer value={draft} onChange={setDraft} onSend={() => send(draft)} disabled={thinking} />
      </div>

      <ChatSidebar classification={context} onReset={reset} />
    </div>
  );
}
