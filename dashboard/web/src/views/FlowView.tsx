import { useStore } from "../store";
import type { MachineModel } from "../types";

// Six-stage pipeline. Position = vertical order. Two parallel lanes (Plato/Hermes).
const STAGES = ["DREAMS", "SURFACE", "DREAMS_DAY", "SUBCONSCIOUS", "DREAMS_ARCHIVE", "DREAMS_QUARANTINE"];

function Lane({ machine }: { machine: MachineModel | null }) {
  if (!machine) return <div className="lane-empty">unavailable</div>;
  return (
    <div className="lane">
      {STAGES.map((stage) => {
        const n = machine.facets.by_layer[stage] || 0;
        const invalid = stage === "DREAMS_QUARANTINE" ? machine.n_invalid : 0;
        const total = stage === "DREAMS_QUARANTINE" ? invalid : n;
        return (
          <div className="stage" key={stage}>
            <div className="stage-name">{stage.replace("DREAMS_", "").replace("DREAMS", "NIGHT")}</div>
            <div className={`stage-bar ${stage === "DREAMS_QUARANTINE" ? "bad" : ""}`}
                 style={{ width: `${Math.min(100, total * 22)}%` }} />
            <div className="stage-count">{total}</div>
          </div>
        );
      })}
    </div>
  );
}

export default function FlowView() {
  const model = useStore((s) => s.model);
  const machine = useStore((s) => s.machine);
  const p = model?.machines.plato ?? null;
  const h = model?.machines.hermes ?? null;
  const showP = machine !== "hermes";
  const showH = machine !== "plato";
  return (
    <div className="flow">
      {showP && (
        <div className="flow-col">
          <div className="flow-head" style={{ color: "#22d3ee" }}>PLATO · MacBook</div>
          <Lane machine={p} />
        </div>
      )}
      {showH && (
        <div className="flow-col">
          <div className="flow-head" style={{ color: "#f59e0b" }}>HERMES · Mac Studio</div>
          <Lane machine={h} />
        </div>
      )}
    </div>
  );
}
