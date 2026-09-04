#!/usr/bin/env python3
"""Validation checks for Database-For-PUR."""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path


def fail(msg: str) -> None:
    print(f"ERROR: {msg}")
    raise SystemExit(1)


def main() -> None:
    if len(sys.argv) != 2:
        fail("usage: python scripts/validate_database.py database/pur_master.db")
    db = Path(sys.argv[1])
    if not db.exists():
        fail(f"database not found: {db}")

    conn = sqlite3.connect(db)
    fk = conn.execute("PRAGMA foreign_key_check").fetchall()
    if fk:
        fail(f"foreign-key violations: {fk[:10]}")

    required = {
        "sources", "experiments", "materials", "formulations",
        "formulation_components", "process_steps", "measurements",
        "evidence", "terminology", "viscosity_curves"
    }
    present = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    missing = required - present
    if missing:
        fail(f"missing tables: {sorted(missing)}")

    # Evidence policy: quantitative measurements should be attributable to a source.
    bad = conn.execute("""
        SELECT COUNT(*) FROM measurements
        WHERE source_id IS NULL OR trim(source_id)=''
    """).fetchone()[0]
    if bad:
        fail(f"measurements without source_id: {bad}")

    bad_levels = conn.execute("""
        SELECT COUNT(*) FROM measurements
        WHERE quality_level IS NOT NULL AND quality_level NOT IN ('A','B','C','D')
    """).fetchone()[0]
    if bad_levels:
        fail(f"invalid measurement quality levels: {bad_levels}")

    counts = {}
    for table in sorted(required):
        counts[table] = conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
    conn.close()

    print("PUR database validation: PASS")
    for table, n in counts.items():
        print(f"  {table:<24} {n}")


if __name__ == "__main__":
    main()
