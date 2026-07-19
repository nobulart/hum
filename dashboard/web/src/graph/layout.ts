import {
  forceSimulation,
  forceManyBody,
  forceLink,
  forceCenter,
  type Simulation,
} from "d3-force";
import type { Fragment, Edge } from "../types";

// A layout node. We DO NOT extend d3's SimulationNodeDatum (its named
// type export is unreliable in this toolchain); instead we keep our own
// interface and cast at the force-simulation boundary.
export interface LayoutNode {
  id: string;
  frag: Fragment;
  origin: "plato" | "hermes" | "shared" | null;
  shared: boolean;
  index?: number;
  x?: number;
  y?: number;
  z?: number;
  vx?: number;
  vy?: number;
  fx?: number | null;
  fy?: number | null;
}

type LayoutLink = {
  source: LayoutNode | string;
  target: LayoutNode | string;
  kind?: string;
  index?: number;
};

// Nodes are clamped to this radius so they always sit inside the camera frame
// (camera at z=18, fov=50 -> visible half-height ~8.4 units). Without it,
// sparse/repulsive layouts fling nodes off-screen.
const VISIBLE_R = 7;

/**
 * Compute a force-directed layout of the HUM fragment graph.
 *
 * `edgesRaw` may reference fragments not present in `nodesRaw` (e.g. the caller
 * passes the full merged edge list while the node set is filtered by the
 * machine selector). We drop any link whose endpoint is missing, because
 * d3-force's forceLink throws "node not found" on dangling endpoints.
 */
export function runLayout(nodesRaw: Fragment[], edgesRaw: Edge[]) {
  const nodes: LayoutNode[] = nodesRaw.map((f, i) => {
    const spread = ((parseInt(String(f.content_hash ?? i), 10) % 360) || (i * 37 % 360)) * (Math.PI / 180);
    return {
      id: String(f.id ?? f.content_hash ?? Math.random().toString(36).slice(2, 10)),
      frag: f,
      origin: (f.origin ?? null) as LayoutNode["origin"],
      shared: !!f.shared,
      x: Math.cos(spread) * 5,
      y: Math.sin(spread) * 5,
      z: 0,
    };
  });

  const nodeIds = new Set(nodes.map((n) => n.id));
  const links: LayoutLink[] = edgesRaw
    .filter((e) => nodeIds.has(String(e.source)) && nodeIds.has(String(e.target)))
    .map((e) => ({ source: e.source, target: e.target, kind: e.kind }));

  try {
    // Run the 2D force simulation manually (deterministic, fast at this scale).
    const sim: Simulation<LayoutNode, LayoutLink> = forceSimulation<LayoutNode, LayoutLink>(
      nodes as unknown as LayoutNode[],
    )
      .force(
        "link",
        forceLink<LayoutNode, LayoutLink>(links as any)
          .id((d: LayoutNode) => d.id)
          .distance(70),
      )
      .force("charge", forceManyBody<LayoutNode>().strength(-400))
      .force("center", forceCenter<LayoutNode>(0, 0))
      .stop();

    const ticks = Math.min(200, 20 + nodes.length * 6);
    for (let i = 0; i < ticks; i++) sim.tick();

    clampToRadius(nodes, VISIBLE_R);

    // Machine separation in Z.
    const zMap: Record<string, number> = { plato: -4, hermes: 4, shared: 0, "null": 0 };
    for (const n of nodes) {
      const key = n.shared ? "shared" : String(n.origin ?? "null");
      n.z = zMap[key] ?? 0;
    }

    return { nodes, links };
  } catch (e) {
    console.error("[hum-dashboard] runLayout error:", e);
    // Graceful fallback: a visible grid (clamped) so the UI still renders.
    for (let i = 0; i < nodes.length; i++) {
      nodes[i].x = ((i % 5) - 2) * 2.4;
      nodes[i].y = (Math.floor(i / 5) - 1) * 2.4;
      nodes[i].z =
        ((nodes[i].origin ?? "null") === "plato"
          ? -4
          : nodes[i].origin === "hermes"
            ? 4
            : 0);
    }
    clampToRadius(nodes, VISIBLE_R);
    return { nodes, links };
  }
}

function clampToRadius(nodes: LayoutNode[], R: number) {
  for (const n of nodes) {
    const r = Math.hypot(n.x ?? 0, n.y ?? 0);
    if (r > R) {
      const k = R / r;
      n.x = (n.x ?? 0) * k;
      n.y = (n.y ?? 0) * k;
    }
  }
}
