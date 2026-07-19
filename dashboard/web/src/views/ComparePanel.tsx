import { useStore } from "../store";
import { TYPE_COLORS, type FragmentType, type MachineModel } from "../types";

function DeltaBar({ label, plato, hermes, color }: {
  label: string; plato: number; hermes: number; color?: string;
}) {
  const max = Math.max(1, plato, hermes);
  const delta = plato - hermes;
  const dClass = delta > 0 ? "up" : delta < 0 ? "down" : "";
  return (
    <div className="facet-row">
      <span className="facet-label" style={color ? { color } : undefined}>{label}</span>
      <div className="facet-bars">
        <div className="bar p" style={{ width: `${(plato / max) * 100}%` }} title={`Plato ${plato}`} />
        <div className="bar h" style={{ width: `${(hermes / max) * 100}%` }} title={`Hermes ${hermes}`} />
      </div>
      <span className="facet-num">
        <b style={{ color: "#22d3ee" }}>{plato}</b>
        <i> / </i>
        <b style={{ color: "#f59e0b" }}>{hermes}</b>
        {delta !== 0 && <em className={`delta ${dClass}`}> ({delta > 0 ? "+" : ""}{delta})</em>}
      </span>
    </div>
  );
}

function FacetBlock({ title, plato, hermes }: {
  title: string; plato: Record<string, number>; hermes: Record<string, number>;
}) {
  const keys = Array.from(new Set([...Object.keys(plato), ...Object.keys(hermes)]))
    .sort((a, b) => (plato[b] || 0) + (hermes[b] || 0) - (plato[a] || 0) - (hermes[a] || 0));
  return (
    <div className="facet-block">
      <div className="facet-title">{title}</div>
      {keys.map((k) => (
        <DeltaBar key={k} label={k} plato={plato[k] || 0} hermes={hermes[k] || 0}
          color={TYPE_COLORS[k as FragmentType]} />
      ))}
    </div>
  );
}

export default function ComparePanel() {
  const model = useStore((s) => s.model);
  if (!model) return null;
  const p: MachineModel = model.machines.plato;
  const h: MachineModel = model.machines.hermes;
  return (
    <div className="compare">
      <FacetBlock title="Fragment type" plato={p.facets.by_type} hermes={h.facets.by_type} />
      <FacetBlock title="Trust level" plato={p.facets.by_trust} hermes={h.facets.by_trust} />
      <FacetBlock title="Lifecycle status" plato={p.facets.by_status} hermes={h.facets.by_status} />
      <FacetBlock title="Layer" plato={p.facets.by_layer} hermes={h.facets.by_layer} />
      <div className="facet-block">
        <div className="facet-title">Weight distribution (0–1)</div>
        {p.facets.weight_hist.map((pv, i) => (
          <DeltaBar key={i} label={`${i / 10}–${(i + 1) / 10}`}
            plato={pv} hermes={h.facets.weight_hist[i] || 0} />
        ))}
      </div>
    </div>
  );
}
