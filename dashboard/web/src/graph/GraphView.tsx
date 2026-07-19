import { useMemo, useState, Component, type ReactNode } from "react";
import { Canvas } from "@react-three/fiber";
import { OrbitControls, Line } from "@react-three/drei";
import * as THREE from "three";
import { useStore } from "../store";
import { TYPE_COLORS, MACHINE_COLORS, SHARED_COLOR, type Fragment, type Edge } from "../types";
import { runLayout, type LayoutNode } from "./layout";

// Render the Canvas tree inside a boundary so a WebGL/runtime error shows a
// visible message instead of silently blanking the whole canvas.
class CanvasErrorBoundary extends Component<
  { children: ReactNode },
  { error: Error | null }
> {
  state = { error: null as Error | null };
  static getDerivedStateFromError(error: Error) {
    return { error };
  }
  render() {
    if (this.state.error) {
      return (
        <div style={{ padding: 24, color: "#ffb3c1", font: "13px ui-monospace, monospace" }}>
          <strong>3D view error:</strong> {String(this.state.error.message || this.state.error)}
        </div>
      );
    }
    return this.props.children;
  }
}

function FragmentNode({
  node, frag, dimmed, selected, onSelect, onHover,
}: {
  node: LayoutNode; frag: Fragment;
  dimmed: boolean; selected: boolean; onSelect: (id: string) => void;
  onHover: (id: string | null) => void;
}) {
  const color = TYPE_COLORS[frag.type] || "#888";
  const size = 0.35 + frag.total_weight * 0.9;
  // origin halo ring
  const halo =
    frag.shared ? SHARED_COLOR
    : frag.origin === "hermes" ? MACHINE_COLORS.hermes
    : MACHINE_COLORS.plato;
  const opacity = dimmed ? 0.12 : 1;
  return (
    <group position={[node.x ?? 0, node.y ?? 0, node.z ?? 0]}>
      <mesh
        onClick={(e) => { e.stopPropagation(); onSelect(frag.id); }}
        onPointerOver={(e) => { e.stopPropagation(); onHover(frag.id); document.body.style.cursor = "pointer"; }}
        onPointerOut={() => { onHover(null); document.body.style.cursor = "auto"; }}
      >
        <sphereGeometry args={[size, 24, 24]} />
        <meshStandardMaterial
          color={color}
          emissive={selected ? color : "#000000"}
          emissiveIntensity={selected ? 0.6 : 0.0}
          transparent opacity={opacity}
          roughness={0.5}
        />
      </mesh>
      {/* origin halo */}
      <mesh rotation={[Math.PI / 2, 0, 0]}>
        <ringGeometry args={[size + 0.12, size + 0.2, 28]} />
        <meshBasicMaterial color={halo} transparent opacity={opacity * 0.7} side={THREE.DoubleSide} />
      </mesh>
    </group>
  );
}

function Edges({ layout, frags, dimmed }: {
  layout: ReturnType<typeof runLayout>; frags: Set<string>; dimmed: boolean;
}) {
  if (!layout) return null;
  const pos = new Map(layout.nodes.map((n) => [n.id, n]));
  const colorFor = (k: string) =>
    k === "shared" ? "#f8fafc" : k === "contradiction" ? "#ff6b35"
    : k === "recurrence" ? "#a78bfa"
    : k === "co-occurs" ? "#334155"
    : "#475569";
  return (
    <>
      {layout.links.map((l, i) => {
        const s = pos.get(l.source as string);
        const t = pos.get(l.target as string);
        if (!s || !t) return null;
        const visible = !dimmed || (frags.has(l.source as string) && frags.has(l.target as string));
        return (
          <Line key={i}
            points={[[s.x ?? 0, s.y ?? 0, s.z ?? 0], [t.x ?? 0, t.y ?? 0, t.z ?? 0]]}
            color={colorFor(l.kind ?? "")} lineWidth={l.kind === "shared" ? 2 : 1}
            transparent opacity={visible ? 0.35 : 0.06} />
        );
      })}
    </>
  );
}

export default function GraphView({ fragments, edges }: { fragments: Fragment[]; edges: Edge[] }) {
  const machine = useStore((s) => s.machine);
  const filterTypes = useStore((s) => s.filter.types);
  const filterTrust = useStore((s) => s.filter.trust);
  const selectedId = useStore((s) => s.selectedId);
  const select = useStore((s) => s.select);
  const [hovered, setHovered] = useState<string | null>(null);

  const visFrags = useMemo(
    () => fragments.filter((f) => {
      if (machine === "plato" && f.origin === "hermes") return false;
      if (machine === "hermes" && f.origin === "plato") return false;
      if (!filterTypes.has(f.type)) return false;
      if (filterTrust.size > 0 && !filterTrust.has(f.trust_level)) return false;
      return true;
    }),
    [fragments, machine, filterTypes, filterTrust],
  );

  const layout = useMemo(() => runLayout(visFrags, edges), [visFrags, edges]);
  const fragById = useMemo(() => new Map(fragments.map((f) => [f.id, f])), [fragments]);

  // focus+context: if something selected/hovered, dim the rest
  const focusId = selectedId || hovered;
  const focusSet = useMemo(() => {
    if (!focusId || !layout) return null;
    const set = new Set<string>([focusId]);
    for (const l of layout.links) {
      const s = l.source as string;
      const t = l.target as string;
      if (s === focusId) set.add(t);
      if (t === focusId) set.add(s);
    }
    return set;
  }, [focusId, layout]);

  return (
    <CanvasErrorBoundary>
    <Canvas camera={{ position: [0, 0, 18], fov: 50 }} dpr={[1, 2]}
            onPointerMissed={() => select(null)}>
      <color attach="background" args={["#0b1020"]} />
      <ambientLight intensity={0.7} />
      <pointLight position={[10, 10, 10]} intensity={0.8} />
      <Edges layout={layout} frags={focusSet ?? new Set()} dimmed={!!focusSet} />
      {layout?.nodes.map((n) => {
        const f = fragById.get(n.id);
        if (!f) return null;
        const dimmed = !!focusSet && !focusSet.has(n.id);
        return (
          <FragmentNode key={n.id} node={n} frag={f}
            dimmed={dimmed} selected={selectedId === n.id}
            onSelect={select} onHover={setHovered} />
        );
      })}
      <OrbitControls enablePan enableZoom enableRotate makeDefault />
    </Canvas>
    </CanvasErrorBoundary>
  );
}
