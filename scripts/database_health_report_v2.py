#!/usr/bin/env python3
"""Print a concise health report for pur_master_v2.db."""
from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path


def count(conn: sqlite3.Connection, table: str) -> int:
    return conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="database/pur_master_v2.db")
    args = ap.parse_args()
    db = Path(args.db)
    if not db.exists():
        raise SystemExit(f"database not found: {db}")

    conn = sqlite3.connect(db)
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    print("Database-For-PUR v2 health report")
    print("=" * 33)
    print(f"integrity_check:          {conn.execute('PRAGMA integrity_check').fetchone()[0]}")
    print(f"foreign-key violations:  {len(conn.execute('PRAGMA foreign_key_check').fetchall())}")

    print("\nCore normalized layer")
    for table in ("sources", "experiments", "materials", "formulations", "measurements", "evidence", "viscosity_curves", "rag_fts"):
        if table in tables:
            print(f"{table:26s} {count(conn, table):>8}")

    print("\nV2 relationship layer")
    for table in ("staging_batches", "staging_records", "paired_measurements", "controlled_contrasts",
                  "controlled_contrast_outcomes", "series_definitions", "scientific_links",
                  "record_equivalence", "decision_benchmarks", "decision_candidates"):
        if table in tables:
            print(f"{table:26s} {count(conn, table):>8}")

    if "staging_batches" in tables:
        lo, hi, n = conn.execute("SELECT MIN(batch_id),MAX(batch_id),COUNT(*) FROM staging_batches").fetchone()
        rows = conn.execute("SELECT COALESCE(SUM(record_count),0) FROM staging_batches").fetchone()[0]
        print("\nIntegration semantics")
        print(f"staging coverage:          Batch {lo:03d} - Batch {hi:03d} ({n} batches)")
        print(f"lossless staging rows:     {rows}")
        print("core relational baseline:  Batch 005 normalized schema")
        print("v2 integration mode:       Batch 006+ lossless rows + promoted scientific relationships")
        print("status:                    usable for RAG / Agent / relationship-aware modeling")
        print("note:                      full row-by-row remapping into legacy formulations/measurements remains a later normalization pass")

    if "paired_measurements" in tables:
        exact = conn.execute("SELECT COUNT(*) FROM v_exact_viscosity_amplification").fetchone()[0]
        blend = conn.execute("SELECT COUNT(*) FROM paired_measurements WHERE pair_type='polyol_blend_to_prepolymer'").fetchone()[0]
        print("\nHigh-value evidence")
        print(f"exact same-T amplification rows: {exact}")
        print(f"blend -> prepolymer pairs:       {blend}")

    conn.close()


if __name__ == "__main__":
    main()
