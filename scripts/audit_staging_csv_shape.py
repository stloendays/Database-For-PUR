#!/usr/bin/env python3
"""Audit Batch 006+ staging CSVs for row/header shape mismatches.

csv.DictReader stores surplus cells under a None key.  That is a data-shape
error, not valid payload, so report the exact file/line before v2 ingestion.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "materials"
BATCH_RE = re.compile(r"batch(\d{3})", re.IGNORECASE)


def main() -> None:
    failures = 0
    checked = 0
    for path in sorted(DATA.glob("*.csv")):
        m = BATCH_RE.search(path.name)
        if not m or int(m.group(1)) < 6:
            continue
        checked += 1
        with path.open("r", encoding="utf-8-sig", newline="") as fh:
            reader = csv.DictReader(fh)
            headers = reader.fieldnames or []
            if len(headers) != len(set(headers)):
                print(f"ERROR {path.relative_to(ROOT)}: duplicate header names")
                failures += 1
            for rownum, row in enumerate(reader, start=2):
                extra = row.get(None)
                if extra:
                    print(
                        f"ERROR {path.relative_to(ROOT)}:{rownum}: "
                        f"{len(extra)} surplus cell(s) beyond {len(headers)} headers: {extra!r}"
                    )
                    failures += 1
                missing = [h for h in headers if row.get(h) is None]
                if missing:
                    print(
                        f"ERROR {path.relative_to(ROOT)}:{rownum}: "
                        f"row ended before columns {missing!r}"
                    )
                    failures += 1
    print(f"staging CSV shape audit: checked={checked} failures={failures}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
