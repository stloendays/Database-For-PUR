#!/usr/bin/env python3
"""Build the unified PUR SQLite database from committed repository releases.

Current build layers:
  1. legacy source metadata from data/legacy/sources.csv
  2. legacy + Batch 005 relational payload from releases/pur_core_integration_v005.zip
  3. cumulative Chinese corpus from releases/cn_seed_batch_004.zip (or latest)
  4. terminology seed from data/master/terminology_seed.csv

Usage:
    python scripts/build_database.py --output database/pur_master.db
    python scripts/build_database.py --cn-release releases/cn_seed_batch_004.zip
    python scripts/build_database.py --integration-release releases/pur_core_integration_v005.zip
"""
from __future__ import annotations

import argparse
import csv
import gzip
import io
import sqlite3
import zipfile
from pathlib import Path
from typing import Iterable, Mapping

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schema" / "pur_cn_v1.sql"

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
    ("standard_index.csv", "standard_index"),
]

INTEGRATION_IMPORTS = [
    ("data/legacy/formulations.csv", "formulations"),
    ("data/legacy/formulation_components.csv", "formulation_components"),
    ("data/legacy/measurements.csv", "measurements"),
    ("data/legacy/protocols.csv", "protocols"),
    ("data/materials/sources.csv", "sources"),
    ("data/materials/materials.csv", "materials"),
    ("data/materials/material_property_values.csv", "material_property_values"),
    ("data/materials/experiments.csv", "experiments"),
    ("data/materials/formulations.csv", "formulations"),
    ("data/materials/formulation_components.csv", "formulation_components"),
    ("data/materials/process_steps.csv", "process_steps"),
    ("data/materials/measurements.csv", "measurements"),
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
    table_cols = {r[1] for r in conn.execute(f'PRAGMA table_info("{table}")')}
    cols = [c for c in (fieldnames or []) if c in table_cols]
    if not cols:
        return 0
    placeholders = ",".join("?" for _ in cols)
    quoted_cols = ",".join(f'"{c}"' for c in cols)
    sql = f'INSERT OR REPLACE INTO "{table}" ({quoted_cols}) VALUES ({placeholders})'
    conn.executemany(sql, [[row.get(c) or None for c in cols] for row in rows])
    return len(rows)


def import_csv(conn: sqlite3.Connection, path: Path, table: str) -> int:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        return import_rows(conn, reader.fieldnames, reader, table)


def import_zip_member(
    conn: sqlite3.Connection,
    zf: zipfile.ZipFile,
    member: str,
    table: str,
) -> int:
    with zf.open(member) as raw, io.TextIOWrapper(raw, encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        return import_rows(conn, reader.fieldnames, reader, table)


def import_zip_gzip_member(
    conn: sqlite3.Connection,
    zf: zipfile.ZipFile,
    member: str,
    table: str,
) -> int:
    with zf.open(member) as raw:
        with gzip.GzipFile(fileobj=raw, mode="rb") as gz:
            with io.TextIOWrapper(gz, encoding="utf-8-sig", newline="") as fh:
                reader = csv.DictReader(fh)
                return import_rows(conn, reader.fieldnames, reader, table)


def latest_release(pattern: str) -> Path | None:
    files = sorted((ROOT / "releases").glob(pattern))
    return files[-1] if files else None


def import_legacy_sources(conn: sqlite3.Connection, path: Path) -> int:
    """Normalize the original legacy source CSV into the current source schema."""
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        rows = []
        for row in csv.DictReader(fh):
            identifier = (row.get("doi_or_patent") or "").strip()
            source_type = (row.get("source_type") or "").strip()
            doi = identifier if identifier.startswith("10.") else ""
            patent_number = identifier if source_type == "patent" else ""
            notes = []
            if row.get("relevance"):
                notes.append(f"Relevance: {row['relevance']}")
            if identifier and not doi and not patent_number:
                notes.append(f"Legacy identifier: {identifier}")
            rows.append(
                {
                    "source_id": row.get("source_id"),
                    "source_type": source_type,
                    "title": row.get("title"),
                    "year": row.get("year"),
                    "doi": doi,
                    "patent_number": patent_number,
                    "publication_number": patent_number,
                    "journal_or_publisher": row.get("publisher"),
                    "license": row.get("license"),
                    "source_url": row.get("source_url"),
                    "notes": " | ".join(notes),
                }
            )
    return import_rows(conn, rows[0].keys() if rows else [], rows, "sources")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default="database/pur_master.db")
    ap.add_argument("--cn-release", default=None)
    ap.add_argument("--integration-release", default=None)
    args = ap.parse_args()

    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        output.unlink()

    cn_release = (
        ROOT / args.cn_release
        if args.cn_release
        else latest_release("cn_seed_batch_*.zip")
    )
    integration_release = (
        ROOT / args.integration_release
        if args.integration_release
        else latest_release("pur_core_integration_v*.zip")
    )
    for label, path in (("Chinese", cn_release), ("integration", integration_release)):
        if path is None or not path.exists():
            raise SystemExit(f"{label} release not found")

    conn = sqlite3.connect(output)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    total = 0

    n = import_legacy_sources(conn, ROOT / "data/legacy/sources.csv")
    total += n
    print(f"imported {n:>6} rows -> sources                  from data/legacy/sources.csv")

    # Legacy relational records must be loaded after their source identities.
    with zipfile.ZipFile(integration_release) as zf:
        members = set(zf.namelist())
        for member, table in INTEGRATION_IMPORTS[:4]:
            n = import_zip_member(conn, zf, member, table)
            total += n
            print(f"imported {n:>6} rows -> {table:<24} from {integration_release.name}::{member}")
        curve_member = "data/legacy/viscosity_curves.csv.gz"
        if curve_member not in members:
            raise SystemExit(f"missing {curve_member} in {integration_release}")
        n = import_zip_gzip_member(conn, zf, curve_member, "viscosity_curves")
        total += n
        print(f"imported {n:>6} rows -> {'viscosity_curves':<24} from {integration_release.name}::{curve_member}")

    # Always prefer the committed cumulative Chinese release over partial direct CSVs.
    with zipfile.ZipFile(cn_release) as zf:
        members = set(zf.namelist())
        for filename, table in CN_IMPORTS:
            member = f"data/cn/{filename}"
            if member not in members:
                continue
            n = import_zip_member(conn, zf, member, table)
            total += n
            print(f"imported {n:>6} rows -> {table:<24} from {cn_release.name}::{member}")

    # Batch 005 manufacturer/material records and controlled RHM benchmark.
    with zipfile.ZipFile(integration_release) as zf:
        for member, table in INTEGRATION_IMPORTS[4:]:
            n = import_zip_member(conn, zf, member, table)
            total += n
            print(f"imported {n:>6} rows -> {table:<24} from {integration_release.name}::{member}")

    terminology = ROOT / "data/master/terminology_seed.csv"
    if terminology.exists():
        n = import_csv(conn, terminology, "terminology")
        total += n
        print(f"imported {n:>6} rows -> terminology              from data/master/terminology_seed.csv")

    conn.commit()
    violations = conn.execute("PRAGMA foreign_key_check").fetchall()
    integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
    conn.close()

    if violations:
        raise SystemExit(f"foreign-key violations: {violations[:10]}")
    if integrity != "ok":
        raise SystemExit(f"integrity check failed: {integrity}")

    print(f"built {output.relative_to(ROOT)} with {total} imported rows")
    print(f"Chinese cumulative release: {cn_release.relative_to(ROOT)}")
    print(f"Integration release: {integration_release.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
