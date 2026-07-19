// Shared types mirroring src/hum/dashboard.py output.

export type FragmentType =
   | "OBSERVATION"  | "BEHAVIOUR"  | "ASSOCIATION"  | "QUESTION"
   | "CONTRADICTION"| "RESISTANCE"    | "SEED"         | "WARNING";

export type MachineId = "plato" | "hermes";


export interface Scores {
  base_significance: number;
  recurrence: number;
  novelty: number;
  utility: number;
  active_work_connection: number;
  consequence: number;
  predictive_or_user: number;
  age_decay: number;
  contradiction_penalty: number;
  provenance_penalty: number;
  total_weight: number;
}

export interface Fragment {
  id: string;
  layer: string;
  type: FragmentType;
  status: string;
  created_at: string | null;
  updated_at: string | null;
  total_weight: number;
  scores: Scores;
  recurrence_count: number;
  first_seen: string | null;
  last_seen: string | null;
  trust_level: string;
  task: string | null;
  references: string[];
  evidence_for: unknown[];
  evidence_against: unknown[];
  content_hash: string;
  text: string;
  // merged-model additions
  origin?: MachineId;
  shared?: boolean;
}

export interface Edge {
  source: string;
  target: string;
  kind: "reference" | "recurrence" | "contradiction" | "shared" | "co-occurs";
}

export interface Facets {
  by_layer: Record<string, number>;
  by_type: Record<string, number>;
  by_status: Record<string, number>;
  by_trust: Record<string, number>;
  weight_hist: number[];
}

export interface MachineModel {
  machine_id: string;
  host: string | null;
  hum_dir: string;
  pulled_at: string | null;
  n_valid: number;
  n_invalid: number;
  facets: Facets;
  fragments: Fragment[];
  edges: Edge[];
  content_hashes: string[];
}

export interface Convergence {
  type_jaccard: number;
  trust_jaccard: number;
  trust_overlap: string[];
  shared_content_hashes: string[];
  shared_count: number;
  count_symmetry: number;
  symmetry_index: number;
}

export interface MergedModel {
  fragments: Fragment[];
  edges: Edge[];
  shared_content_hashes: string[];
}

export interface HUMModel {
  generated_at: string;
  machines: { plato: MachineModel; hermes: MachineModel };
  merged: MergedModel;
  convergence: Convergence;
  sources?: {
    hum_dir: string;
    hermes_host: string;
    hermes_cache_dir: string;
    hermes_available: boolean;
  };
}

export const TYPE_COLORS: Record<FragmentType, string> = {
  OBSERVATION: "#4cc9f0",
  BEHAVIOUR: "#4895ef",
  ASSOCIATION: "#7b2cbf",
  QUESTION: "#f72585",
  CONTRADICTION: "#ff6b35",
  RESISTANCE: "#e63946",
  SEED: "#2ec4b6",
  WARNING: "#ffd166",
};

export const MACHINE_COLORS: Record<MachineId, string> = {
  plato: "#22d3ee",
  hermes: "#f59e0b",
};

export const SHARED_COLOR = "#f8fafc";
