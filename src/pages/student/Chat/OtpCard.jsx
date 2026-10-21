import { useEffect, useRef, useState } from "react";
import { ShieldCheck, MessageCircle, RotateCw } from "lucide-react";

/**
 * Shown under a reply when the backend sent a WhatsApp verification code.
 *
 * Typing the code here simply sends it as a chat message — the backend checks
 * it before anything else, so typing it straight into the composer works too.
 */
export default function OtpCard({ otp, active, onSubmit }) {
  const [code, setCode] = useState("");
  const [left, setLeft] = useState(otp?.expires_in_seconds ?? 300);
  const [resendIn, setResendIn] = useState(30);
  const ref = useRef(null);

  useEffect(() => {
    if (active) ref.current?.focus();
  }, [active]);

  useEffect(() => {
    if (!active) return undefined;
    const t = setInterval(() => {
      setLeft((s) => Math.max(0, s - 1));
      setResendIn((s) => Math.max(0, s - 1));
    }, 1000);
    return () => clearInterval(t);
  }, [active]);

  if (!otp || otp.rate_limited) return null;

  const mm = String(Math.floor(left / 60)).padStart(1, "0");
  const ss = String(left % 60).padStart(2, "0");
  const ready = code.length === 6;

  const submit = (e) => {
    e?.preventDefault();
    if (ready && active) onSubmit(code);
  };

  return (
    <form className={`st-otp${active ? "" : " done"}`} onSubmit={submit}>
      <div className="st-otp-head">
        <MessageCircle size={15} color="var(--jade)" />
        <span>
          Code sent on WhatsApp to <b className="ua-num">{otp.masked_phone}</b>
          {otp.roll_number && <> for <b>{otp.roll_number}</b></>}
        </span>
      </div>

      {active ? (
        <>
          <div className="st-otp-row">
            <input
              ref={ref}
              className="st-otp-input ua-num"
              inputMode="numeric"
              autoComplete="one-time-code"
              maxLength={6}
              placeholder="••••••"
              value={code}
              onChange={(e) => setCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
              aria-label="6-digit verification code"
            />
            <button type="submit" className="ua-btn primary" disabled={!ready || left === 0}>
              <ShieldCheck size={14} />
              Verify
            </button>
          </div>
          <div className="st-otp-foot">
            <span className="ua-num">{left > 0 ? `Expires in ${mm}:${ss}` : "Code expired"}</span>
            <button
              type="button"
              className="st-otp-link"
              disabled={resendIn > 0 && left > 0}
              onClick={() => onSubmit("resend")}
            >
              <RotateCw size={12} />
              {resendIn > 0 && left > 0 ? `Resend in ${resendIn}s` : "Resend code"}
            </button>
          </div>
          {otp.dev_code && (
            <div className="st-otp-dev">
              Demo mode (no WhatsApp provider): code is <b className="ua-num">{otp.dev_code}</b>
            </div>
          )}
        </>
      ) : (
        <div className="st-otp-foot">
          <span>This request is no longer waiting for a code.</span>
        </div>
      )}
    </form>
  );
}
