import { useEffect, useMemo, useState } from "react";

import { AlertLogPanel, groupAlerts } from "./components/AlertLogPanel";
import { AnalyticsPanel } from "./components/AnalyticsPanel";
import { LiveFeedPanel } from "./components/LiveFeedPanel";
import { MiniMapPanel } from "./components/MiniMapPanel";
import { useLiveStream } from "./hooks/useLiveStream";

type TrendPoint = { time: string; density: number; velocity: number };
type SeverityState = "normal" | "caution" | "critical" | "offline";

function App() {
  const { payload, status, alerts } = useLiveStream();
  const [history, setHistory] = useState<TrendPoint[]>([]);
  const [acknowledged, setAcknowledged] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (!payload) return;

    const time = new Date(payload.timestamp).toLocaleTimeString();
    setHistory((prev) => {
      if (prev.length > 0 && prev[prev.length - 1].time === time) {
        return prev;
      }
      return [...prev.slice(-59), { time, density: payload.density_per_m2, velocity: payload.avg_velocity_mps }];
    });
  }, [payload]);

  const threads = useMemo(() => groupAlerts(alerts), [alerts]);

  const unackedThreads = useMemo(() => threads.filter((item) => !acknowledged.has(item.id)), [threads, acknowledged]);

  const severity = useMemo<SeverityState>(() => {
    if (status !== "live") return "offline";
    if ((payload?.fruin_level === "E" || payload?.fruin_level === "F") || unackedThreads.some((x) => x.severity === "critical")) {
      return "critical";
    }
    if (payload?.fruin_level === "D" || unackedThreads.length > 0) {
      return "caution";
    }
    return "normal";
  }, [status, payload?.fruin_level, unackedThreads]);

  const highlightPeople = useMemo(() => {
    const ids = new Set<string>();
    for (const thread of unackedThreads.slice(0, 4)) {
      if (thread.personId) ids.add(thread.personId);
    }
    return ids;
  }, [unackedThreads]);

  const onAcknowledge = (id: string) => {
    setAcknowledged((prev) => {
      const next = new Set(prev);
      next.add(id);
      return next;
    });
  };

  const severityLabel =
    severity === "critical" ? "CRITICAL" : severity === "caution" ? "CAUTION" : severity === "offline" ? "OFFLINE" : "NORMAL";

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <h1>CrowdGuard Operations Console</h1>
          <p>Real-time crowd monitoring with explainable incident triage</p>
        </div>
        <div className={`status-pill ${severity}`}>{severityLabel}</div>
      </header>

      <section className={`incident-bar ${severity}`} role="status" aria-live="polite">
        <div className="incident-title">Active Incidents</div>
        <div className="incident-items">
          {unackedThreads.length === 0 && <span className="muted">No unacknowledged incidents</span>}
          {unackedThreads.slice(0, 3).map((thread) => (
            <article key={thread.id} className={`incident-chip ${thread.severity}`}>
              <strong>{thread.eventType.toUpperCase()}</strong>
              <span>{thread.personId ?? thread.zoneId}</span>
              <span>x{thread.count}</span>
            </article>
          ))}
        </div>
      </section>

      <section className="kpis">
        <article>
          <h3>People</h3>
          <p>{payload?.people_count ?? 0}</p>
        </article>
        <article>
          <h3>Fruin LOS</h3>
          <p>{payload?.fruin_level ?? "-"}</p>
        </article>
        <article>
          <h3>Density</h3>
          <p>{(payload?.density_per_m2 ?? 0).toFixed(3)} /m2</p>
        </article>
        <article>
          <h3>Velocity</h3>
          <p>{(payload?.avg_velocity_mps ?? 0).toFixed(3)} m/s</p>
        </article>
      </section>

      <section className="ops-grid">
        <section className="ops-main">
          <LiveFeedPanel payload={payload} highlightPeople={highlightPeople} />
          <section className="ops-lower-grid">
            <MiniMapPanel payload={payload} />
            <AnalyticsPanel
              points={history}
              densityNow={payload?.density_per_m2 ?? 0}
              velocityNow={payload?.avg_velocity_mps ?? 0}
            />
          </section>
        </section>

        <AlertLogPanel threads={threads} acknowledged={acknowledged} onAcknowledge={onAcknowledge} />
      </section>
    </main>
  );
}

export default App;
