/**
 * One changed field, old value struck through beside the new one.
 * Used in the save preview and in the audit log so a change reads the same
 * way before and after it happens.
 */
export default function DiffRow({ field, from, to }) {
  return (
    <div className="ua-diff">
      <span className="fld">{field}</span>
      <span className="old">{from}</span>
      <span className="new">{to}</span>
    </div>
  );
}
