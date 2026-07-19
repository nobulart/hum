import { useStore } from "../store";
import type { Fragment } from "../types";

function byDay(frags: Fragment[]): Map<string, { plato: number; hermes: number }> {
  const m = new Map<string, { plato: number; hermes: number }>();
  for (const f of frags) {
    const d = (f.created_at || "").slice(0, 10);
    if (!d) continue;
    const e = m.get(d) || { plato: 0, hermes: 0 };
    if (f.origin === "hermes") e.hermes++;
    else e.plato++;
    m.set(d, e);
  }
  return m;
}

export default function TimelineView() {
  const model = useStore((s) => s.model);
  const machine = useStore((s) => s.machine);
  if (!model) return null;
  const frags = model.merged.fragments.filter((f) => {
    if (machine === "plato" && f.origin === "hermes") return false;
    if (machine === "hermes" && f.origin === "plato") return false;
    return true;
  });
  const days = Array.from(byDay(frags).entries()).sort();
  const max = Math.max(1, ...days.flatMap(([, v]) => [v.plato, v.hermes]));

  return (
    <div className="timeline">
      <div className="tl-title">Fragment accumulation by day</div>
      {days.length === 0 && <div className="tl-empty">no dated fragments yet</div>}
      {days.map(([day, v]) => (
        <div className="tl-row" key={day}>
          <span className="tl-day">{day}</span>
          <div className="tl-bars">
            {machine !== "hermes" && (
              <div className="tl-bar p" style={{ width: `${(v.plato / max) * 100}%` }} title={`Plato ${v.plato}`} />
            )}
            {machine !== "plato" && (
              <div className="tl-bar h" style={{ width: `${(v.hermes / max) * 100}%` }} title={`Hermes ${v.hermes}`} />
            )}
          </div>
          <span className="tl-num">{v.plato + v.hermes}</span>
        </div>
      ))}
      <div className="tl-legend">
        <span style={{ color: "#22d3ee" }}>■ Plato</span>
        <span style={{ color: "#f59e0b" }}>■ Hermes</span>
      </div>
    </div>
  );
}
