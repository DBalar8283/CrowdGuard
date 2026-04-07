import type { StreamPayload } from "../types";

interface Props {
  payload: StreamPayload | null;
  highlightPeople: Set<string>;
}

export function LiveFeedPanel({ payload, highlightPeople }: Props) {
  const avgVelocity = payload?.avg_velocity_mps ?? 0;
  const frameW = payload?.frame_width ?? 1280;
  const frameH = payload?.frame_height ?? 720;
  const frameSrc = payload?.frame_jpeg ? `data:image/jpeg;base64,${payload.frame_jpeg}` : null;

  return (
    <section className="panel panel-feed">
      <header className="panel-header">
        <h2>Live Feed</h2>
        <div className="panel-meta">Zone risk view</div>
      </header>
      <div className={`feed-canvas ${avgVelocity < 0.04 ? "risk-elevated" : ""}`}>
        <div className="zone-ribbon">Exit Zone A</div>
        {frameSrc ? (
          <img src={frameSrc} alt="Live camera feed" className="feed-image" />
        ) : (
          <div className="feed-fallback">Waiting for real feed or simulation frame...</div>
        )}

        {payload?.tracks.map((track) => {
          const [x1, y1, x2, y2] = track.bbox;
          const isPriority = highlightPeople.has(track.person_id);
          return (
            <div
              key={track.person_id}
              className={`bbox ${isPriority ? "priority" : "normal"}`}
              style={{
                left: `${(x1 / frameW) * 100}%`,
                top: `${(y1 / frameH) * 100}%`,
                width: `${((x2 - x1) / frameW) * 100}%`,
                height: `${((y2 - y1) / frameH) * 100}%`,
              }}
              aria-label={`${track.person_id} bounding box`}
            >
              {isPriority && <span className="track-chip">{track.person_id}</span>}
            </div>
          );
        })}
      </div>
    </section>
  );
}
