#!/usr/bin/env python3
"""Build PUR master SQLite database from repository CSV files.

Usage:
    python scripts/build_database.py --output database/pur_master.db
"""
from __future__ import annotations

import argparse
import csv
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schema" / "pur_cn_v1.sql"


def import_csv(conn: sqlite3.Connection, csv_path: Path, table: str) -> int:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)
    if not rows:
        return 0

    table_cols = {
        row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()
    }
    cols = [c for c in reader.fieldnames or [] if c in table_cols]
    if not cols:
        return 0

    placeholders = ",".join("?" for _ in cols)
    quoted_cols = ",".join(f'"{c}"' for c in cols)
    sql = f'INSERT OR REPLACE INTO "{table}" ({quoted_cols}) VALUES ({placeholders})'
    conn.executemany(sql, [[row.get(c) or None for c in cols] for row in rows])
    return len(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default="database/pur_master.db")
    args = ap.parse_args()

    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        output.unlink()

    conn = sqlite3.connect(output)
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))

    imports = [
        (ROOT / "data" / "legacy" / "sources.csv", "sources"),
        (ROOT / "data" / "master" / "terminology_seed.csv", "terminology"),
        (ROOT / "data" / "cn" / "sources.csv", "sources"),
        (ROOT / "data" / "cn" / "experiments.csv", "experiments"),
        (ROOT / "data" / "cn" / "materials.csv", "materials"),
        (ROOT / "data" / "cn" / "formulations.csv", "formulations"),
        (ROOT / "data" / "cn" / "formulation_components.csv", "formulation_components"),
        (ROOT / "data" / "cn" / "process_steps.csv", "process_steps"),
        (ROOT / "data" / "cn" / "measurements.csv", "measurements"),
        (ROOT / "data" / "cn" / "evidence.csv", "evidence"),
    ]

    total = 0
    for path, table in imports:
        if path.exists():
            n = import_csv(conn, path, table)
            total += n
            print(f"imported {n:>6} rows -> {table:<24} from {path.relative_to(ROOT)}")

    conn.commit()
    conn.execute("PRAGMA foreign_key_check")
    conn.close()
    print(f"built {output.relative_to(ROOT)} with {total} imported CSV rows")


if __name__ == "__main__":
    main()
