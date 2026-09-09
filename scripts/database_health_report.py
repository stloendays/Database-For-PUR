#!/usr/bin/env python3
"""Report cumulative-build health and staged-batch integration lag."""
from __future__ import annotations

import argparse
import csv
import json
import re
import sqlite3
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BATCH_RE = re.compile(r"BATCH_(\d+)\.md$")
CSV_BATCH_RE = re.compile(r"batch(\d+)", re.IGNORECASE)


def count_csv_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.reader(fh)
        try:
            next(reader)
        except StopIteration:
            return 0
        return sum(1 for _ in reader)


def scan_staging() -> dict:
    material_dir = ROOT / "data" / "materials"
    docs: dict[int, str] = {}
    for path in material_dir.glob("BATCH_*.md"):
        match = BATCH_RE.search(path.name)
        if match:
            docs[int(match.group(1))] = str(path.relative_to(ROOT))

    rows_by_batch: dict[int, int] = defaultdict(int)
    files_by_batch: dict[int, list[str]] = defaultdict(list)
    for path in material_dir.glob("*.csv"):
        match = CSV_BATCH_RE.search(path.name)
        if not match:
            continue
        batch = int(match.group(1))
        rows_by_batch[batch] += count_csv_rows(path)
        files_by_batch[batch].append(str(path.relative_to(ROOT)))

    latest = max(docs, default=None)
    staged = sorted(b for b in docs if b >= 6)
    return {
        "latest_documented_batch": latest,
        "staged_batches": staged,
        "staging_document_count": len(staged),
        "csv_rows_by_batch": dict(sorted(rows_by_batch.items())),
        "csv_files_by_batch": {str(k): sorted(v) for k, v in sorted(files_by_batch.items())},
        "total_staging_csv_rows_batch006_plus": sum(v for k, v in rows_by_batch.items() if k >= 6),
    }


def scan_db(db: Path) -> dict:
    if not db.exists():
        return {"exists": False, "path": str(db)}
    conn = sqlite3.connect(db)
    try:
        tables = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )]
        counts = {}
        for table in tables:
            if table.startswith("rag_fts_"):
                continue
            counts[table] = conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
        fk_violations = len(conn.execute("PRAGMA foreign_key_check").fetchall())
        return {
            "exists": True,
            "path": str(db),
            "integrity_check": integrity,
            "foreign_key_violations": fk_violations,
            "table_counts": counts,
            "rag_fts_documents": counts.get("rag_fts", 0),
        }
    finally:
        conn.close()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="database/pur_master.db")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    db_path = Path(args.db)
    if not db_path.is_absolute():
        db_path = ROOT / db_path

    report = {"master": scan_db(db_path), "staging": scan_staging()}
    latest = report["staging"]["latest_documented_batch"]
    report["integration"] = {
        "validated_master_batch": 5,
        "latest_documented_batch": latest,
        "batch_lag": None if latest is None else max(0, latest - 5),
        "status": "current" if latest in (None, 5) else "staging_ahead_of_master",
    }

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        return

    print("Database-For-PUR health report")
    print("=" * 31)
    master = report["master"]
    if master["exists"]:
        print(f"master DB: {master['path']}")
        print(f"integrity: {master['integrity_check']}")
        print(f"foreign-key violations: {master['foreign_key_violations']}")
        for key in ("sources", "experiments", "materials", "formulations", "measurements", "evidence", "viscosity_curves", "rag_fts"):
            if key in master["table_counts"]:
                print(f"{key:24s} {master['table_counts'][key]:>8}")
    else:
        print(f"master DB not found: {master['path']}")

    staging = report["staging"]
    print("\nStaging")
    print(f"latest documented batch: {staging['latest_documented_batch']}")
    print(f"Batch 006+ documents:     {staging['staging_document_count']}")
    print(f"Batch 006+ CSV rows:      {staging['total_staging_csv_rows_batch006_plus']}")
    print("rows by batch:")
    for batch, rows in staging["csv_rows_by_batch"].items():
        if int(batch) >= 6:
            print(f"  Batch {int(batch):03d}: {rows}")

    integ = report["integration"]
    print("\nIntegration")
    print(f"validated master batch:   {integ['validated_master_batch']:03d}")
    if integ["latest_documented_batch"]:
        print(f"latest staging batch:     {integ['latest_documented_batch']:03d}")
    else:
        print("latest staging batch:     n/a")
    print(f"integration lag:          {integ['batch_lag']} batches")
    print(f"status:                   {integ['status']}")


if __name__ == "__main__":
    main()
