import { useMemo, useRef, useState, Component, type ReactNode } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls, Line, Html } from "@react-three/drei";
import * as THREE from "three";
import { useStore } from "../store";
import { TYPE_COLORS, MACHINE_COLORS, SHARED_COLOR, type Fragment, type Edge } from "../types";
import { runLayout, type LayoutNode, type Stratum } from "./layout";

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

// Animated glowball: a small emissive core plus an additive back-side shell that
// reads as a soft halo without adding any lights (keeps perf flat at scale).
function FragmentNode({
  node, frag, dimmed, selected, onSelect, onHover, targetY,
}: {
  node: LayoutNode; frag: Fragment;
  dimmed: boolean; selected: boolean; onSelect: (id: string) => void;
  onHover: (id: string | null) => void; targetY: number;
}) {
  const color = TYPE_COLORS[frag.type] || "#888";
  const size = 0.18 + frag.total_weight * 0.5;
  const halo =
    frag.shared ? SHARED_COLOR
    : frag.origin === "hermes" ? MACHINE_COLORS.hermes
    : MACHINE_COLORS.plato;
  const opacity = dimmed ? 0.1 : 1;

  // promotion tween: ease Y from previous stratum to the new one
  const group = useRef<THREE.Group>(null);
  const yRef = useRef(node.y);
  useFrame(() => {
    if (group.current) {
      yRef.current += (targetY - yRef.current) * 0.12;
      group.current.position.y = yRef.current;
    }
  });

  return (
    <group ref={group} position={[node.x, node.y, node.z]}>
      <mesh
        onClick={(e) => { e.stopPropagation(); onSelect(frag.id); }}
        onPointerOver={(e) => { e.stopPropagation(); onHover(frag.id); document.body.style.cursor = "pointer"; }}
        onPointerOut={() => { onHover(null); document.body.style.cursor = "auto"; }}
      >
        <sphereGeometry args={[size, 20, 20]} />
        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={selected ? 0.9 : 0.45}
          transparent opacity={opacity * 0.92}
          roughness={0.45}
          metalness={0.0}
        />
      </mesh>
      {/* soft additive halo */}
      <mesh scale={1.9}>
        <sphereGeometry args={[size, 16, 16]} />
        <meshBasicMaterial
          color={color}
          transparent
          opacity={opacity * (selected ? 0.28 : 0.16)}
          blending={THREE.AdditiveBlending}
          depthWrite={false}
          side={THREE.BackSide}
        />
      </mesh>
      {/* origin halo ring */}
      <mesh rotation={[Math.PI / 2, 0, 0]}>
        <ringGeometry args={[size + 0.1, size + 0.17, 24]} />
        <meshBasicMaterial color={halo} transparent opacity={opacity * 0.7} side={THREE.DoubleSide} />
      </mesh>
    </group>
  );
}

function Edges({ layout, frags, dimmed }: { layout: ReturnType<typeof runLayout>; frags: Set<string>; dimmed: boolean }) {
  const pos = new Map(layout.nodes.map((n) => [n.id, n]));
  const colorFor = (k: string) =>
    k === "shared" ? "#f8fafc" : k === "contradiction" ? "#ff6b35"
    : k === "recurrence" ? "#a78bfa"
    : k === "co-occurs" ? "#334155"
    : "#475569";
  return (
    <>
      {layout.links.map((l, i) => {
        const s = pos.get(l.source);
        const t = pos.get(l.target);
        if (!s || !t) return null;
        const visible = !dimmed || (frags.has(l.source) && frags.has(l.target));
        return (
          <Line key={i}
            points={[[s.x, s.y, s.z], [t.x, t.y, t.z]]}
            color={colorFor(l.kind ?? "")} lineWidth={l.kind === "shared" ? 2 : 1}
            transparent opacity={visible ? 0.32 : 0.05} />
        );
      })}
    </>
  );
}

