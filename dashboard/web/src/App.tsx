import { useStore } from "./store";
import { useHUMStream } from "./useHUMStream";
import TopBar from "./views/TopBar";
import GraphView from "./graph/GraphView";
import FlowView from "./views/FlowView";
import TimelineView from "./views/TimelineView";
import ComparePanel from "./views/ComparePanel";
import Inspector from "./views/Inspector";
import CommandBar from "./views/CommandBar";

export default function App() {
  // subscribe to the stream once at the app root
  useHUMStream();
  const model = useStore((s) => s.model);
  const view = useStore((s) => s.view);
  const machine = useStore((s) => s.machine);
  const error = useStore((s) => s.lastError);
  const toggleCommand = useStore((s) => s.toggleCommand);

  // ⌘K / Ctrl-K
  if (typeof window !== "undefined") {
    window.onkeydown = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        toggleCommand();
      }
    };
  }

  if (!model) {
    return (
      <div className="app">
        <TopBar />
        <div className="loading">{error ? `error: ${error}` : "loading HUM corpus…"}</div>
      </div>
    );
  }

  const fragments = model.merged.fragments.filter((f) => {
    if (machine === "plato" && f.origin === "hermes") return false;
    if (machine === "hermes" && f.origin === "plato") return false;
    return true;
  });

  return (
    <div className="app">
      <TopBar />
      <div className="main">
        <section className="canvas-wrap">
          {view === "graph" && <GraphView fragments={fragments} edges={model.merged.edges} />}
          {view === "flow" && <FlowView />}
          {view === "timeline" && <TimelineView />}
          {error && <div className="toast">{error}</div>}
        </section>
        <aside className="side">
          <ComparePanel />
          <Inspector />
        </aside>
      </div>
      <CommandBar />
    </div>
  );
}
