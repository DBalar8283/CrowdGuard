import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

interface TrendPoint {
  time: string;
  density: number;
  velocity: number;
}

interface Props {
  points: TrendPoint[];
  densityNow: number;
  velocityNow: number;
}

function densityPercent(density: number) {
  return Math.max(0, Math.min(100, (density / 1.8) * 100));
}

export function AnalyticsPanel({ points, densityNow, velocityNow }: Props) {
  return (
    <section className="panel panel-analytics">
      <header className="panel-header">
        <h2>Operational Trends</h2>
      </header>

      <div className="ops-metrics">
        <article className="ops-card">
          <h3>Density Gauge</h3>
          <div className="gauge-track" aria-label="Density gauge">
            <div className="gauge-fill" style={{ width: `${densityPercent(densityNow)}%` }} />
          </div>
          <p>{densityNow.toFixed(3)} /m2</p>
        </article>

        <article className="ops-card">
          <h3>Velocity</h3>
          <p>{velocityNow.toFixed(3)} m/s</p>
          <small className={velocityNow < 0.04 ? "risk-text" : "muted"}>
            {velocityNow < 0.04 ? "Potential bottleneck" : "Flow stable"}
          </small>
        </article>
      </div>

      <div className="chart-wrap">
        <ResponsiveContainer width="100%" height={170}>
          <AreaChart data={points}>
            <XAxis dataKey="time" hide />
            <YAxis domain={[0, "auto"]} hide />
            <Tooltip />
            <Area type="monotone" dataKey="density" stroke="#ff6b6b" fill="#ff6b6b33" strokeWidth={2} />
            <Area type="monotone" dataKey="velocity" stroke="#60d0ff" fill="#60d0ff28" strokeWidth={2} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
