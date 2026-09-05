#!/usr/bin/env python3
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "materials"

FORM = DATA / "henkel_us5599895_formulations_batch008.csv"
MATS = DATA / "henkel_us5599895_materials_batch008.csv"
CONTRASTS = DATA / "henkel_us5599895_controlled_contrasts_batch008.csv"
SOURCES = DATA / "batch008_sources.csv"


def load(path: Path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def fnum(value: str):
    return None if value in (None, "") else float(value)


sources = load(SOURCES)
forms = load(FORM)
mats = load(MATS)
contrasts = load(CONTRASTS)

source_ids = {r["source_id"] for r in sources}
assert source_ids == {"PAT_US5599895A"}

for group_name, rows in [("formulations", forms), ("materials", mats), ("contrasts", contrasts)]:
    for row in rows:
        assert row["source_id"] in source_ids, (group_name, row)

assert len(forms) == 17
assert len({r["record_id"] for r in forms}) == len(forms)

component_cols = [
    "polyester_a_wt_pct", "polyester_b_wt_pct", "polyester_c_wt_pct",
    "polyester_d_wt_pct", "polyester_i_wt_pct", "polyester_h_wt_pct",
    "ppg425_wt_pct", "tackifier_beta_pinene_wt_pct",
    "hydrocarbon_resin_wt_pct", "mdi44_wt_pct",
]

for row in forms:
    total = sum(fnum(row[c]) or 0.0 for c in component_cols)
    reported = float(row["reported_total_wt_pct"])
    assert abs(total - reported) < 1e-6, (row["record_id"], total, reported)
    # Patent tables contain rounding to one or two decimals; accept at most 0.11 wt% closure error.
    assert abs(reported - 100.0) <= 0.11, (row["record_id"], reported)
    lo = fnum(row["viscosity_130c_pa_s_min"])
    hi = fnum(row["viscosity_130c_pa_s_max"])
    if lo is not None or hi is not None:
        assert lo is not None and hi is not None
        assert 0 < lo <= hi
    slo = fnum(row["initial_strength_min_kg_cm"])
    shi = fnum(row["initial_strength_max_kg_cm"])
    if slo is not None or shi is not None:
        assert slo is not None and shi is not None
        assert 0 <= slo <= shi
    assert row["nco_oh_ratio"] in {"1.3:1", "1.4:1", "1.5:1"}

form_ids = {r["record_id"] for r in forms}
assert len(contrasts) == 3
for row in contrasts:
    assert row["baseline_record_id"] in form_ids
    assert row["variant_record_id"] in form_ids
    vb = float(row["baseline_viscosity_130c_pa_s"])
    vv = float(row["variant_viscosity_130c_pa_s"])
    assert abs((vv - vb) - float(row["delta_viscosity_130c_pa_s"])) < 1e-6
    assert abs((vv / vb) - float(row["viscosity_ratio_variant_over_baseline"])) < 1e-4

material_ids = {r["material_id"] for r in mats}
required = {
    "MAT_HENKEL_POLY_A", "MAT_HENKEL_POLY_B", "MAT_HENKEL_POLY_C",
    "MAT_HENKEL_POLY_D", "MAT_HENKEL_POLY_H", "MAT_HENKEL_POLY_I",
    "MAT_HENKEL_PPG425", "MAT_HENKEL_TACK_BPINENE",
    "MAT_HENKEL_HC_RESIN", "MAT_HENKEL_MDI44",
}
assert required <= material_ids

print(f"Batch 008 validation passed: {len(forms)} formulations, {len(mats)} materials, {len(contrasts)} controlled contrasts.")
