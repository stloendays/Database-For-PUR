PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS staging_batches (
  batch_id INTEGER PRIMARY KEY,
  batch_name TEXT NOT NULL,
  status TEXT NOT NULL,
  source_file_count INTEGER NOT NULL DEFAULT 0,
  record_count INTEGER NOT NULL DEFAULT 0,
  integrated_at TEXT,
  notes TEXT
);

CREATE TABLE IF NOT EXISTS staging_records (
  staging_record_id TEXT PRIMARY KEY,
  batch_id INTEGER NOT NULL REFERENCES staging_batches(batch_id),
  source_file TEXT NOT NULL,
  record_type TEXT NOT NULL,
  source_id TEXT,
  native_id TEXT,
  evidence_locator TEXT,
  quality_level TEXT,
  payload_json TEXT NOT NULL,
  UNIQUE(batch_id, source_file, staging_record_id)
);

CREATE TABLE IF NOT EXISTS paired_measurements (
  pair_id TEXT PRIMARY KEY,
  batch_id INTEGER NOT NULL REFERENCES staging_batches(batch_id),
  source_id TEXT,
  pair_type TEXT NOT NULL,
  series_id TEXT,
  precursor_id TEXT,
  product_id TEXT,
  precursor_stage TEXT,
  product_stage TEXT,
  property_name TEXT NOT NULL,
  precursor_value REAL,
  precursor_unit TEXT,
  precursor_temperature_c REAL,
  product_value REAL,
  product_unit TEXT,
  product_temperature_c REAL,
  same_temperature INTEGER CHECK (same_temperature IN (0,1) OR same_temperature IS NULL),
  composition_match_class TEXT,
  derived_ratio REAL,
  derivation_status TEXT,
  isocyanate TEXT,
  isocyanate_index REAL,
  target_nco_pct REAL,
  reaction_method_id TEXT,
  evidence_strength TEXT,
  evidence_locator TEXT,
  notes TEXT,
  payload_json TEXT
);

