PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS sources (
  source_id TEXT PRIMARY KEY,
  source_type TEXT NOT NULL,
  title TEXT NOT NULL,
  title_en TEXT,
  authors TEXT,
  institution TEXT,
  journal_or_publisher TEXT,
  year INTEGER,
  language TEXT,
  doi TEXT,
  patent_number TEXT,
  publication_number TEXT,
  standard_number TEXT,
  source_url TEXT,
  local_source_path TEXT,
  license TEXT,
  access_date TEXT,
  quality_level TEXT CHECK (quality_level IN ('A','B','C','D') OR quality_level IS NULL),
  extraction_status TEXT,
  notes TEXT
);

CREATE TABLE IF NOT EXISTS experiments (
  experiment_id TEXT PRIMARY KEY,
  source_id TEXT NOT NULL REFERENCES sources(source_id),
  experiment_number TEXT,
  sample_id TEXT,
  example_number TEXT,
  sample_type TEXT CHECK (sample_type IN ('sample','example','comparative_example','control','reference','unknown') OR sample_type IS NULL),
  description TEXT,
  evidence_locator TEXT,
  page TEXT,
  table_id TEXT,
  figure_id TEXT,
  quality_level TEXT CHECK (quality_level IN ('A','B','C','D') OR quality_level IS NULL),
  notes TEXT
);

CREATE TABLE IF NOT EXISTS materials (
  material_id TEXT PRIMARY KEY,
  normalized_name TEXT NOT NULL,
  name_zh TEXT,
  name_en TEXT,
  chemical_name TEXT,
  cas_number TEXT,
  category TEXT,
  subcategory TEXT,
  supplier TEXT,
  grade TEXT,
  molecular_weight_g_mol REAL,
  mn_g_mol REAL,
  mw_g_mol REAL,
  functionality REAL,
  oh_value_mg_koh_g REAL,
  nco_pct REAL,
  acid_value_mg_koh_g REAL,
  water_content_pct REAL,
  melting_point_c REAL,
  tg_c REAL,
  viscosity_value REAL,
  viscosity_unit TEXT,
  viscosity_temperature_c REAL,
  density_g_cm3 REAL,
  aromatic_fraction REAL,
  aliphatic_fraction REAL,
  source_id TEXT REFERENCES sources(source_id),
  notes TEXT
);

CREATE TABLE IF NOT EXISTS material_aliases (
  alias_id INTEGER PRIMARY KEY AUTOINCREMENT,
  material_id TEXT NOT NULL REFERENCES materials(material_id),
  alias TEXT NOT NULL,
  language TEXT,
  supplier TEXT,
  grade TEXT,
  UNIQUE(material_id, alias)
);

CREATE TABLE IF NOT EXISTS formulations (
  formulation_id TEXT PRIMARY KEY,
  experiment_id TEXT REFERENCES experiments(experiment_id),
  source_id TEXT NOT NULL REFERENCES sources(source_id),
  sample_id TEXT,
  material_class TEXT,
  application TEXT,
  formulation_basis TEXT,
  total_reported_amount REAL,
  total_unit TEXT,
  nco_oh_index REAL,
  target_nco_pct REAL,
  actual_nco_pct REAL,
  curing_type TEXT,
  composition_completeness TEXT,
  evidence_locator TEXT,
  source_url TEXT,
  notes TEXT
);

CREATE TABLE IF NOT EXISTS formulation_components (
  component_record_id TEXT PRIMARY KEY,
  formulation_id TEXT NOT NULL REFERENCES formulations(formulation_id),
  material_id TEXT REFERENCES materials(material_id),
  component_name_raw TEXT NOT NULL,
  component_name_normalized TEXT,
  role TEXT,
  amount REAL,
  unit TEXT,
  amount_basis TEXT,
  wt_pct REAL,
  mol REAL,
  equivalent REAL,
  molecular_weight_g_mol REAL,
  functionality REAL,
  oh_value_mg_koh_g REAL,
  nco_pct REAL,
  renewable_content_pct REAL,
  evidence_locator TEXT,
  notes TEXT
);

CREATE TABLE IF NOT EXISTS process_steps (
  process_step_id TEXT PRIMARY KEY,
  experiment_id TEXT REFERENCES experiments(experiment_id),
  formulation_id TEXT REFERENCES formulations(formulation_id),
  step_no INTEGER,
  operation TEXT NOT NULL,
  temperature_c REAL,
  time_value REAL,
  time_unit TEXT,
  pressure_kpa REAL,
  vacuum_mpa REAL,
  rpm REAL,
  atmosphere TEXT,
  addition_order TEXT,
  endpoint TEXT,
  water_content_pct REAL,
  evidence_locator TEXT,
  notes TEXT
);

