PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS batch_registry (
  batch_id TEXT PRIMARY KEY,
  batch_number INTEGER NOT NULL UNIQUE,
  integration_status TEXT NOT NULL,
  document_path TEXT,
  record_count INTEGER NOT NULL DEFAULT 0,
  source_count INTEGER NOT NULL DEFAULT 0,
  integrated_date TEXT,
  notes TEXT
);

CREATE TABLE IF NOT EXISTS batch_records (
  batch_record_id TEXT PRIMARY KEY,
  batch_id TEXT NOT NULL REFERENCES batch_registry(batch_id),
  source_id TEXT REFERENCES sources(source_id),
  file_name TEXT NOT NULL,
  record_type TEXT NOT NULL,
  row_number INTEGER NOT NULL,
  entity_key TEXT,
  evidence_locator TEXT,
  payload_json TEXT NOT NULL,
  payload_sha256 TEXT NOT NULL,
  UNIQUE(batch_id, file_name, row_number)
);

CREATE TABLE IF NOT EXISTS batch_record_values (
  batch_record_id TEXT NOT NULL REFERENCES batch_records(batch_record_id) ON DELETE CASCADE,
  field_name TEXT NOT NULL,
  value_text TEXT NOT NULL,
  numeric_value REAL,
  qualifier TEXT,
  PRIMARY KEY(batch_record_id, field_name)
);

CREATE TABLE IF NOT EXISTS controlled_relations (
  relation_id TEXT PRIMARY KEY,
  batch_id TEXT NOT NULL REFERENCES batch_registry(batch_id),
  source_id TEXT REFERENCES sources(source_id),
  relation_type TEXT NOT NULL,
  members_json TEXT,
  evidence_strength TEXT,
  evidence_locator TEXT,
  payload_json TEXT NOT NULL,
  notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_batch_registry_number ON batch_registry(batch_number);
CREATE INDEX IF NOT EXISTS idx_batch_records_batch ON batch_records(batch_id);
CREATE INDEX IF NOT EXISTS idx_batch_records_source ON batch_records(source_id);
CREATE INDEX IF NOT EXISTS idx_batch_records_file ON batch_records(file_name);
CREATE INDEX IF NOT EXISTS idx_batch_records_type ON batch_records(record_type);
CREATE INDEX IF NOT EXISTS idx_batch_values_field ON batch_record_values(field_name);
CREATE INDEX IF NOT EXISTS idx_batch_values_numeric ON batch_record_values(field_name, numeric_value);
CREATE INDEX IF NOT EXISTS idx_controlled_relations_batch ON controlled_relations(batch_id);
CREATE INDEX IF NOT EXISTS idx_controlled_relations_source ON controlled_relations(source_id);
CREATE INDEX IF NOT EXISTS idx_controlled_relations_type ON controlled_relations(relation_type);

CREATE VIEW IF NOT EXISTS batch_numeric_values AS
SELECT
  r.batch_id,
  r.source_id,
  r.file_name,
  r.record_type,
  r.entity_key,
  r.evidence_locator,
  v.field_name,
  v.numeric_value,
  v.qualifier,
  v.value_text
FROM batch_records r
JOIN batch_record_values v ON v.batch_record_id = r.batch_record_id
WHERE v.numeric_value IS NOT NULL;