CREATE TABLE IF NOT EXISTS controlled_contrasts (
  contrast_id TEXT PRIMARY KEY,
  batch_id INTEGER NOT NULL REFERENCES staging_batches(batch_id),
  source_id TEXT,
  sample_a TEXT,
  sample_b TEXT,
  contrast_class TEXT,
  changed_factors TEXT,
  held_factors TEXT,
  evidence_strength TEXT,
  evidence_locator TEXT,
  notes TEXT,
  payload_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS controlled_contrast_outcomes (
  outcome_id TEXT PRIMARY KEY,
  contrast_id TEXT NOT NULL REFERENCES controlled_contrasts(contrast_id) ON DELETE CASCADE,
  metric_name TEXT NOT NULL,
  value_a REAL,
  value_b REAL,
  raw_a TEXT,
  raw_b TEXT,
  unit TEXT,
  delta_b_minus_a REAL,
  ratio_b_over_a REAL,
  temperature_c REAL,
  time_value REAL,
  time_unit TEXT,
  notes TEXT
);

CREATE TABLE IF NOT EXISTS series_definitions (
  series_id TEXT PRIMARY KEY,
  batch_id INTEGER NOT NULL REFERENCES staging_batches(batch_id),
  source_id TEXT,
  series_type TEXT NOT NULL,
  members_json TEXT NOT NULL,
  held_features TEXT,
  covarying_features TEXT,
  primary_outcomes TEXT,
  evidence_strength TEXT,
  notes TEXT,
  payload_json TEXT
);

CREATE TABLE IF NOT EXISTS scientific_links (
  link_id TEXT PRIMARY KEY,
  batch_id INTEGER NOT NULL REFERENCES staging_batches(batch_id),
  source_id TEXT,
  link_type TEXT NOT NULL,
  entity_a TEXT,
  entity_b TEXT,
  metric_a TEXT,
  metric_b TEXT,
  derived_value REAL,
  derived_semantics TEXT,
  evidence_strength TEXT,
  notes TEXT,
  payload_json TEXT
);

CREATE TABLE IF NOT EXISTS record_equivalence (
  equivalence_id TEXT PRIMARY KEY,
  batch_id INTEGER NOT NULL REFERENCES staging_batches(batch_id),
  source_id TEXT,
  source_record_id TEXT,
  canonical_source_id TEXT,
  canonical_record_id TEXT,
  overlap_status TEXT,
  matching_basis TEXT,
  action TEXT NOT NULL,
  payload_json TEXT
);

CREATE TABLE IF NOT EXISTS decision_benchmarks (
  benchmark_id TEXT PRIMARY KEY,
  batch_id INTEGER NOT NULL REFERENCES staging_batches(batch_id),
  source_id TEXT,
  title TEXT NOT NULL,
  task_type TEXT NOT NULL,
  objective_name TEXT NOT NULL,
  objective_direction TEXT CHECK (objective_direction IN ('maximize','minimize','target') OR objective_direction IS NULL),
  objective_unit TEXT,
  condition_json TEXT,
  constraints_json TEXT,
  candidate_scope TEXT,
  ground_truth_candidate_id TEXT,
  notes TEXT
);

CREATE TABLE IF NOT EXISTS decision_candidates (
  benchmark_id TEXT NOT NULL REFERENCES decision_benchmarks(benchmark_id) ON DELETE CASCADE,
  candidate_id TEXT NOT NULL,
  objective_value REAL,
  objective_raw TEXT,
  unit TEXT,
  feasible INTEGER CHECK (feasible IN (0,1) OR feasible IS NULL),
  rank INTEGER,
  is_optimal INTEGER NOT NULL DEFAULT 0 CHECK (is_optimal IN (0,1)),
  candidate_payload_json TEXT,
  PRIMARY KEY (benchmark_id, candidate_id)
);

CREATE INDEX IF NOT EXISTS idx_staging_batch ON staging_records(batch_id);
CREATE INDEX IF NOT EXISTS idx_staging_source ON staging_records(source_id);
CREATE INDEX IF NOT EXISTS idx_staging_type ON staging_records(record_type);
CREATE INDEX IF NOT EXISTS idx_pair_source ON paired_measurements(source_id);
CREATE INDEX IF NOT EXISTS idx_pair_type ON paired_measurements(pair_type);
CREATE INDEX IF NOT EXISTS idx_pair_same_temp ON paired_measurements(same_temperature);
CREATE INDEX IF NOT EXISTS idx_contrast_source ON controlled_contrasts(source_id);
CREATE INDEX IF NOT EXISTS idx_contrast_class ON controlled_contrasts(contrast_class);
CREATE INDEX IF NOT EXISTS idx_outcome_metric ON controlled_contrast_outcomes(metric_name);
CREATE INDEX IF NOT EXISTS idx_series_source ON series_definitions(source_id);
CREATE INDEX IF NOT EXISTS idx_link_type ON scientific_links(link_type);
CREATE INDEX IF NOT EXISTS idx_equiv_canonical ON record_equivalence(canonical_source_id, canonical_record_id);
CREATE INDEX IF NOT EXISTS idx_benchmark_objective ON decision_benchmarks(objective_name);
CREATE INDEX IF NOT EXISTS idx_candidate_optimal ON decision_candidates(is_optimal);

CREATE VIEW IF NOT EXISTS v_exact_viscosity_amplification AS
SELECT
  pair_id,
  batch_id,
  source_id,
  series_id,
  precursor_id,
  product_id,
  precursor_value,
  precursor_unit,
  precursor_temperature_c,
  product_value,
  product_unit,
  product_temperature_c,
  composition_match_class,
  derived_ratio,
  isocyanate,
  isocyanate_index,
  target_nco_pct,
  evidence_strength,
  evidence_locator
FROM paired_measurements
WHERE property_name = 'viscosity'
  AND same_temperature = 1
  AND derived_ratio IS NOT NULL
  AND (
    composition_match_class LIKE 'exact%'
    OR composition_match_class = 'single_polyol_same_temperature'
  );

CREATE VIEW IF NOT EXISTS v_decision_ground_truth AS
SELECT
  b.benchmark_id,
  b.title,
  b.objective_name,
  b.objective_direction,
  b.condition_json,
  b.constraints_json,
  c.candidate_id,
  c.objective_value,
  c.unit,
  c.feasible,
  c.rank,
  c.is_optimal
FROM decision_benchmarks b
JOIN decision_candidates c USING (benchmark_id);
