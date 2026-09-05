#!/usr/bin/env python3
import csv
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "materials"


def rows(name):
    with (DATA / name).open(newline="", encoding="utf-8") as f:
        data = list(csv.DictReader(f))
    assert all(None not in r for r in data), f"CSV width mismatch in {name}"
    return data


sources = rows("batch011_sources.csv")
methods = rows("batch011_methods.csv")
materials = rows("us8394868_materials_batch011.csv")
pairs = rows("us8394868_same_temp_amplification_batch011.csv")
series = rows("us8394868_controlled_index_series_batch011.csv")

source_ids = {r["source_id"] for r in sources}
method_ids = {r["method_id"] for r in methods}
assert source_ids == {"PAT_US8394868B2"}
assert len(materials) == 5
assert len(pairs) == 5
assert len(series) == 3

for table in (methods, materials, pairs, series):
    assert all(r["source_id"] in source_ids for r in table)

for r in pairs:
    assert r["reaction_method_id"] in method_ids
    t0 = float(r["precursor_temperature_c"])
    t1 = float(r["prepolymer_temperature_c"])
    assert math.isclose(t0, t1, rel_tol=0, abs_tol=1e-12)
    assert r["same_temperature_pair"] == "1"
    calc = float(r["prepolymer_viscosity_mpa_s"]) / float(r["precursor_viscosity_mpa_s"])
    assert math.isclose(calc, float(r["viscosity_amplification_factor"]), rel_tol=2e-6, abs_tol=2e-6)

exact = [r for r in pairs if r["composition_match_class"] == "exact_same_blend_same_temperature"]
near = [r for r in pairs if r["composition_match_class"] == "near_matched_same_temperature"]
assert len(exact) == 3 and len(near) == 2
assert {r["precursor_viscosity_mpa_s"] for r in exact} == {"710"}
assert {r["precursor_blend_parts"] for r in exact} == {"50:50"}
assert {r["isocyanate"] for r in exact} == {"VORANATE T-80"}

idx = [int(r["isocyanate_index"]) for r in series]
visc = [float(r["viscosity_mpa_s"]) for r in series]
amp = [float(r["viscosity_amplification_vs_unreacted_blend"]) for r in series]
load = [float(r["g_isocyanate_per_100g_polyol"]) for r in series]
assert idx == [30, 33, 36]
assert visc == sorted(visc)
assert amp == sorted(amp)
assert load == sorted(load)

for r in series:
    assert math.isclose(float(r["polyol_a_wt_fraction"]) + float(r["polyol_b_wt_fraction"]), 1.0, abs_tol=1e-12)
    calc = float(r["viscosity_mpa_s"]) / 710.0
    assert math.isclose(calc, float(r["viscosity_amplification_vs_unreacted_blend"]), rel_tol=2e-6, abs_tol=2e-6)

assert all(r["factor_status"].startswith("derived_") for r in pairs)

print("Batch 011 validation passed:", len(materials), "materials;", len(pairs), "same-temperature links;", len(series), "controlled-index rows")
