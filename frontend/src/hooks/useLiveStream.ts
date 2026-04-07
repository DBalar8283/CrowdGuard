import { useEffect, useRef, useState } from "react";

import type { AlertItem, StreamPayload } from "../types";

const FALLBACK_URL = "ws://127.0.0.1:8000/ws/live";

export type LiveAlert = AlertItem & { receivedAt: string };

export function useLiveStream() {
  const [payload, setPayload] = useState<StreamPayload | null>(null);
  const [status, setStatus] = useState<"connecting" | "live" | "offline">("connecting");
  const [alerts, setAlerts] = useState<LiveAlert[]>([]);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const ws = new WebSocket((import.meta as any).env?.VITE_WS_URL ?? FALLBACK_URL);
    wsRef.current = ws;

    ws.onopen = () => setStatus("live");
    ws.onerror = () => setStatus("offline");
    ws.onclose = () => setStatus("offline");

    ws.onmessage = (event: MessageEvent<string>) => {
      const next = JSON.parse(event.data) as StreamPayload;
      setPayload(next);
      if (next.alerts.length > 0) {
        const enriched = next.alerts.map((item) => ({ ...item, receivedAt: next.timestamp }));
        setAlerts((prev) => [...enriched, ...prev].slice(0, 200));
      }
    };

    return () => {
      ws.close();
      wsRef.current = null;
    };
  }, []);

  return { payload, status, alerts };
}
