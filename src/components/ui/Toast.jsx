import { CheckCircle2, AlertTriangle } from "lucide-react";

/** Single toast. The stack itself lives in ToastContext. */
export default function Toast({ title, desc, tone = "jade" }) {
  const Icon = tone === "rose" ? AlertTriangle : CheckCircle2;
  return (
    <div className="ua-toast">
      <Icon size={15} color={`var(--${tone})`} style={{ flex: "0 0 15px", marginTop: 1 }} />
      <div>
        <b>{title}</b>
        <span>{desc}</span>
      </div>
    </div>
  );
}
