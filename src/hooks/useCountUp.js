import { useState, useEffect } from "react";

/**
 * Eases a number up to its target on mount.
 *
 * Used once, on the dashboard metric tiles. The whole page has exactly one
 * orchestrated entrance; everything else moves only in response to a click.
 */
export function useCountUp(target, run, ms = 850) {
  const [v, setV] = useState(0);

  useEffect(() => {
    if (!run) {
      setV(target);
      return;
    }
    let raf;
    let start;
    const step = (t) => {
      if (!start) start = t;
      const p = Math.min((t - start) / ms, 1);
      setV(target * (1 - Math.pow(1 - p, 3))); // ease-out cubic
      if (p < 1) raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [target, run, ms]);

  return v;
}
