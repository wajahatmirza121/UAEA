import { useState, useRef, useEffect, useCallback } from "react";
import { useLocation } from "react-router-dom";
import MessageBubble from "./MessageBubble";
import Composer from "./Composer";
import ChatSidebar from "./ChatSidebar";
import { QUICK_ASKS } from "@/mocks/routing";
import { classify, detectLanguage, CONFIDENCE_FLOOR } from "@/lib/classify";
import { answer, trustLine, followUps } from "@/lib/assistant";
import { chatMessage } from "@/lib/api";
import { useApp } from "@/context/AppContext";

let seq = 0;
const nextId = () => `m${++seq}`;
const newSessionId = () =>
  `web-${(globalThis.crypto?.randomUUID?.() || `${Date.now()}-${Math.random().toString(36).slice(2)}`)}`;

/** Turn a POST /v1/chat/message response into a thread message. */
function fromBackend(data, localClassification, lang) {
  const src = (data.sources || [])[0];
  const isOtpTurn = data.engine === "otp" || !!data.otp;
  let classification = null;
  if (!isOtpTurn) {
    if (localClassification && localClassification.confidence >= CONFIDENCE_FLOOR) classification = localClassification;
    else if (data.intent_label && data.confidence >= CONFIDENCE_FLOOR)
      classification = { label: data.intent_label, confidence: data.confidence };
  }
  const resolved = data.resolved !== false;
  return {
    id: nextId(),
    role: "bot",
    lang: data.language || lang,
    classification,
    markdown: data.reply,
    lines: [],
    toolCalls: data.tool_calls || [],
    source: src ? [src.source, src.section].filter(Boolean).join(" ") : null,
    verified: null,
    trust: null,
    resolved,
    otp: data.otp || null,
    engine: data.engine,
    model: data.model,
    escalated: data.escalated,
    reason: resolved ? null : "I could not find this in the university records.",
    followUps: resolved && !data.otp && !isOtpTurn ? followUps(data.intent, data.language || lang) : null,
  };
}

const GREETING = {
  en: "Assalam o alaikum. Ask me about fees, deadlines, when classes start, timetables, hostels, scholarships or which office handles what. For your own result, fee status or attendance, send your roll number — I will verify it with a code on WhatsApp first.",
  roman: "Assalam o alaikum. Fees, tareekhon, classes kab shuru hongi, timetable, hostel, scholarship ya kisi bhi shobe ke baare mein poochein. Apna result, fee status ya attendance dekhne ke liye roll number likhein — pehle WhatsApp par code se verify hoga.",
  ur: "السلام علیکم۔ فیس، تاریخوں، کلاسز کے آغاز، ٹائم ٹیبل، ہاسٹل یا وظائف کے بارے میں پوچھیں۔ اپنا رزلٹ، فیس یا حاضری دیکھنے کے لیے رول نمبر لکھیں — پہلے واٹس ایپ پر کوڈ سے تصدیق ہو گی۔",
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
 * Every message goes to the backend (POST /v1/chat/message), which uses
 * Groq + the university database and asks for a WhatsApp OTP before showing
 * any student's private records. If the backend is unreachable, the built-in
 * demo engine (mock data) answers instead, so the page never dead-ends.
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
  // One backend conversation per chat; "Start over" begins a new one.
  const sessionRef = useRef(newSessionId());

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

  /**
   * The built-in demo engine (mock data, no backend). Used only when the
   * backend cannot be reached, so the page still works on its own.
   */
  const localReply = (text, lang, classification) => {
    const pending = slotRef.current;
    if (pending && (!classification || classification.confidence < CONFIDENCE_FLOOR)) {
      const r = answer({ text, classification: pending.classification, lang: pending.lang, store });
      slotRef.current = r.needsSlot ? { ...pending, options: r.options } : null;
      return {
        id: nextId(), role: "bot", lang: pending.lang, classification: pending.classification,
        lines: r.body, toolCalls: r.toolCalls, source: r.source, verified: r.verified,
        trust: trustLine(r.verified, pending.lang), resolved: r.resolved, options: r.options, engine: "local",
        followUps: r.resolved && !r.needsSlot ? followUps(pending.classification.intent, pending.lang) : null,
      };
    }
    if (!classification || classification.confidence < CONFIDENCE_FLOOR) {
      const fallbackDept = classification?.department || store.departments.find((d) => d.id === "dep-01");
      return {
        id: nextId(), role: "bot", lang, engine: "local",
        classification: classification || { label: "Not recognised", confidence: 0, department: fallbackDept },
        lines: [
          lang === "ur"
            ? "معذرت، میں یقین سے نہیں کہہ سکتا کہ یہ سوال کس شعبے کا ہے، اس لیے اندازہ نہیں لگاؤں گا۔"
            : lang === "roman"
            ? "Maazrat, main yaqeen se nahi keh sakta ke ye sawal kis shobe ka hai, is liye andaaza nahi lagaunga."
            : "I am not confident which department this belongs to, so I would rather not guess.",
        ],
        toolCalls: [], resolved: false, reason: "Nothing in my records matched this closely enough.",
      };
    }
    const r = answer({ text, classification, lang, store });
    slotRef.current = r.needsSlot ? { slot: r.needsSlot, classification, lang, options: r.options } : null;
    return {
      id: nextId(), role: "bot", lang, classification, lines: r.body, toolCalls: r.toolCalls,
      source: r.source, verified: r.verified, trust: trustLine(r.verified, lang), resolved: r.resolved,
      options: r.options, engine: "local",
      followUps: r.resolved && !r.needsSlot ? followUps(classification.intent, lang) : null,
    };
  };

  const send = useCallback(
    async (raw) => {
      const text = String(raw ?? "").trim();
      if (!text) return;

      const lang = detectLanguage(text);
      // Codes are typed as messages; mask them in the thread like a password field.
      const shown = /^\s*\d{3}[\s-]?\d{3}\s*$/.test(text) ? "••••••" : text;
      setMessages((prev) => [...prev, { id: nextId(), role: "user", lang, lines: [shown], resolved: true }]);
      setDraft("");
      setThinking(true);

      // Classified locally too, so the routing card and sidebar can show the
      // owning office straight away.
      const classification = classify(text, store.departments);

      let msg;
      try {
        const data = await chatMessage(sessionRef.current, text);
        msg = fromBackend(data, classification, lang);
        slotRef.current = null;
      } catch (err) {
        console.warn("[chat] backend unavailable, using built-in demo data:", err?.message);
        msg = localReply(text, lang, classification);
      }
      setMessages((prev) => [...prev, msg]);
      setThinking(false);
      if (msg.classification) setContext(msg.classification);
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [store]
  );

  const onFeedback = (id, value) =>
    setMessages((prev) => prev.map((m) => (m.id === id ? { ...m, feedback: value } : m)));

  const reset = () => {
    slotRef.current = null;
    sessionRef.current = newSessionId();
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
          {messages.map((m, i) => (
            <MessageBubble
              key={m.id}
              message={m}
              onFeedback={onFeedback}
              onSuggest={send}
              otpActive={!!m.otp && i === messages.length - 1 && !thinking}
            />
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

          {!thinking && suggestions && !last?.otp && (
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
