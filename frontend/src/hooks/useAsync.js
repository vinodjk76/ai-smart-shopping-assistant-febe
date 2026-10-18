import { useCallback, useEffect, useRef, useState } from "react";
import { errorMessage } from "../api/client";

/**
 * Run an async loader on mount / when deps change.
 * Returns { data, loading, error, reload }.
 */
export function useAsync(loader, deps = []) {
  const [state, setState] = useState({ data: null, loading: true, error: null });
  const counter = useRef(0);

  const run = useCallback(() => {
    const id = ++counter.current;
    setState((s) => ({ ...s, loading: true, error: null }));
    loader()
      .then((data) => {
        if (id === counter.current) setState({ data, loading: false, error: null });
      })
      .catch((err) => {
        if (id === counter.current)
          setState({ data: null, loading: false, error: errorMessage(err) });
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(() => {
    run();
    return () => {
      counter.current += 1; // ignore stale responses after unmount / dep change
    };
  }, [run]);

  return { ...state, reload: run };
}
