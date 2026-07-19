import { useEffect, useRef, useCallback } from "react";
import { useStore } from "./store";
import type { HUMModel } from "./types";

// Pulls /api/hum once, then subscribes to /api/stream (SSE) for live model pushes.
export function useHUMStream() {
  const setModel = useStore((s) => s.setModel);
  const setError = useStore((s) => s.setError);
  const esRef = useRef<EventSource | null>(null);

  const fetchOnce = useCallback(async () => {
    try {
      const r = await fetch("/api/hum");
      if (!r.ok) throw new Error(`/api/hum ${r.status}`);
      const m = (await r.json()) as HUMModel;
      setModel(m);
    } catch (e) {
      setError(String(e));
    }
  }, [setModel, setError]);

  useEffect(() => {
    let closed = false;
    fetchOnce();
    const es = new EventSource("/api/stream");
    esRef.current = es;
    es.onmessage = (ev) => {
      try {
        const data = JSON.parse(ev.data);
        if (data.type === "model") setModel(data.model as HUMModel);
      } catch {
        /* ignore malformed frame */
      }
    };
    es.onerror = () => {
      if (!closed) setError("SSE connection lost; retrying…");
    };
    return () => {
      closed = true;
      es.close();
    };
  }, [fetchOnce, setModel, setError]);

  const pull = useCallback(async () => {
    const s = useStore.getState();
    s.setPulling(true);
    try {
      const r = await fetch("/api/pull", { method: "POST" });
      const j = await r.json();
      if (!j.ok) s.setError(j.message || "pull failed");
    } catch (e) {
      s.setError(String(e));
    } finally {
      s.setPulling(false);
    }
  }, []);

  return { pull };
}
