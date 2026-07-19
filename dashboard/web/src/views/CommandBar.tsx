import { useEffect, useRef, useState } from "react";
import { useStore } from "../store";
import { ALL_TYPES } from "../store";
import { TYPE_COLORS } from "../types";

// A quiet ⌘K command bar: filter by type, jump to a fragment, toggle view.
export default function CommandBar() {
  const open = useStore((s) => s.commandOpen);
  const toggle = useStore((s) => s.toggleCommand);
  const model = useStore((s) => s.model);
  const toggleType = useStore((s) => s.toggleType);
  const setView = useStore((s) => s.setView);
  const select = useStore((s) => s.select);
  const [q, setQ] = useState("");
  const ref = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (open && ref.current) ref.current.focus();
  }, [open]);

  if (!open) return null;
  const fragMatches = model
    ? model.merged.fragments.filter((f) =>
        (f.text || "").toLowerCase().includes(q.toLowerCase()))
      .slice(0, 12)
    : [];

  return (
    <div className="cmdk-backdrop" onClick={() => toggle(false)}>
      <div className="cmdk" onClick={(e) => e.stopPropagation()}>
        <input ref={ref} value={q} onChange={(e) => setQ(e.target.value)}
          placeholder="filter types · jump to fragment · set view…" />
        <div className="cmdk-section">Types</div>
        <div className="cmdk-types">
          {ALL_TYPES.map((t) => (
            <button key={t} className="cmdk-type"
              style={{ borderColor: TYPE_COLORS[t] }}
              onClick={() => toggleType(t)}>{t}</button>
          ))}
        </div>
        <div className="cmdk-section">Views</div>
        <div className="cmdk-row">
          {(["graph", "flow", "timeline"] as const).map((v) => (
            <button key={v} onClick={() => { setView(v); toggle(false); }}>{v}</button>
          ))}
        </div>
        {q && (
          <>
            <div className="cmdk-section">Fragments</div>
            {fragMatches.map((f) => (
              <button key={f.id} className="cmdk-frag"
                onClick={() => { select(f.id); toggle(false); setQ(""); }}>
                <span style={{ color: TYPE_COLORS[f.type] }}>{f.type}</span> · {f.text.slice(0, 60)}
              </button>
            ))}
          </>
        )}
      </div>
    </div>
  );
}
