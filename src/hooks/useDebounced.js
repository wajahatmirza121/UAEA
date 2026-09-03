import { useState, useEffect } from "react";

/** Delays a fast-changing value. Used on every search box. */
export function useDebounced(value, ms = 220) {
  const [v, setV] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setV(value), ms);
    return () => clearTimeout(t);
  }, [value, ms]);
  return v;
}
