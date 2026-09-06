#!/usr/bin/env python3
"""Validation for the cumulative Database-For-PUR SQLite build through Batch 016."""
from __future__ import annotations

import csv
import hashlib
import json
import re
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BATCH_RE = re.compile(r"batch(?P<num>\d{3})", re.IGNORECASE)
RELATION_HINTS = ("contrast", "series", "pair", "amplification", "link", "overlap", "audit")
START_BATCH = 6
END_BATCH = 16


def fail(msg: str) -> None:
    print(f"ERROR: {msg}")
    raise SystemExit(1)


def staging_files() -> list[tuple[int, Path]]:
    out = []
    for path in sorted((ROOT / "data" / "materials").glob("*.csv")):
        m = BATCH_RE.search(path.name)
        if not m:
            continue
        num = int(m.group("num"))
        if START_BATCH <= num <= END_BATCH:
            out.append((num, path))
    return out


def csv_row_count(path: Path) -> int:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return sum(1 for _ in csv.DictReader(fh))


def main() -> None:
    if len(sys.argv) != 2:
        fail("usage: python scripts/validate_database_v016.py database/pur_master.db")
    db = Path(sys.argv[1])
    if not db.is_absolute():
        db = ROOT / db
    if not db.exists():
        fail(f"database not found: {db}")

    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate_database.py"), str(db)],
        cwd=ROOT,
        check=True,
    )

    conn = sqlite3.connect(db)
    conn.execute("PRAGMA foreign_keys = ON")
    required = {"batch_registry", "batch_records", "batch_record_values", "controlled_relations"}
    present = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    missing = required - present
    if missing:
        fail(f"missing Batch 006-016 integration tables: {sorted(missing)}")

    files = staging_files()
    if not files:
        fail("no Batch 006-016 staging CSV files discovered")

    expected_total = sum(csv_row_count(path) for _, path in files)
    actual_total = conn.execute("SELECT COUNT(*) FROM batch_records").fetchone()[0]
    if actual_total != expected_total:
        fail(f"lossless row-count mismatch: SQLite {actual_total}, committed CSVs {expected_total}")

    expected_files = {path.name for _, path in files}
    actual_files = {r[0] for r in conn.execute("SELECT DISTINCT file_name FROM batch_records")}
    if actual_files != expected_files:
        fail(f"staging file coverage mismatch: missing={sorted(expected_files-actual_files)}, extra={sorted(actual_files-expected_files)}")

    for num in range(START_BATCH, END_BATCH + 1):
        batch_id = f"BATCH_{num:03d}"
        expected = sum(csv_row_count(path) for n, path in files if n == num)
        row = conn.execute(
            "SELECT integration_status, record_count FROM batch_registry WHERE batch_id=?",
            (batch_id,),
        ).fetchone()
        if row is None:
            fail(f"missing batch registry row: {batch_id}")
        status, record_count = row
        if status != "integrated_lossless_plus_canonical":
            fail(f"unexpected integration status for {batch_id}: {status}")
        if record_count != expected:
            fail(f"registry row count mismatch for {batch_id}: {record_count} != {expected}")

    expected_relations = sum(
        csv_row_count(path)
        for _, path in files
        if any(h in path.name.lower() for h in RELATION_HINTS)
    )
    actual_relations = conn.execute("SELECT COUNT(*) FROM controlled_relations").fetchone()[0]
    if actual_relations != expected_relations:
        fail(f"controlled relation count mismatch: {actual_relations} != {expected_relations}")

    for record_id, payload, payload_sha in conn.execute(
        "SELECT batch_record_id, payload_json, payload_sha256 FROM batch_records"
    ):
        if hashlib.sha256(payload.encode("utf-8")).hexdigest() != payload_sha:
            fail(f"payload hash mismatch: {record_id}")
        obj = json.loads(payload)
        expected_values = sum(1 for v in obj.values() if str(v).strip() != "")
        actual_values = conn.execute(
            "SELECT COUNT(*) FROM batch_record_values WHERE batch_record_id=?", (record_id,)
        ).fetchone()[0]
        if actual_values != expected_values:
            fail(f"field preservation mismatch for {record_id}: {actual_values} != {expected_values}")

    fts_count = conn.execute("SELECT COUNT(*) FROM rag_fts WHERE doc_type='batch_record'").fetchone()[0]
    if fts_count != actual_total:
        fail(f"FTS coverage mismatch: {fts_count} != {actual_total}")

    source_ids = set()
    for _, path in files:
        if "sources" not in path.name.lower():
            continue
        with path.open("r", encoding="utf-8-sig", newline="") as fh:
            for row in csv.DictReader(fh):
                if row.get("source_id"):
                    source_ids.add(row["source_id"])
    missing_sources = [sid for sid in sorted(source_ids) if conn.execute("SELECT 1 FROM sources WHERE source_id=?", (sid,)).fetchone() is None]
    if missing_sources:
        fail(f"registered staging sources missing from canonical sources: {missing_sources[:20]}")

    projected_measurements = conn.execute(
        "SELECT COUNT(*) FROM measurements WHERE extraction_method='staging_csv_lossless_import'"
    ).fetchone()[0]
    if projected_measurements == 0:
        fail("no staging outcome fields were projected into canonical measurements")

    integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
    fk = conn.execute("PRAGMA foreign_key_check").fetchall()
    if integrity != "ok" or fk:
        fail(f"post-integration database check failed: integrity={integrity}, fk={fk[:10]}")

    counts = {
        "sources": conn.execute("SELECT COUNT(*) FROM sources").fetchone()[0],
        "materials": conn.execute("SELECT COUNT(*) FROM materials").fetchone()[0],
        "formulations": conn.execute("SELECT COUNT(*) FROM formulations").fetchone()[0],
        "measurements": conn.execute("SELECT COUNT(*) FROM measurements").fetchone()[0],
        "protocols": conn.execute("SELECT COUNT(*) FROM protocols").fetchone()[0],
        "batch_records": actual_total,
        "batch_record_values": conn.execute("SELECT COUNT(*) FROM batch_record_values").fetchone()[0],
        "controlled_relations": actual_relations,
        "staging_measurements": projected_measurements,
    }
    conn.close()

    print("PUR cumulative database validation through Batch 016: PASS")
    print("  committed staging files  ", len(expected_files))
    print("  integrated batches        11 (006-016)")
    for key, value in counts.items():
        print(f"  {key:<24} {value}")
    print("DATABASE_COUNTS_JSON=" + json.dumps(counts, sort_keys=True))


if __name__ == "__main__":
    main()
