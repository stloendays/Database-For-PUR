#!/usr/bin/env python3
"""Validate that historical recovery boundaries are explicit inside PUR v2."""
from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_DEFICITS = {
    "formulation_components": 122,
    "process_steps": 72,
    "protocols": 20,
    "evidence": 8,
}
EXPECTED_STRUCTURAL = {
    "experiments": "fk_closed_with_parent_stubs",
    "formulations": "fk_closed_with_parent_stubs",
    "patents": "identity_index_reconstructed",
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    args = ap.parse_args()
    db = ROOT / args.db
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row

    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if "data_recovery_status" not in tables:
        raise SystemExit("missing data_recovery_status table")

    rows = {
        r["table_name"]: r
        for r in conn.execute(
            "SELECT * FROM data_recovery_status WHERE layer='cn_batch004_historical_recovery'"
        )
    }
    if len(rows) != 7:
        raise SystemExit(f"expected 7 Chinese recovery rows, found {len(rows)}")

    for table_name, expected_missing in EXPECTED_DEFICITS.items():
        row = rows.get(table_name)
        if row is None:
            raise SystemExit(f"missing recovery row for {table_name}")
        if row["missing_rows"] != expected_missing:
            raise SystemExit(
                f"{table_name} missing_rows={row['missing_rows']} != {expected_missing}"
            )
        if row["status"] != "historical_metadata_deficit":
            raise SystemExit(f"unexpected deficit status for {table_name}: {row['status']}")

    for table_name, expected_status in EXPECTED_STRUCTURAL.items():
        row = rows.get(table_name)
        if row is None:
            raise SystemExit(f"missing recovery row for {table_name}")
        if row["missing_rows"] != 0:
            raise SystemExit(f"{table_name} should be FK-closed, missing_rows={row['missing_rows']}")
        if row["status"] != expected_status:
            raise SystemExit(
                f"{table_name} status={row['status']} != {expected_status}"
            )

    negatives = conn.execute(
        "SELECT COUNT(*) FROM data_recovery_status WHERE missing_rows < 0"
    ).fetchone()[0]
    if negatives:
        raise SystemExit("negative recovery deficits detected")

    print("v2 recovery metadata validation: PASS")
    print("  historical deficit tables: formulation_components=122, process_steps=72, protocols=20, evidence=8")
    print("  FK-closed structural layers: experiments, formulations, patents")
    conn.close()


if __name__ == "__main__":
    main()
