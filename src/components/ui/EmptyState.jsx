/** Empty state. The body should say what to do next, not just what is absent. */
export default function EmptyState({ title, body, action }) {
  return (
    <div className="ua-empty">
      <h4>{title}</h4>
      {body && <p>{body}</p>}
      {action}
    </div>
  );
}
