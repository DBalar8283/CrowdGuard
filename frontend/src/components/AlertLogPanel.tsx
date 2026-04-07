import type { LiveAlert } from "../hooks/useLiveStream";

export interface AlertThread {
  id: string;
  severity: "info" | "warn" | "critical";
  eventType: string;
  zoneId: string;
  personId?: string;
  count: number;
  lastMessage: string;
  lastSeen: string;
  reasons: string[];
}

interface Props {
  threads: AlertThread[];
  acknowledged: Set<string>;
  onAcknowledge: (id: string) => void;
}

export function AlertLogPanel({ threads, acknowledged, onAcknowledge }: Props) {
  return (
    <section className="panel panel-alerts" aria-live="polite">
      <header className="panel-header">
        <h2>Incident Triage</h2>
        <div className="panel-meta">{threads.length} active threads</div>
      </header>

      <div className="alert-list">
        {threads.length === 0 && <p className="muted">No active incidents.</p>}
        {threads.map((thread) => {
          const isAcked = acknowledged.has(thread.id);
          return (
            <article key={thread.id} className={`alert-item ${thread.severity} ${isAcked ? "acked" : ""}`}>
              <div className="alert-row">
                <p className="alert-msg">{thread.lastMessage}</p>
                <span className="alert-count">x{thread.count}</span>
              </div>
              <p className="alert-meta">
                {thread.eventType} | {thread.zoneId} {thread.personId ? `| ${thread.personId}` : ""}
              </p>
              <p className="alert-reason">{thread.reasons.slice(0, 2).join(", ") || "reason unavailable"}</p>
              <div className="alert-controls">
                <span className="muted">Last seen {new Date(thread.lastSeen).toLocaleTimeString()}</span>
                <button
                  type="button"
                  className="ack-btn"
                  onClick={() => onAcknowledge(thread.id)}
                  aria-label={`Acknowledge ${thread.eventType} incident`}
                >
                  {isAcked ? "Acknowledged" : "Acknowledge"}
                </button>
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}

export function groupAlerts(alerts: LiveAlert[]): AlertThread[] {
  const map = new Map<string, AlertThread>();

  for (const alert of alerts) {
    const key = `${alert.event_type}:${alert.person_id ?? "zone"}:${alert.zone_id}`;
    const reasons = alert.reasons.map((r) => r.reason_code);
    const existing = map.get(key);

    if (!existing) {
      map.set(key, {
        id: key,
        severity: alert.severity,
        eventType: alert.event_type,
        zoneId: alert.zone_id,
        personId: alert.person_id,
        count: 1,
        lastMessage: alert.message,
        lastSeen: alert.receivedAt,
        reasons,
      });
      continue;
    }

    existing.count += 1;
    if (alert.severity === "critical") {
      existing.severity = "critical";
    }
    existing.lastMessage = alert.message;
    existing.lastSeen = alert.receivedAt;
    existing.reasons = Array.from(new Set([...existing.reasons, ...reasons]));
  }

  return [...map.values()].sort((a, b) => {
    if (a.severity !== b.severity) {
      return severityWeight(b.severity) - severityWeight(a.severity);
    }
    return new Date(b.lastSeen).getTime() - new Date(a.lastSeen).getTime();
  });
}

function severityWeight(level: AlertThread["severity"]) {
  if (level === "critical") return 3;
  if (level === "warn") return 2;
  return 1;
}
