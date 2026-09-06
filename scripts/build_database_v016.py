#!/usr/bin/env python3
"""Build the cumulative PUR SQLite database through Batch 016.

This wrapper first reconstructs the verified Batch 005 canonical core with the
existing builder, then integrates every committed staging CSV from Batch
006 through Batch 016 using a lossless row/value layer plus conservative
projection into canonical sources, protocols, and recognized measurement
outcomes.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

from staging_sqlite import import_staging_batches

ROOT = Path(__file__).resolve().parents[1]
EXTENSION_SCHEMA = ROOT / "schema" / "pur_staging_v016.sql"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default="database/pur_master.db")
    ap.add_argument("--cn-release", default=None)
    ap.add_argument("--integration-release", default=None)
    ap.add_argument("--start-batch", type=int, default=6)
    ap.add_argument("--end-batch", type=int, default=16)
    args = ap.parse_args()

    if args.start_batch > args.end_batch:
        raise SystemExit("start batch must be <= end batch")

    core_cmd = [
        sys.executable,
        str(ROOT / "scripts" / "build_database.py"),
        "--output",
        args.output,
    ]
    if args.cn_release:
        core_cmd.extend(["--cn-release", args.cn_release])
    if args.integration_release:
        core_cmd.extend(["--integration-release", args.integration_release])

    print("building verified Batch 005 canonical core...")
    subprocess.run(core_cmd, cwd=ROOT, check=True)

    output = ROOT / args.output
    conn = sqlite3.connect(output)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(EXTENSION_SCHEMA.read_text(encoding="utf-8"))

    stats = import_staging_batches(
        conn,
        ROOT,
        start_batch=args.start_batch,
        end_batch=args.end_batch,
    )

    conn.execute("DELETE FROM rag_fts WHERE doc_type = 'batch_record'")
    rows = conn.execute(
        """SELECT batch_record_id, source_id, file_name, payload_json,
                  batch_id, record_type, entity_key, evidence_locator
           FROM batch_records
           ORDER BY batch_id, file_name, row_number"""
    ).fetchall()
    for record_id, source_id, file_name, payload, batch_id, record_type, entity_key, evidence_locator in rows:
        metadata = json.dumps(
            {
                "batch_id": batch_id,
                "record_type": record_type,
                "entity_key": entity_key,
                "evidence_locator": evidence_locator,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
        conn.execute(
            """INSERT INTO rag_fts(document_id, source_id, doc_type, title, content, metadata_json)
               VALUES (?,?,?,?,?,?)""",
            (record_id, source_id, "batch_record", file_name, payload, metadata),
        )

    conn.commit()
    violations = conn.execute("PRAGMA foreign_key_check").fetchall()
    integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
    batch_records = conn.execute("SELECT COUNT(*) FROM batch_records").fetchone()[0]
    batch_values = conn.execute("SELECT COUNT(*) FROM batch_record_values").fetchone()[0]
    relations = conn.execute("SELECT COUNT(*) FROM controlled_relations").fetchone()[0]
    fts_batch = conn.execute("SELECT COUNT(*) FROM rag_fts WHERE doc_type='batch_record'").fetchone()[0]
    conn.close()

    if violations:
        raise SystemExit(f"foreign-key violations after staging integration: {violations[:10]}")
    if integrity != "ok":
        raise SystemExit(f"integrity check failed after staging integration: {integrity}")
    if fts_batch != batch_records:
        raise SystemExit(f"FTS batch-record mismatch: {fts_batch} != {batch_records}")

    print("staging integration complete")
    print(f"  batches          {args.start_batch:03d}-{args.end_batch:03d}")
    print(f"  batch records    {batch_records}")
    print(f"  field values     {batch_values}")
    print(f"  relations        {relations}")
    print(f"  FTS batch docs   {fts_batch}")
    print("STAGING_STATS_JSON=" + json.dumps(stats, sort_keys=True))
    print(f"built cumulative SQLite: {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
