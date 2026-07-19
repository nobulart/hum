import { useStore } from "../store";
import { TYPE_COLORS, MACHINE_COLORS, SHARED_COLOR } from "../types";

export default function Inspector() {
  const model = useStore((s) => s.model);
  const selectedId = useStore((s) => s.selectedId);
  const select = useStore((s) => s.select);
  if (!model || !selectedId) return null;
  const frag = model.merged.fragments.find((f) => f.id === selectedId);
  if (!frag) return null;
  const color = TYPE_COLORS[frag.type] || "#888";
  const halo = frag.shared ? SHARED_COLOR
    : frag.origin === "hermes" ? MACHINE_COLORS.hermes : MACHINE_COLORS.plato;
  return (
    <div className="inspector">
      <button className="insp-close" onClick={() => select(null)}>×</button>
      <div className="insp-type" style={{ color }}>{frag.type}</div>
      <div className="insp-meta">
        <span className="badge" style={{ borderColor: halo, color: halo }}>
          {frag.origin?.toUpperCase()}{frag.shared ? " · SHARED" : ""}
        </span>
        <span className="badge">{frag.status}</span>
        <span className="badge">{frag.layer}</span>
      </div>
      <div className="insp-body">{frag.text}</div>
      <dl className="insp-scores">
        <dt>weight</dt><dd>{frag.total_weight.toFixed(3)}</dd>
        <dt>recurrence</dt><dd>{frag.recurrence_count}</dd>
        <dt>trust</dt><dd>{frag.trust_level}</dd>
        <dt>task</dt><dd>{frag.task || "—"}</dd>
        <dt>created</dt><dd>{frag.created_at || "—"}</dd>
        <dt>hash</dt><dd className="mono">{frag.content_hash}</dd>
      </dl>
      {frag.evidence_for?.length > 0 && (
        <div className="insp-ev"><b>for:</b> {frag.evidence_for.join("; ")}</div>
      )}
      {frag.evidence_against?.length > 0 && (
        <div className="insp-ev bad"><b>against:</b> {frag.evidence_against.join("; ")}</div>
      )}
    </div>
  );
}
