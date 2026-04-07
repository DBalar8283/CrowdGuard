import type { StreamPayload } from "../types";

interface Props {
  payload: StreamPayload | null;
}

export function MiniMapPanel({ payload }: Props) {
  const los = payload?.fruin_level ?? "A";
  const zoneClass = los === "E" || los === "F" ? "zone-box zone-hot" : los === "D" ? "zone-box zone-warn" : "zone-box";

  return (
    <section className="panel panel-mini">
      <header className="panel-header">
        <h2>Digital Twin</h2>
        <div className="panel-meta">LOS {los}</div>
      </header>
      <svg className="minimap" viewBox="0 0 100 100" role="img" aria-label="Zone minimap">
        <rect x="1" y="1" width="98" height="98" className={zoneClass} />
        {payload?.tracks.map((track) => (
          <circle key={track.person_id} cx={track.map_point.x * 10} cy={track.map_point.y * 10} r="1.6" className="person-dot" />
        ))}
      </svg>
    </section>
  );
}
