#!/usr/bin/env python3
"""Validate Batch 006 staging CSVs before SQLite integration."""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data" / "materials"

EXPECTED_ROWS = {
    "batch006_sources.csv": 2,
    "prepolymer_pair_benchmarks_batch006.csv": 22,
    "material_application_claims_batch006.csv": 17,
    "patent_polyol_properties_batch006.csv": 4,
    "patent_purhm_benchmark_batch006.csv": 5,
}


def rows(name: str) -> list[dict[str, str]]:
    path = BASE / name
    if not path.exists():
        raise SystemExit(f"missing Batch 006 file: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def unique(values: list[str], label: str) -> None:
    if len(values) != len(set(values)):
        raise SystemExit(f"duplicate {label}")


def main() -> None:
    loaded = {name: rows(name) for name in EXPECTED_ROWS}
    for name, expected in EXPECTED_ROWS.items():
        actual = len(loaded[name])
        if actual != expected:
            raise SystemExit(f"{name}: expected {expected} rows, found {actual}")

    pair = loaded["prepolymer_pair_benchmarks_batch006.csv"]
    unique([r["pair_id"] for r in pair], "pair_id")
    targets = {r["target_nco_pct"] for r in pair}
    if targets != {"10", "15"}:
        raise SystemExit(f"unexpected target NCO set: {sorted(targets)}")
    grades = {r["polyol_grade"] for r in pair}
    if len(grades) != 11:
        raise SystemExit(f"expected 11 paired polyol grades, found {len(grades)}")
    for grade in grades:
        subset = [r for r in pair if r["polyol_grade"] == grade]
        if {r["target_nco_pct"] for r in subset} != {"10", "15"}:
            raise SystemExit(f"incomplete NCO pair for {grade}")

    bench = loaded["patent_purhm_benchmark_batch006.csv"]
    unique([r["sample_id"] for r in bench], "patent benchmark sample_id")
    for r in bench:
        nco = float(r["nco_wt_pct"])
        visc = float(r["melt_viscosity_cp"])
        if not (0 < nco < 10):
            raise SystemExit(f"implausible NCO value in {r['sample_id']}: {nco}")
        if visc <= 0:
            raise SystemExit(f"non-positive viscosity in {r['sample_id']}: {visc}")
        if float(r["green_strength_6min_psi"]) < 0:
            raise SystemExit(f"negative green strength in {r['sample_id']}")

    polyols = loaded["patent_polyol_properties_batch006.csv"]
    unique([r["material_id"] for r in polyols], "patent polyol material_id")

    print("Batch 006 validation: PASS")
    for name, expected in EXPECTED_ROWS.items():
        print(f"  {name:<48} {expected}")
    print("  paired polyol grades                               11")
    print("  target NCO levels                                 10%, 15%")


if __name__ == "__main__":
    main()
