#!/usr/bin/env python3
"""Reassemble and validate the canonical 4,559-point legacy viscosity payload.

The historical committed gzip is truncated. The canonical replacement is stored as
five Git blobs generated from the complete legacy SQLite table, with `pNCO_pct`
normalized to the schema field `pnco_pct`.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import io
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEGACY = ROOT / "data" / "legacy"
EXPECTED_ROWS = 4559
EXPECTED_SAMPLES = 39
EXPECTED_PNCO = {"4.0", "5.0", "6.0", "7.0", "8.0", "9.0", "10.0"}
REQUIRED_FIELDS = {
    "source_id", "sample_id", "polyol_code", "isocyanate_code", "pnco_pct",
    "sequence_index", "temperature_c", "viscosity_pa_s", "evidence_locator", "source_url",
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default="data/legacy/viscosity_curves.csv.gz")
    args = ap.parse_args()

    parts = sorted(LEGACY.glob("viscosity_curves.normalized.csv.gz.part*"))
    if len(parts) != 5:
        raise SystemExit(f"expected 5 normalized viscosity parts, found {len(parts)}")

    raw = b"".join(p.read_bytes() for p in parts)
    try:
        with gzip.GzipFile(fileobj=io.BytesIO(raw), mode="rb") as gz:
            text = gz.read().decode("utf-8-sig")
    except Exception as exc:
        raise SystemExit(f"normalized viscosity gzip failed decompression: {exc}") from exc

    reader = csv.DictReader(io.StringIO(text))
    fields = set(reader.fieldnames or [])
    missing = REQUIRED_FIELDS - fields
    if missing:
        raise SystemExit(f"viscosity payload missing required fields: {sorted(missing)}")
    if "pNCO_pct" in fields:
        raise SystemExit("legacy mixed-case pNCO_pct field remains; expected normalized pnco_pct")

    rows = list(reader)
    if len(rows) != EXPECTED_ROWS:
        raise SystemExit(f"expected {EXPECTED_ROWS} viscosity rows, found {len(rows)}")
    samples = {r["sample_id"] for r in rows}
    if len(samples) != EXPECTED_SAMPLES:
        raise SystemExit(f"expected {EXPECTED_SAMPLES} curve samples, found {len(samples)}")
    pnco = {r["pnco_pct"] for r in rows}
    if pnco != EXPECTED_PNCO:
        raise SystemExit(f"unexpected pnco_pct levels: {sorted(pnco)}")

    for i, row in enumerate(rows, 1):
        try:
            float(row["temperature_c"])
            viscosity = float(row["viscosity_pa_s"])
            float(row["pnco_pct"])
            int(float(row["sequence_index"]))
        except ValueError as exc:
            raise SystemExit(f"non-numeric viscosity record at row {i}: {exc}") from exc
        if viscosity <= 0:
            raise SystemExit(f"non-positive viscosity at row {i}: {viscosity}")

    output = Path(args.output)
    if not output.is_absolute():
        output = ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(raw)

    # Verify the exact bytes written are still readable.
    with gzip.open(output, "rt", encoding="utf-8-sig", newline="") as fh:
        written = list(csv.DictReader(fh))
    if len(written) != EXPECTED_ROWS:
        raise SystemExit("written viscosity gzip failed round-trip row-count validation")

    print("Legacy viscosity reconstruction: PASS")
    print(f"  rows:         {len(rows)}")
    print(f"  curve samples:{len(samples):>5}")
    print(f"  pNCO levels:  {', '.join(sorted(pnco, key=float))}")
    print(f"  output:       {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
