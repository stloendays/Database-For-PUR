#!/usr/bin/env python3
"""Import machine-readable historical recovery status into a PUR v2 SQLite DB."""
from __future__ import annotations

import argparse
import csv
import io
import sqlite3
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schema" / "pur_v2_recovery.sql"
MEMBER = "data/cn/recovery_status.csv"


def as_int(value: str | None) -> int | None:
    s = (value or "").strip()
    return int(s) if s else None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--cn-release", required=True)
    args = ap.parse_args()

    db = ROOT / args.db
    release = ROOT / args.cn_release
    if not db.exists():
        raise SystemExit(f"database not found: {db}")
    if not release.exists():
        raise SystemExit(f"Chinese release not found: {release}")

    with zipfile.ZipFile(release) as zf:
        if MEMBER not in zf.namelist():
            raise SystemExit(f"{MEMBER} not found in {release}")
        text = zf.read(MEMBER).decode("utf-8-sig")
        rows = list(csv.DictReader(io.StringIO(text, newline="")))

    now = datetime.now(timezone.utc).isoformat()
    conn = sqlite3.connect(db)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))

    layer = "cn_batch004_historical_recovery"
    for row in rows:
        table_name = (row.get("table_name") or "").strip()
        if not table_name:
            raise SystemExit("recovery_status row missing table_name")
        documented = as_int(row.get("documented_batch004_rows"))
        operational = as_int(row.get("operational_rows"))
        missing = as_int(row.get("missing_rows"))
        if documented is not None and operational is not None and missing is not None:
            if documented - operational != missing:
                raise SystemExit(
                    f"recovery arithmetic mismatch for {table_name}: "
                    f"{documented} - {operational} != {missing}"
                )
        conn.execute(
            """
            INSERT INTO data_recovery_status(
              recovery_id, layer, source_release, table_name,
              documented_rows, operational_rows, missing_rows,
              status, policy, integrated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(recovery_id) DO UPDATE SET
              layer=excluded.layer,
              source_release=excluded.source_release,
              table_name=excluded.table_name,
              documented_rows=excluded.documented_rows,
              operational_rows=excluded.operational_rows,
              missing_rows=excluded.missing_rows,
              status=excluded.status,
              policy=excluded.policy,
              integrated_at=excluded.integrated_at
            """,
            (
                f"cn_batch004:{table_name}",
                layer,
                str(release.relative_to(ROOT)),
                table_name,
                documented,
                operational,
                missing,
                (row.get("status") or "unknown").strip(),
                (row.get("policy") or "").strip() or None,
                now,
            ),
        )

    conn.commit()
    total = conn.execute(
        "SELECT COUNT(*) FROM data_recovery_status WHERE layer=?", (layer,)
    ).fetchone()[0]
    deficits = conn.execute(
        "SELECT COUNT(*) FROM data_recovery_status WHERE layer=? AND missing_rows>0", (layer,)
    ).fetchone()[0]
    conn.close()
    print(f"recovery status import: PASS rows={total} deficit_tables={deficits}")


if __name__ == "__main__":
    main()