CREATE TABLE IF NOT EXISTS measurements (
  measurement_id TEXT PRIMARY KEY,
  experiment_id TEXT REFERENCES experiments(experiment_id),
  formulation_id TEXT REFERENCES formulations(formulation_id),
  source_id TEXT NOT NULL REFERENCES sources(source_id),
  sample_id TEXT,
  measurement_stage TEXT CHECK (measurement_stage IN ('raw_material','polyol_blend','pre_reaction','during_reaction','prepolymer','hot_melt','cured_1d','cured_3d','cured_7d','cured_other','unknown') OR measurement_stage IS NULL),
  property_name_raw TEXT,
  property_name_normalized TEXT NOT NULL,
  value REAL,
  qualifier TEXT,
  value_min REAL,
  value_max REAL,
  uncertainty REAL,
  unit TEXT,
  original_value TEXT,
  original_unit TEXT,
  temperature_c REAL,
  temperature_min_c REAL,
  temperature_max_c REAL,
  time_value REAL,
  time_unit TEXT,
  humidity_pct REAL,
  condition TEXT,
  method_or_standard TEXT,
  substrate_1 TEXT,
  substrate_2 TEXT,
  failure_mode TEXT,
  n_replicates INTEGER,
  evidence_type TEXT CHECK (evidence_type IN ('measured','example','comparative_example','reported','recommended_range','claimed_range','inferred','digitized_from_figure','unknown') OR evidence_type IS NULL),
  evidence_locator TEXT,
  extraction_method TEXT,
  quality_level TEXT CHECK (quality_level IN ('A','B','C','D') OR quality_level IS NULL),
  source_url TEXT,
  notes TEXT
);

CREATE TABLE IF NOT EXISTS protocols (
  protocol_id TEXT PRIMARY KEY,
  source_id TEXT NOT NULL REFERENCES sources(source_id),
  protocol_type TEXT,
  method_standard TEXT,
  parameters_json TEXT,
  substrate_1 TEXT,
  substrate_2 TEXT,
  evidence_locator TEXT,
  source_url TEXT,
  notes TEXT
);

CREATE TABLE IF NOT EXISTS patents (
  patent_id TEXT PRIMARY KEY,
  source_id TEXT NOT NULL REFERENCES sources(source_id),
  application_number TEXT,
  publication_number TEXT,
  grant_number TEXT,
  priority_date TEXT,
  filing_date TEXT,
  publication_date TEXT,
  applicant TEXT,
  inventors TEXT,
  family_id TEXT,
  jurisdiction TEXT,
  notes TEXT
);

CREATE TABLE IF NOT EXISTS terminology (
  term_id TEXT PRIMARY KEY,
  raw_term TEXT NOT NULL,
  normalized_term TEXT NOT NULL,
  english_term TEXT,
  category TEXT,
  language TEXT DEFAULT 'zh',
  notes TEXT
);

CREATE TABLE IF NOT EXISTS evidence (
  evidence_id TEXT PRIMARY KEY,
  source_id TEXT NOT NULL REFERENCES sources(source_id),
  experiment_id TEXT REFERENCES experiments(experiment_id),
  entity_type TEXT,
  entity_id TEXT,
  evidence_type TEXT,
  evidence_locator TEXT,
  excerpt TEXT,
  source_url TEXT,
  local_source_path TEXT,
  quality_level TEXT CHECK (quality_level IN ('A','B','C','D') OR quality_level IS NULL),
  extraction_method TEXT,
  verified INTEGER DEFAULT 0 CHECK (verified IN (0,1)),
  notes TEXT
);

CREATE TABLE IF NOT EXISTS viscosity_curves (
  viscosity_point_id INTEGER PRIMARY KEY AUTOINCREMENT,
  source_id TEXT NOT NULL REFERENCES sources(source_id),
  experiment_id TEXT REFERENCES experiments(experiment_id),
  formulation_id TEXT REFERENCES formulations(formulation_id),
  sample_id TEXT,
  measurement_stage TEXT,
  polyol_code TEXT,
  isocyanate_code TEXT,
  pnco_pct REAL,
  sequence_index INTEGER,
  temperature_c REAL NOT NULL,
  viscosity_pa_s REAL NOT NULL,
  evidence_locator TEXT,
  source_url TEXT,
  notes TEXT
);

CREATE VIRTUAL TABLE IF NOT EXISTS rag_fts USING fts5(
  document_id UNINDEXED,
  source_id UNINDEXED,
  doc_type,
  title,
  content,
  metadata_json UNINDEXED,
  tokenize='unicode61'
);

CREATE INDEX IF NOT EXISTS idx_formulations_source ON formulations(source_id);
CREATE INDEX IF NOT EXISTS idx_components_formulation ON formulation_components(formulation_id);
CREATE INDEX IF NOT EXISTS idx_measurements_property ON measurements(property_name_normalized);
CREATE INDEX IF NOT EXISTS idx_measurements_source ON measurements(source_id);
CREATE INDEX IF NOT EXISTS idx_measurements_stage ON measurements(measurement_stage);
CREATE INDEX IF NOT EXISTS idx_process_formulation ON process_steps(formulation_id);
CREATE INDEX IF NOT EXISTS idx_viscosity_temp ON viscosity_curves(temperature_c);
CREATE INDEX IF NOT EXISTS idx_viscosity_source ON viscosity_curves(source_id);
CREATE INDEX IF NOT EXISTS idx_evidence_source ON evidence(source_id);