function StratumDisc({ stratum }: { stratum: Stratum }) {
  return (
    <group position={[0, stratum.y, 0]}>
      <mesh rotation={[-Math.PI / 2, 0, 0]}>
        <ringGeometry args={[stratum.radius * 0.96, stratum.radius * 1.04, 64]} />
        <meshBasicMaterial color="#22304f" transparent opacity={0.5} side={THREE.DoubleSide} />
      </mesh>
      <Html position={[stratum.radius + 0.4, 0, 0]} center distanceFactor={14} style={{ pointerEvents: "none" }}>
        <div style={{
          font: "600 11px ui-monospace, monospace", letterSpacing: "0.5px",
          color: "#7c8aa5", whiteSpace: "nowrap", textTransform: "uppercase",
          textShadow: "0 0 6px #000",
        }}>
          {stratum.layer}<span style={{ color: "#475569" }}> · {stratum.count}</span>
        </div>
      </Html>
    </group>
  );
}

function Legend() {
  const items: [string, string][] = [
    ["co-occurs", "#334155"],
    ["reference", "#475569"],
    ["recurrence", "#a78bfa"],
    ["contradiction", "#ff6b35"],
    ["shared", "#f8fafc"],
  ];
  return (
    <div className="legend">
      <div className="legend-title">edges</div>
      {items.map(([k, c]) => (
        <div key={k} className="legend-row">
          <span className="legend-swatch" style={{ background: c }} />
          {k}
        </div>
      ))}
    </div>
  );
}

export default function GraphView({ fragments, edges }: { fragments: Fragment[]; edges: Edge[] }) {
  const machine = useStore((s) => s.machine);
  const filterTypes = useStore((s) => s.filter.types);
  const filterTrust = useStore((s) => s.filter.trust);
  const filterText = useStore((s) => s.filter.text);
  const selectedId = useStore((s) => s.selectedId);
  const select = useStore((s) => s.select);
  const [hovered, setHovered] = useState<string | null>(null);

  const visFrags = useMemo(
    () => fragments.filter((f) => {
      if (machine === "plato" && f.origin === "hermes") return false;
      if (machine === "hermes" && f.origin === "plato") return false;
      if (!filterTypes.has(f.type)) return false;
      if (filterTrust.size > 0 && !filterTrust.has(f.trust_level)) return false;
      if (filterText && !(f.text || "").toLowerCase().includes(filterText.toLowerCase())) return false;
      return true;
    }),
    [fragments, machine, filterTypes, filterTrust, filterText],
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

  // target Y per node, so a layer change between pulls tweens the node down
  const targetYById = useMemo(() => {
    const m = new Map<string, number>();
    for (const n of layout.nodes) m.set(n.id, n.y);
    return m;
  }, [layout]);

  return (
    <div className="graph-wrap">
      <CanvasErrorBoundary>
        <Canvas camera={{ position: [0, 2, 18], fov: 50 }} dpr={[1, 2]}
                onPointerMissed={() => select(null)}>
          <color attach="background" args={["#0b1020"]} />
          <ambientLight intensity={0.75} />
          <pointLight position={[10, 10, 10]} intensity={0.7} />
          {layout.strata.map((s) => <StratumDisc key={s.layer} stratum={s} />)}
          <Edges layout={layout} frags={focusSet ?? new Set()} dimmed={!!focusSet} />
          {layout.nodes.map((n) => {
            const f = fragById.get(n.id);
            if (!f) return null;
            const dimmed = !!focusSet && !focusSet.has(n.id);
            const targetY = targetYById.get(n.id) ?? n.y;
            return (
              <FragmentNode key={n.id} node={n} frag={f}
                dimmed={dimmed} selected={selectedId === n.id}
                onSelect={select} onHover={setHovered} targetY={targetY} />
            );
          })}
          <OrbitControls enablePan enableZoom enableRotate makeDefault target={[0, 0, 0]} />
        </Canvas>
      </CanvasErrorBoundary>
      <Legend />
    </div>
  );
}
