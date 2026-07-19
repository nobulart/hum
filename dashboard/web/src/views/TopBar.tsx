import { useStore, type MachineSel, type ViewMode } from "../store";
import { useHUMStream } from "../useHUMStream";

const MACHINES: MachineSel[] = ["plato", "hermes", "both"];
const VIEWS: ViewMode[] = ["graph", "flow", "timeline"];

export default function TopBar() {
  const { pull } = useHUMStream();
  const model = useStore((s) => s.model);
  const machine = useStore((s) => s.machine);
  const setMachine = useStore((s) => s.setMachine);
  const view = useStore((s) => s.view);
  const setView = useStore((s) => s.setView);
  const webgpu = useStore((s) => s.webgpu);
  const setWebGPU = useStore((s) => s.setWebGPU);
  const toggleCommand = useStore((s) => s.toggleCommand);
  const pulling = useStore((s) => s.pulling);
  const hermesAvailable = useStore((s) => s.hermesAvailable);

  const conv = model?.convergence;
  const sim = conv ? Math.round(conv.symmetry_index * 100) : 0;

  return (
    <header className="topbar">
      <div className="brand">HUM<span>·</span>dashboard</div>

      <div className="seg machine-seg">
        {MACHINES.map((m) => (
          <button key={m} className={machine === m ? "on" : ""}
            onClick={() => setMachine(m)}>
            {m === "both" ? "Both" : m === "plato" ? "Plato" : "Hermes"}
          </button>
        ))}
      </div>

      <div className="seg view-seg">
        {VIEWS.map((v) => (
          <button key={v} className={view === v ? "on" : ""}
            onClick={() => setView(v)}>{v}</button>
        ))}
      </div>

      {conv && (
        <div className="conv" title={`type Jaccard ${conv.type_jaccard}, trust Jaccard ${conv.trust_jaccard}, shared ${conv.shared_count}`}>
          <span className="conv-label">convergence</span>
          <span className="conv-val">{sim}%</span>
        </div>
      )}

      <div className="spacer" />

      <button className="ghost" onClick={() => toggleCommand()} title="⌘K">⌘K</button>
      <button className={`ghost ${webgpu ? "on" : ""}`} onClick={() => setWebGPU(!webgpu)}
        title="WebGPU renderer (Safari 26 / Chrome)">WebGPU</button>
      <button className={`pull ${pulling ? "busy" : ""}`} onClick={pull}
        disabled={pulling || !hermesAvailable}
        title={hermesAvailable ? `pull ${model?.sources?.hermes_host}` : "Hermes unavailable"}>
        {pulling ? "pulling…" : "↻ pull Hermes"}
      </button>
    </header>
  );
}
