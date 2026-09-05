#!/usr/bin/env python3
"""Validate Batch 007 staging CSVs before cumulative SQLite integration."""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "materials"


def read(name: str):
    with (DATA / name).open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def fail(msg: str) -> None:
    raise SystemExit(f"ERROR: {msg}")


def main() -> None:
    matched = read("evonik_matched_130c_amplification_batch007.csv")
    if len(matched) != 10:
        fail(f"expected 10 same-temperature Evonik rows, found {len(matched)}")

    factors = []
    for row in matched:
        if row["same_temperature_pair"] != "1":
            fail(f"matched row not flagged same-temperature: {row['record_id']}")
        t0 = float(row["precursor_temperature_c"])
        t1 = float(row["prepolymer_temperature_c"])
        if t0 != t1:
            fail(f"temperature mismatch in {row['record_id']}: {t0} vs {t1}")
        raw = float(row["precursor_viscosity_pa_s"])
        pre = float(row["prepolymer_viscosity_pa_s"])
        factor = float(row["viscosity_amplification_factor"])
        expected = pre / raw
        if abs(factor - expected) > 1e-4:
            fail(f"amplification mismatch in {row['record_id']}")
        factors.append(factor)

    if min(factors) < 2.9 or max(factors) < 13.9:
        fail("matched amplification range is unexpectedly truncated")

    stepan = read("stepan_purhm_typical_properties_batch007.csv")
    if len(stepan) != 17:
        fail(f"expected 17 Stepan PURHM rows, found {len(stepan)}")
    if any(row["same_temperature_pair"] != "0" for row in stepan):
        fail("Stepan cross-temperature rows must not be flagged as direct amplification pairs")

    polyesters = read("patent_polyester_structure_batch007.csv")
    rhm = read("patent_rhm_structure_property_batch007.csv")
    if len(polyesters) != 9 or len(rhm) != 9:
        fail(f"expected 9 polyester + 9 RHM controlled rows; found {len(polyesters)} + {len(rhm)}")
    polyester_ids = {r["polyester_id"] for r in polyesters}
    dangling = [r["record_id"] for r in rhm if r["third_polyester_id"] not in polyester_ids]
    if dangling:
        fail(f"dangling third-polyester references: {dangling}")
    for row in rhm:
        parts = float(row["dynacoll_7130_parts"]) + float(row["dynacoll_7230_parts"]) + float(row["third_polyester_parts"])
        if abs(parts - float(row["polyol_total_parts"])) > 1e-9:
            fail(f"polyol blend does not close to total in {row['record_id']}")

    crystalline = read("patent_crystalline_prepolymer_batch007.csv")
    if len(crystalline) != 11:
        fail(f"expected 11 crystalline polyester/prepolymer rows, found {len(crystalline)}")
    temps = {float(r["prepolymer_viscosity_temperature_c"]) for r in crystalline}
    if temps != {120.0, 140.0}:
        fail(f"expected explicit 120/140 C viscosity temperatures, found {sorted(temps)}")

    audit = read("evonik_source_version_audit_batch007.csv")
    if len(audit) != 1:
        fail("expected one explicit source-version discrepancy audit row")
    a = audit[0]
    rel = abs(float(a["older_value_pa_s"]) - float(a["newer_value_pa_s"])) / float(a["older_value_pa_s"]) * 100
    if abs(rel - float(a["relative_difference_pct"])) > 1e-9:
        fail("source-version relative difference does not recompute")

    print("Batch 007 validation: PASS")
    print(f"  same-temperature Evonik pairs  {len(matched)}")
    print(f"  amplification range            {min(factors):.2f}x to {max(factors):.2f}x")
    print(f"  Stepan PURHM property rows      {len(stepan)}")
    print(f"  controlled patent blend rows    {len(rhm)}")
    print(f"  crystalline prepolymer rows     {len(crystalline)}")
    print(f"  source-version audit rows       {len(audit)}")


if __name__ == "__main__":
    main()
