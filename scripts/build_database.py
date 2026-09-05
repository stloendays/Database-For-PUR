#!/usr/bin/env python3
"""Build the PUR master SQLite database from repository data.

The builder prefers transparent CSV files under ``data/cn``.  For tables that
are not checked into the source tree individually, it falls back to the latest
``releases/cn_seed_batch_*.zip`` cumulative release.  This keeps the repository
small while preserving a one-command, reproducible database build.

Usage:
    python scripts/build_database.py --output database/pur_master.db
    python scripts/build_database.py --cn-release releases/cn_seed_batch_003.zip
"""
from __future__ import annotations

import argparse
import csv
import io
import sqlite3
import zipfile
from pathlib import Path
from typing import Iterable, Mapping

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schema" / "pur_cn_v1.sql"

THESIS_SCHEMA = """
CREATE TABLE IF NOT EXISTS thesis_index (
  source_id TEXT PRIMARY KEY REFERENCES sources(source_id),
  author TEXT,
  title TEXT NOT NULL,
  institution TEXT,
  year INTEGER,
  degree TEXT,
  verification_basis TEXT,
  verification_url TEXT,
  fulltext_status TEXT,
  priority TEXT,
  notes TEXT
);
CREATE INDEX IF NOT EXISTS idx_thesis_fulltext_status
  ON thesis_index(fulltext_status);
CREATE INDEX IF NOT EXISTS idx_thesis_priority
  ON thesis_index(priority);
"""

CN_IMPORTS = [
    ("sources.csv", "sources"),
    ("experiments.csv", "experiments"),
    ("materials.csv", "materials"),
    ("formulations.csv", "formulations"),
    ("formulation_components.csv", "formulation_components"),
    ("process_steps.csv", "process_steps"),
    ("measurements.csv", "measurements"),
    ("protocols.csv", "protocols"),
    ("patents.csv", "patents"),
    ("evidence.csv", "evidence"),
    ("thesis_index.csv", "thesis_index"),
]


def import_rows(
    conn: sqlite3.Connection,
    fieldnames: Iterable[str] | None,
    rows: Iterable[Mapping[str, str]],
    table: str,
) -> int:
    rows = list(rows)
    if not rows:
        return 0

    table_cols = {
        row[1] for row in conn.execute(f'PRAGMA table_info("{table}")').fetchall()
    }
    cols = [c for c in (fieldnames or []) if c in table_cols]
    if not cols:
        return 0

    placeholders = ",".join("?" for _ in cols)
    quoted_cols = ",".join(f'"{c}"' for c in cols)
    sql = f'INSERT OR REPLACE INTO "{table}" ({quoted_cols}) VALUES ({placeholders})'
    conn.executemany(sql, [[row.get(c) or None for c in cols] for row in rows])
    return len(rows)


def import_csv(conn: sqlite3.Connection, csv_path: Path, table: str) -> int:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        return import_rows(conn, reader.fieldnames, reader, table)


def import_zip_csv(
    conn: sqlite3.Connection,
    zf: zipfile.ZipFile,
    filename: str,
    table: str,
) -> int | None:
    members = set(zf.namelist())
    for member in (f"data/cn/{filename}", filename):
        if member not in members:
            continue
        with zf.open(member, "r") as raw:
            with io.TextIOWrapper(raw, encoding="utf-8-sig", newline="") as fh:
                reader = csv.DictReader(fh)
                return import_rows(conn, reader.fieldnames, reader, table)
    return None


def latest_cn_release() -> Path | None:
    releases = sorted((ROOT / "releases").glob("cn_seed_batch_*.zip"))
    return releases[-1] if releases else None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default="database/pur_master.db")
    ap.add_argument(
        "--cn-release",
        default=None,
        help="optional cumulative Chinese release ZIP; defaults to latest cn_seed_batch_*.zip",
    )
    args = ap.parse_args()

    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        output.unlink()

    release = ROOT / args.cn_release if args.cn_release else latest_cn_release()
    if release is not None and not release.exists():
        raise SystemExit(f"Chinese release not found: {release}")

    conn = sqlite3.connect(output)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.executescript(THESIS_SCHEMA)

    total = 0
    base_imports = [
        (ROOT / "data" / "legacy" / "sources.csv", "sources"),
        (ROOT / "data" / "master" / "terminology_seed.csv", "terminology"),
    ]
    for path, table in base_imports:
        if path.exists():
            n = import_csv(conn, path, table)
            total += n
            print(f"imported {n:>6} rows -> {table:<24} from {path.relative_to(ROOT)}")

    zf = zipfile.ZipFile(release, "r") if release is not None else None
    try:
        for filename, table in CN_IMPORTS:
            direct = ROOT / "data" / "cn" / filename
            if direct.exists():
                n = import_csv(conn, direct, table)
                source_label = str(direct.relative_to(ROOT))
            elif zf is not None:
                imported = import_zip_csv(conn, zf, filename, table)
                if imported is None:
                    continue
                n = imported
                source_label = f"{release.relative_to(ROOT)}::{filename}"
            else:
                continue
            total += n
            print(f"imported {n:>6} rows -> {table:<24} from {source_label}")
    finally:
        if zf is not None:
            zf.close()

    conn.commit()
    violations = conn.execute("PRAGMA foreign_key_check").fetchall()
    if violations:
        conn.close()
        raise SystemExit(f"foreign-key violations: {violations[:10]}")

    conn.close()
    print(f"built {output.relative_to(ROOT)} with {total} imported rows")
    if release is not None:
        print(f"Chinese cumulative release: {release.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
