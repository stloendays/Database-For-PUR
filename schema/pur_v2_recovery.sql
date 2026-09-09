PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS data_recovery_status (
  recovery_id TEXT PRIMARY KEY,
  layer TEXT NOT NULL,
  source_release TEXT,
  table_name TEXT NOT NULL,
  documented_rows INTEGER,
  operational_rows INTEGER,
  missing_rows INTEGER,
  status TEXT NOT NULL,
  policy TEXT,
  integrated_at TEXT NOT NULL,
  UNIQUE(layer, table_name),
  CHECK (missing_rows IS NULL OR missing_rows >= 0)
);

CREATE INDEX IF NOT EXISTS idx_recovery_layer
  ON data_recovery_status(layer);
CREATE INDEX IF NOT EXISTS idx_recovery_status
  ON data_recovery_status(status);
CREATE INDEX IF NOT EXISTS idx_recovery_missing
  ON data_recovery_status(missing_rows);

CREATE VIEW IF NOT EXISTS v_data_quality_deficits AS
SELECT
  recovery_id,
  layer,
  source_release,
  table_name,
  documented_rows,
  operational_rows,
  missing_rows,
  status,
  policy,
  integrated_at
FROM data_recovery_status
WHERE COALESCE(missing_rows, 0) > 0;
