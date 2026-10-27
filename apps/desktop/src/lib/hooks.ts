import { useEffect, useState } from "react";
import { getBackend, type Backend } from "./backend";
import { useApp } from "./store";
import type { AttemptRecord } from "./types";

/** Load async data; reloads when deps or the global dataVersion change. */
export function useData<T>(fn: (be: Backend) => Promise<T>, deps: unknown[] = []) {
  const v = useApp((s) => s.dataVersion);
  const [state, setState] = useState<{ data?: T; error?: unknown; loading: boolean }>({ loading: true });
  useEffect(() => {
    let live = true;
    setState((s) => ({ ...s, loading: true }));
    getBackend().then(fn).then((data) => live && setState({ data, loading: false }), (error) => live && setState({ error, loading: false }));
    return () => { live = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [v, ...deps]);
  return state;
}

export const useAttempts = () => useData((be) => be.db<AttemptRecord[]>({ op: "list_attempts" }));

export function randomSeed(): number {
  const a = new Uint32Array(1);
  crypto.getRandomValues(a);
  return a[0] % 1_000_000_000;
}
