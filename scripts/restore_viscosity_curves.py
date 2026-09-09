#!/usr/bin/env python3
"""Reassemble and validate the canonical 4,559-point legacy viscosity payload.

The historical committed gzip is truncated. The canonical replacement is stored as
small SHA-pinned Git blobs generated from the complete legacy SQLite table, with
`pNCO_pct` normalized to the schema field `pnco_pct`.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
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

# Ordered chunks and their exact Git blob SHAs. The two historically problematic
# 9-kB chunks (part02/part04) are stored as 1-kB subchunks to make byte-level
# verification deterministic through the connector.
CHUNKS = [
    ("viscosity_curves.normalized.csv.gz.part00", "36d23cf66115b1e6801953701838356c1fb6ed40"),
    ("viscosity_curves.normalized.csv.gz.part01", "ef3d3bb3ae014bde575788bfd087eaf71cec805c"),
    ("viscosity_curves.normalized.csv.gz.part02.00", "44b91088cdd879ab4d70ad3de3ea5a06513f4d4a"),
    ("viscosity_curves.normalized.csv.gz.part02.01", "9e3bca63c49dc529190d3a776fc14c4c86d03be3"),
    ("viscosity_curves.normalized.csv.gz.part02.02", "8f7cb1b935a05406442c80f80b399a06e7ea1266"),
    ("viscosity_curves.normalized.csv.gz.part02.03", "d63ad705bde2a46fca923c004707ad9247aaf12f"),
    ("viscosity_curves.normalized.csv.gz.part02.04", "e2356323f806c775d6db1d6227217b0975365176"),
    ("viscosity_curves.normalized.csv.gz.part02.05", "78c0e06ede884fc033f560852d8ba1abf557de43"),
    ("viscosity_curves.normalized.csv.gz.part02.06", "fd45c149b2549aeb61cb1f7628145b0d7749d8b0"),
    ("viscosity_curves.normalized.csv.gz.part02.07", "beeb751c638964ebd3b8a3427b746fb39dedc23e"),
    ("viscosity_curves.normalized.csv.gz.part02.08", "7cb5bc801515d08d894221e6ef51738d464f573f"),
    ("viscosity_curves.normalized.csv.gz.part03", "8df562c2ff9b98834902f1afca02f55793f35003"),
    ("viscosity_curves.normalized.csv.gz.part04.00", "8d0d1afc8e373cc9c0a226c48ded883f2e165df7"),
    ("viscosity_curves.normalized.csv.gz.part04.01", "cbc1b772491765310b376d043c3d129c976412a9"),
    ("viscosity_curves.normalized.csv.gz.part04.02", "ccfe5cb4eff8482d9d31494811cb17d434ee4bb6"),
    ("viscosity_curves.normalized.csv.gz.part04.03", "ed60e7cf63aca05dce7976f8cc48ed79e52b2353"),
    ("viscosity_curves.normalized.csv.gz.part04.04", "e1d50b132d14c8178fb88c11731ba8a8c3ec094c"),
    ("viscosity_curves.normalized.csv.gz.part04.05", "cda6a8cabd6372e7d08dd11d4f0c810be91aa264"),
]


def git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default="data/legacy/viscosity_curves.csv.gz")
    args = ap.parse_args()

    payloads = []
    for name, expected_sha in CHUNKS:
        path = LEGACY / name
        if not path.exists():
            raise SystemExit(f"missing viscosity recovery chunk: {path.relative_to(ROOT)}")
        data = path.read_bytes()
        actual_sha = git_blob_sha(data)
        if actual_sha != expected_sha:
            raise SystemExit(
                f"Git blob SHA mismatch for {name}: {actual_sha} != {expected_sha}"
            )
        payloads.append(data)

    raw = b"".join(payloads)
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
    print(f"  SHA-verified chunks: {len(CHUNKS)}")
    print(f"  rows:                {len(rows)}")
    print(f"  curve samples:       {len(samples)}")
    print(f"  pNCO levels:         {', '.join(sorted(pnco, key=float))}")
    print(f"  output:              {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
