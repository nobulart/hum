declare module "d3-force-3d" {
  export interface SimulationNodeDatum {
    index?: number;
    x?: number; y?: number; z?: number;
    vx?: number; vy?: number; vz?: number;
    fx?: number; fy?: number; fz?: number;
  }
  export interface SimulationLinkDatum<N> {
    source: N | string | number;
    target: N | string | number;
    index?: number;
  }
  export interface Force<N extends SimulationNodeDatum, L> {
    (alpha?: number): void;
    initialize?: (nodes: N[], ...args: unknown[]) => void;
  }
  export interface Simulation<N extends SimulationNodeDatum, L> {
    tick(iterations?: number): this;
    stop(): this;
    nodes(): N[];
    nodes(nodes: N[]): this;
    force(name: string): unknown;
    force(name: string, force: unknown): this;
    alpha(x: number): this;
    alphaMin(x: number): this;
    on(type: string, cb: (() => void) | null): this;
  }
  export function forceSimulation<N extends SimulationNodeDatum>(
    nodes?: N[],
  ): Simulation<N, unknown>;
  export function forceManyBody(): Force<SimulationNodeDatum, unknown> & { strength(s: number): unknown };
  export function forceLink<N extends SimulationNodeDatum, L>(
    links?: L[],
  ): Force<N, L> & { id(fn: (n: N) => string): unknown; distance(d: number): unknown; strength(s: number): unknown };
  export function forceCenter(x?: number, y?: number, z?: number): Force<SimulationNodeDatum, unknown>;
  export function forceX(x?: number): Force<SimulationNodeDatum, unknown> & { strength(s: number): unknown };
  export function forceY(y?: number): Force<SimulationNodeDatum, unknown> & { strength(s: number): unknown };
  export function forceZ(z?: number): Force<SimulationNodeDatum, unknown> & { strength(s: number): unknown };
}
