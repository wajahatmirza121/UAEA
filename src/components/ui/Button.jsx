import { Loader2 } from "lucide-react";

/**
 * Button with a built-in loading state.
 * While `loading` is true the icon is swapped for a spinner and the button
 * disables itself, so callers never have to manage both.
 */
export default function Button({
  children,
  variant = "",
  size = "",
  loading = false,
  icon: Icon,
  disabled,
  className = "",
  ...rest
}) {
  return (
    <button
      className={`ua-btn ${variant} ${size} ${className}`.trim()}
      disabled={loading || disabled}
      {...rest}
    >
      {loading ? <Loader2 size={14} className="ua-spin" /> : Icon ? <Icon size={14} /> : null}
      {children}
    </button>
  );
}
