/** Shimmer placeholder. Rows fade slightly down the stack so the list reads
 *  as loading rather than as a solid block. */
export default function Skeleton({ height = 40, rows = 1, gap = 9, style }) {
  if (rows === 1) return <div className="ua-skel" style={{ height, ...style }} />;

  return (
    <div style={{ display: "grid", gap }}>
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="ua-skel" style={{ height, opacity: 1 - i * 0.12 }} />
      ))}
    </div>
  );
}
