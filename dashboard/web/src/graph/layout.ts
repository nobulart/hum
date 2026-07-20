import type { Fragment, Edge } from "../types";

// Layout node for the HUM fragment graph.
export interface LayoutNode {
  id: string;
  frag: Fragment;
  origin: "plato" | "hermes" | "shared" | null;
  shared: boolean;
  layer: string;
  layerIndex: number;
  x: number;
  y: number;
  z: number;
}

type LayoutLink = { source: string; target: string; kind?: string };

// Vertical stack order, top -> bottom. Mirrors the backend LAYERS constant
// (src/hum/dashboard.py). Unknown layers fall to the bottom bucket so the view
// never breaks when a new stratum appears.
export const STRATA_ORDER = [
  "DREAMS", "SURFACE", "DREAMS_DAY", "SUBCONSCIOUS",
  "DREAMS_ARCHIVE", "DREAMS_QUARANTINE",
];

export interface Stratum {
  layer: string;
  index: number;
  y: number;
  radius: number;
  count: number;
}

export interface LayoutResult {
  nodes: LayoutNode[];
  links: LayoutLink[];
  strata: Stratum[];
}

const STRATA_GAP = 3.0; // vertical spacing between rings
const R_MIN = 1.6; // base ring radius for a sparse stratum
const R_K = 0.95; // density term: ring grows with sqrt(count)
const GOLDEN = 2.399963229728653; // golden angle for even angular spread
const VISIBLE_R = 8.0; // clamp so rings stay inside the camera frame

function layerIndex(layer: string | undefined): number {
  const i = STRATA_ORDER.indexOf((layer ?? "").toUpperCase());
  return i >= 0 ? i : STRATA_ORDER.length;
}

// Deterministic [0,1) hash so node placement is stable across refreshes
// (same id -> same spot), which makes the promotion tween readable.
function hash01(s: string, salt = 0): number {
  let h = 2166136261 ^ salt;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return ((h >>> 0) % 100000) / 100000;
}

/**
 * Deterministic strata-ring layout.
 *
 * Replaces the old 2D d3-force sim (which collapsed every fragment into one
 * plane and overlapped them). Each fragment now sits in a horizontal ring whose
 * Y is fixed by its HUM `layer` — directly mirroring the conceptual "stacked
 * cloud rings" model. Within a ring, fragments are spread by golden angle with
 * small radial jitter, so they never pile up. Ring radius scales with
 * sqrt(count) so busy strata (DREAMS) get more room.
 *
 * `co-occurs` edges already link fragments sharing a layer file, so intra-ring
 * arcs and cross-ring reference lines both read naturally.
 */
export function runLayout(nodesRaw: Fragment[], edgesRaw: Edge[]): LayoutResult {
  const nLayers = STRATA_ORDER.length + 1; // +1 for the unknown bucket
  const mid = (nLayers - 1) / 2;

  // bucket fragments by stratum
  const groups = new Map<string, Fragment[]>();
  for (const f of nodesRaw) {
    const key = String(layerIndex(f.layer));
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key)!.push(f);
  }

  const strata: Stratum[] = [];
  const nodes: LayoutNode[] = [];

  for (const [key, frags] of groups) {
    const li = Number(key);
    const y = (mid - li) * STRATA_GAP;
    const count = frags.length;
    const radius = count <= 1 ? R_MIN * 0.5 : R_MIN + R_K * Math.sqrt(count);
    strata.push({
      layer: STRATA_ORDER[li] ?? "OTHER",
      index: li,
      y,
      radius,
      count,
    });

    frags.forEach((f, k) => {
      const theta = GOLDEN * k + hash01(String(f.id ?? f.content_hash ?? k), 7) * 0.9;
      const rJitter = (hash01(String(f.id), 13) - 0.5) * 0.5;
      const r = count <= 1 ? 0 : radius + rJitter;
      const id = String(f.id ?? f.content_hash ?? Math.random().toString(36).slice(2, 10));
      nodes.push({
        id,
        frag: f,
        origin: (f.origin ?? null) as LayoutNode["origin"],
        shared: !!f.shared,
        layer: f.layer ?? "",
        layerIndex: li,
        x: Math.cos(theta) * r,
        y,
        z: Math.sin(theta) * r,
      });
    });
  }

  const nodeIds = new Set(nodes.map((n) => n.id));
  const links: LayoutLink[] = edgesRaw
    .filter((e) => nodeIds.has(String(e.source)) && nodeIds.has(String(e.target)))
    .map((e) => ({ source: String(e.source), target: String(e.target), kind: e.kind }));

  // keep rings inside the visible frame
  for (const n of nodes) {
    const r = Math.hypot(n.x, n.z);
    if (r > VISIBLE_R) {
      const k = VISIBLE_R / r;
      n.x *= k;
      n.z *= k;
    }
  }

  strata.sort((a, b) => a.index - b.index);
  return { nodes, links, strata };
}
