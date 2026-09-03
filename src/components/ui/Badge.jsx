/**
 * Small status pill.
 * Tone maps to the semantic colour tokens: jade only ever means verified.
 */
export default function Badge({ tone = "grey", children, ...rest }) {
  return (
    <span className={`ua-badge ${tone}`} {...rest}>
      {children}
    </span>
  );
}
