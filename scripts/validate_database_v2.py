#!/usr/bin/env python3
"""Validation checks for Database-For-PUR v2."""
from __future__ import annotations

import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def fail(msg: str) -> None:
    print(f"ERROR: {msg}")
    raise SystemExit(1)


def scalar(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> int | float | str | None:
    row = conn.execute(sql, params).fetchone()
    return row[0] if row else None


def main() -> None:
    if len(sys.argv) != 2:
        fail("usage: python scripts/validate_database_v2.py database/pur_master_v2.db")
    db = Path(sys.argv[1])
    if not db.exists():
        fail(f"database not found: {db}")

    subprocess.run([sys.executable, str(ROOT / "scripts" / "validate_database.py"), str(db)], cwd=ROOT, check=True)

    conn = sqlite3.connect(db)
    integrity = scalar(conn, "PRAGMA integrity_check")
    if integrity != "ok":
        fail(f"integrity check failed: {integrity}")
    fk = conn.execute("PRAGMA foreign_key_check").fetchall()
    if fk:
        fail(f"foreign-key violations: {fk[:10]}")

    required = {
        "staging_batches", "staging_records", "paired_measurements", "controlled_contrasts",
        "controlled_contrast_outcomes", "series_definitions", "scientific_links",
        "record_equivalence", "decision_benchmarks", "decision_candidates",
    }
    present = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    missing = required - present
    if missing:
        fail(f"missing v2 tables: {sorted(missing)}")

    batches = int(scalar(conn, "SELECT COUNT(*) FROM staging_batches WHERE batch_id BETWEEN 6 AND 16") or 0)
    if batches != 11:
        fail(f"expected Batch 006-016 coverage (11 batches), found {batches}")

    staging = int(scalar(conn, "SELECT COUNT(*) FROM staging_records") or 0)
    if staging < 100:
        fail(f"staging ingestion suspiciously small: {staging} rows")

    pairs = int(scalar(conn, "SELECT COUNT(*) FROM paired_measurements") or 0)
    if pairs < 37:
        fail(f"expected at least 37 promoted precursor/product pairs, found {pairs}")
    same_temp = int(scalar(conn, "SELECT COUNT(*) FROM paired_measurements WHERE same_temperature=1") or 0)
    if same_temp < 15:
        fail(f"expected at least 15 same-temperature viscosity pairs, found {same_temp}")
    exact_blend = int(scalar(conn, """
        SELECT COUNT(*) FROM paired_measurements
        WHERE pair_type='polyol_blend_to_prepolymer'
          AND composition_match_class='exact_same_blend_same_temperature'
    """) or 0)
    if exact_blend != 3:
        fail(f"Batch 011 exact 50/50 blend series should have 3 rows, found {exact_blend}")

    contrasts = int(scalar(conn, "SELECT COUNT(*) FROM controlled_contrasts") or 0)
    if contrasts < 32:
        fail(f"expected at least 32 controlled contrasts, found {contrasts}")
    outcomes = int(scalar(conn, "SELECT COUNT(*) FROM controlled_contrast_outcomes") or 0)
    if outcomes < 40:
        fail(f"expected at least 40 contrast outcomes, found {outcomes}")

    equiv = int(scalar(conn, "SELECT COUNT(*) FROM record_equivalence") or 0)
    if equiv != 17:
        fail(f"Batch 015 family-overlap map should contain 17 rows, found {equiv}")
    wrong_action = int(scalar(conn, "SELECT COUNT(*) FROM record_equivalence WHERE action <> 'do_not_duplicate'") or 0)
    if wrong_action:
        fail(f"family duplicate map contains {wrong_action} non-dedup actions")

    benchmarks = int(scalar(conn, "SELECT COUNT(*) FROM decision_benchmarks") or 0)
    if benchmarks < 7:
        fail(f"expected at least 7 decision benchmarks, found {benchmarks}")
    candidate_rows = int(scalar(conn, "SELECT COUNT(*) FROM decision_candidates") or 0)
    if candidate_rows < 28:
        fail(f"expected at least 28 decision-candidate rows, found {candidate_rows}")

    gt = scalar(conn, "SELECT ground_truth_candidate_id FROM decision_benchmarks WHERE benchmark_id='B016_MAX_CROSSPEEL_5MIN'")
    if gt != "US20070155859_EX4":
        fail(f"5-min cross-peel ground truth should be EX4, found {gt}")
    gt20 = scalar(conn, "SELECT ground_truth_candidate_id FROM decision_benchmarks WHERE benchmark_id='B016_MAX_CROSSPEEL_20MIN'")
    if gt20 != "US20070155859_EX1":
        fail(f"20-min cross-peel ground truth should be EX1, found {gt20}")
    gtc = scalar(conn, "SELECT ground_truth_candidate_id FROM decision_benchmarks WHERE benchmark_id='B016_CONSTRAINED_5MIN_STRENGTH'")
    if gtc != "US20070155859_EX3":
        fail(f"constrained 5-min ground truth should be EX3, found {gtc}")

    duplicate_staging_ids = int(scalar(conn, """
        SELECT COUNT(*) FROM (
          SELECT staging_record_id, COUNT(*) n FROM staging_records GROUP BY staging_record_id HAVING n>1
        )
    """) or 0)
    if duplicate_staging_ids:
        fail(f"duplicate staging_record_id values: {duplicate_staging_ids}")

    print("PUR database v2 validation: PASS")
    print(f"  staging batches          {batches}")
    print(f"  staging rows             {staging}")
    print(f"  paired measurements      {pairs}")
    print(f"  same-temperature pairs   {same_temp}")
    print(f"  controlled contrasts     {contrasts}")
    print(f"  contrast outcomes        {outcomes}")
    print(f"  equivalence mappings     {equiv}")
    print(f"  decision benchmarks      {benchmarks}")
    print(f"  decision candidates      {candidate_rows}")
    conn.close()


if __name__ == "__main__":
    main()
