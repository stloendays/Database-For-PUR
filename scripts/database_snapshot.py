#!/usr/bin/env python3
"""Write a machine-readable snapshot for a built PUR SQLite database."""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

CORE_TABLES = [
    "sources", "experiments", "materials", "material_property_values", "formulations",
    "formulation_components", "process_steps", "measurements", "protocols", "patents",
    "evidence", "terminology", "viscosity_curves", "thesis_index", "standard_index",
    "batch_registry", "batch_records", "batch_record_values", "controlled_relations",
]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("database")
    ap.add_argument("--output", default="database/snapshot_v016.json")
    args = ap.parse_args()

    db = Path(args.database)
    out = Path(args.output)
    conn = sqlite3.connect(db)
    present = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    counts = {t: conn.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0] for t in CORE_TABLES if t in present}
    batches = [
        dict(zip(("batch_id", "status", "record_count", "source_count"), row))
        for row in conn.execute(
            "SELECT batch_id, integration_status, record_count, source_count FROM batch_registry ORDER BY batch_number"
        )
    ] if "batch_registry" in present else []
    integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
    fk_count = len(conn.execute("PRAGMA foreign_key_check").fetchall())
    conn.close()

    payload = {
        "schema_generation": "pur_cn_v1 + pur_staging_v016",
        "integrated_through": "BATCH_016",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "database_bytes": db.stat().st_size,
        "database_sha256": hashlib.sha256(db.read_bytes()).hexdigest(),
        "integrity_check": integrity,
        "foreign_key_violations": fk_count,
        "counts": counts,
        "batches": batches,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
