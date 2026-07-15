export type Priority = "must_have" | "nice_to_have" | "deal_breaker";
export type Operator = "eq" | "contains" | "gte" | "lte" | "not_eq" | null;

export type Criterion = {
  id: string;
  label: string;
  priority: Priority;
  field: string | null;
  operator: Operator;
  value: string | number | boolean | null;
  verifiable: boolean;
};

export type BuyerBrief = {
  version: 1;
  mode: "property_search" | "web_research";
  original_query: string;
  currency: string;
  criteria: Criterion[];
};

export type CriterionEvaluation = {
  criterion_id: string;
  label: string;
  priority: Priority;
  status: "matched" | "conflict" | "unknown" | "unsupported";
  actual: unknown;
};

export type Property = {
  id: string;
  title: string;
  area: string;
  price: number | null;
  currency: string;
  beds: number | null;
  baths: number | null;
  property_type: string | null;
  furnishing: string | null;
  completion_status: string | null;
  building_name?: string | null;
  building_total_area_sqft?: number | null;
  building_total_parking_spaces?: number | null;
  building_floors?: number | null;
  building_elevators?: number | null;
  year_of_completion: number | null;
  latitude: number | null;
  longitude: number | null;
  location_status: "exact" | "unavailable";
  source_url: string | null;
  source_name: string | null;
  observed_at: string | null;
  snapshot_id: string;
  dataset_snapshot_at: string;
  data_status: "listing_snapshot";
  fit_score: number | null;
  evidence_coverage: number | null;
  suitability: "suitable" | "conditional" | "excluded";
  evaluations: CriterionEvaluation[];
  matched_criteria: string[];
  conflicting_criteria: string[];
  unknown_criteria: string[];
  unsupported_criteria: string[];
};

export type TraceStep = { node: string; label: string; status: "started" | "completed"; duration_ms?: number };
export type SourceItem = { title: string; url: string; observed_at: string | null; kind: string };
export type Relaxation = { criterion_id: string; resulting_match_count: number };
export type RunStatus = "idle" | "interpreting" | "running" | "completed" | "failed" | "cancelled";
export type RunStats = { candidate_count: number; audited_count: number; total_matches: number; shown_count: number };
export type GuidanceReason = {
  property_id: string;
  code: "all_verifiable_criteria_matched" | "highest_fit" | "highest_evidence" | "lowest_price_tiebreak";
  criterion_ids: string[];
};
export type GuidanceCaveat = { property_id: string | null; criterion_id: string; status: "conflict" | "unknown" | "unsupported" };
export type PropertyGuidance = {
  version: 1;
  outcome: "matches" | "conditional" | "no_match";
  best_match_id: string | null;
  runner_up_id: string | null;
  reasons: GuidanceReason[];
  caveats: GuidanceCaveat[];
  next_action: "review_best_match" | "compare_matches" | "edit_brief";
};
export type PropertyEvent = RunStats & { properties: Property[] };
export type MarketContext = {
  area: string;
  matching_basis?: string[];
  record_count?: number;
  usable_record_count?: number;
  period_start?: string | null;
  period_end?: string | null;
  price_median?: number | null;
  price_q1?: number | null;
  price_q3?: number | null;
  evidence_quality: "strong" | "limited" | "insufficient";
  property_type_mix?: Record<string, number>;
  bedroom_mix?: Record<string, number>;
  unavailable?: boolean;
};

export type AffordabilityInput = {
  price: number;
  deposit: number;
  annualRate: number;
  years: number;
  transfer: number;
  finance: number;
  moving: number;
  annualService: number;
};
export type ScenarioForm = Record<"deposit" | "annualRate" | "years" | "transfer" | "finance" | "moving" | "annualService", string>;
