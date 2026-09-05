#!/usr/bin/env python3
"""Validation checks for the unified Database-For-PUR build."""
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
    integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
    if integrity != "ok":
        fail(f"integrity check failed: {integrity}")

    fk = conn.execute("PRAGMA foreign_key_check").fetchall()
    if fk:
        fail(f"foreign-key violations: {fk[:10]}")

    required = {
        "sources", "experiments", "materials", "material_property_values",
        "formulations", "formulation_components", "process_steps", "measurements",
        "protocols", "patents", "evidence", "terminology", "viscosity_curves",
        "thesis_index", "standard_index", "rag_fts",
    }
    present = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    missing = required - present
    if missing:
        fail(f"missing tables: {sorted(missing)}")

    counts = {table: conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
              for table in sorted(required - {"rag_fts"})}

    if counts["viscosity_curves"] != 4559:
        fail(f"expected 4559 migrated viscosity points, found {counts['viscosity_curves']}")
    if counts["material_property_values"] < 200:
        fail("Batch 005 material property layer appears incomplete")
    if counts["sources"] < 66 or counts["materials"] < 37 or counts["measurements"] < 795:
        fail("unified integration counts are below the verified Batch 005 baseline")

    conn.close()
    print("PUR database validation: PASS")
    print("  integrity_check           ok")
    print("  foreign_key_violations    0")
    for table, n in counts.items():
        print(f"  {table:<26} {n}")


if __name__ == "__main__":
    main()
