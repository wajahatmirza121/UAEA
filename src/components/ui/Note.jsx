/** Inline callout. Tone carries the meaning; the icon is passed by the caller. */
export default function Note({ tone = "brass", icon: Icon, children }) {
  return (
    <div className={`ua-note ${tone}`}>
      {Icon && <Icon size={15} color={`var(--${tone})`} />}
      <span>{children}</span>
    </div>
  );
}
