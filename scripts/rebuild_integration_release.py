#!/usr/bin/env python3
"""Rebuild the Batch 005 integration payload without the truncated historical ZIP.

Inputs are all committed, source-traceable records:
- legacy_core.tar.gz.part01..03: complete legacy relational export;
- data/legacy/viscosity_curves.csv.gz;
- Batch 005 manufacturer tables in data/materials/.

Specification ranges remain ranges; no midpoint is substituted.
"""
from __future__ import annotations

import argparse
import csv
import io
import re
import tarfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEGACY = ROOT / "data" / "legacy"
MATDIR = ROOT / "data" / "materials"
EXPECTED_LEGACY = {
    "formulations.csv": 85,
    "formulation_components.csv": 278,
    "measurements.csv": 547,
    "protocols.csv": 22,
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def csv_bytes(rows: list[dict]) -> bytes:
    if not rows:
        return b""
    out = io.StringIO(newline="")
    writer = csv.DictWriter(out, fieldnames=list(rows[0]), extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue().encode("utf-8")


def tok(text: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "_", text.upper()).strip("_")


def f(value) -> float | None:
    try:
        s = str(value).strip().replace(",", "")
        return float(s) if s else None
    except (TypeError, ValueError):
        return None


def parse_range(value: str | None):
    s = (value or "").strip().replace("–", "-").replace("—", "-")
    if not s:
        return None, None, None, None
    if s.startswith(("<=", "≤")):
        return None, None, f(s.lstrip("<≤=")), "<="
    if s.startswith("<"):
        return None, None, f(s[1:]), "<"
    m = re.fullmatch(r"\s*([-+]?\d+(?:\.\d+)?)\s*-\s*([-+]?\d+(?:\.\d+)?)\s*", s)
    if m:
        return None, float(m.group(1)), float(m.group(2)), "range"
    return f(s), None, None, None


def recover_legacy() -> dict[str, bytes]:
    parts = sorted(LEGACY.glob("legacy_core.tar.gz.part*"))
    if len(parts) != 3:
        raise SystemExit(f"expected three legacy payload parts, found {len(parts)}")
    payload = b"".join(p.read_bytes() for p in parts)
    members: dict[str, bytes] = {}
    with tarfile.open(fileobj=io.BytesIO(payload), mode="r:gz") as tf:
        for name, expected in EXPECTED_LEGACY.items():
            raw = tf.extractfile(name).read()
            n = len(list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))))
            if n != expected:
                raise SystemExit(f"{name}: expected {expected} rows, found {n}")
            members[f"data/legacy/{name}"] = raw
    curves = LEGACY / "viscosity_curves.csv.gz"
    members["data/legacy/viscosity_curves.csv.gz"] = curves.read_bytes()
    return members


def build_sources() -> list[dict]:
    rows = [dict(r) for r in read_csv(MATDIR / "batch005_sources.csv")]
    for r in read_csv(MATDIR / "stepan_polyols_batch005.csv"):
        rows.append({
            "source_id": f"MFR_STEPAN_{tok(r['grade'])}",
            "source_type": "manufacturer_tds",
            "title": r["grade"],
            "title_en": r["grade"],
            "authors": "",
            "institution": "Stepan",
            "journal_or_publisher": "Stepan",
            "year": "2026",
            "language": "en",
            "doi": "",
            "patent_number": "",
            "publication_number": "",
            "standard_number": "",
            "source_url": r["source_url"],
            "local_source_path": "",
            "license": "Manufacturer publication; see source",
            "access_date": "2026-09-05",
            "quality_level": "A",
            "extraction_status": "structured_official_tds",
            "notes": r.get("notes", ""),
        })
    if len(rows) != 9 or len({r["source_id"] for r in rows}) != 9:
        raise SystemExit(f"Batch 005 source reconstruction failed: {len(rows)} rows")
    return rows


def add_prop(props: list[dict], mid: str, sid: str, name: str, *, value=None,
             lo=None, hi=None, qualifier=None, unit=None, temp=None, locator=None,
             condition=None):
    if value is None and lo is None and hi is None:
        return
    props.append({
        "property_record_id": f"MPV_{len(props)+1:04d}",
        "material_id": mid,
        "source_id": sid,
        "property_name": name,
        "value": value,
        "qualifier": qualifier,
        "value_min": lo,
        "value_max": hi,
        "unit": unit,
        "temperature_c": temp,
        "condition": condition,
        "method_or_standard": None,
        "evidence_type": "reported/specification",
        "evidence_locator": locator,
        "quality_level": "A",
        "source_url": None,
        "notes": None,
    })


def build_materials():
    materials, props = [], []
    summary = read_csv(MATDIR / "material_property_summary_batch005.csv")
    for r in summary:
        mid, sid, loc = r["material_id"], r["source_id"], r.get("evidence_locator")
        oh_lo, oh_hi = f(r.get("oh_min_mg_koh_g")), f(r.get("oh_max_mg_koh_g"))
        acid_lo, acid_hi = f(r.get("acid_min_mg_koh_g")), f(r.get("acid_max_mg_koh_g"))
        materials.append({
            "material_id": mid, "normalized_name": r["grade"], "name_en": r["grade"],
            "category": "polyol", "subcategory": r.get("material_family"),
            "supplier": r.get("supplier"), "grade": r["grade"],
            "molecular_weight_g_mol": f(r.get("molecular_weight_g_mol")),
            "oh_value_mg_koh_g": oh_lo if oh_lo == oh_hi else None,
            "acid_value_mg_koh_g": acid_lo if acid_lo == acid_hi else None,
            "melting_point_c": f(r.get("melting_point_c")), "tg_c": f(r.get("tg_c")),
            "density_g_cm3": f(r.get("density_23c_kg_dm3")), "source_id": sid,
            "notes": f"Morphology: {r.get('morphology') or 'not reported'}; {loc or ''}",
        })
        add_prop(props, mid, sid, "hydroxyl_number",
                 value=oh_lo if oh_lo == oh_hi else None,
                 lo=oh_lo if oh_lo != oh_hi else None, hi=oh_hi if oh_lo != oh_hi else None,
                 qualifier="range" if oh_lo != oh_hi else None, unit="mg KOH/g", locator=loc)
        aq = (r.get("acid_qualifier") or "").strip() or None
        if acid_lo is not None and acid_hi is not None and acid_lo != acid_hi:
            add_prop(props, mid, sid, "acid_number", lo=acid_lo, hi=acid_hi, qualifier=aq or "range", unit="mg KOH/g", locator=loc)
        elif acid_hi is not None and acid_lo is None:
            add_prop(props, mid, sid, "acid_number", hi=acid_hi, qualifier=aq or "max", unit="mg KOH/g", locator=loc)
        else:
            add_prop(props, mid, sid, "acid_number", value=acid_lo, qualifier=aq, unit="mg KOH/g", locator=loc)
        for key, name, unit, temp in [
            ("molecular_weight_g_mol", "molecular_weight", "g/mol", None),
            ("tg_c", "glass_transition_temperature", "C", None),
            ("melting_point_c", "melting_point", "C", None),
            ("softening_point_c", "softening_point", "C", None),
            ("density_23c_kg_dm3", "density", "kg/dm3", 23),
            ("viscosity_80c_pa_s", "viscosity", "Pa.s", 80),
            ("viscosity_130c_pa_s", "viscosity", "Pa.s", 130),
        ]:
            add_prop(props, mid, sid, name, value=f(r.get(key)), unit=unit, temp=temp, locator=loc)
        detail = loc or ""
        m = re.search(r"viscosity (\d+(?:\.\d+)?)-(\d+(?:\.\d+)?) mPa\.s @(\d+(?:\.\d+)?)C", detail, re.I)
        if m:
            add_prop(props, mid, sid, "viscosity", lo=float(m.group(1)), hi=float(m.group(2)), qualifier="range", unit="mPa.s", temp=float(m.group(3)), locator=loc)
        m = re.search(r"viscosity (\d+(?:\.\d+)?)±(\d+(?:\.\d+)?) mPa\.s @(\d+(?:\.\d+)?)C", detail, re.I)
        if m:
            center, tol = float(m.group(1)), float(m.group(2))
            add_prop(props, mid, sid, "viscosity", value=center, lo=center-tol, hi=center+tol, qualifier="plus_minus", unit="mPa.s", temp=float(m.group(3)), locator=loc)
        m = re.search(r"water (?:approx )?(?:<=|≤)?(\d+(?:\.\d+)?) wt\.%", detail, re.I)
        if m:
            if "<=" in detail or "≤" in detail:
                add_prop(props, mid, sid, "water_content", hi=float(m.group(1)), qualifier="<=", unit="wt.%", locator=loc)
            else:
                add_prop(props, mid, sid, "water_content", value=float(m.group(1)), qualifier="approx", unit="wt.%", locator=loc)
        m = re.search(r"equivalent weight (?:approx )?(\d+(?:\.\d+)?) g/mol", detail, re.I)
        if m:
            add_prop(props, mid, sid, "equivalent_weight", value=float(m.group(1)), qualifier="approx" if "approx" in detail.lower() else None, unit="g/mol", locator=loc)

    for r in read_csv(MATDIR / "isocyanate_property_summary_batch005.csv"):
        mid, sid, loc = f"MAT_BASF_{tok(r['grade'])}", r["source_id"], r.get("evidence_locator")
        materials.append({
            "material_id": mid, "normalized_name": r["grade"], "name_en": r["grade"],
            "category": "isocyanate", "subcategory": r.get("subtype"),
            "supplier": r["supplier"], "grade": r["grade"],
            "functionality": f(r.get("nominal_functionality")), "nco_pct": f(r.get("nco_wt_pct")),
            "viscosity_value": f(r.get("viscosity_cp")), "viscosity_unit": "cP",
            "viscosity_temperature_c": f(r.get("viscosity_temperature_c")), "source_id": sid,
            "notes": loc,
        })
        add_prop(props, mid, sid, "nco_content", value=f(r.get("nco_wt_pct")), unit="wt.%", locator=loc)
        add_prop(props, mid, sid, "nominal_functionality", value=f(r.get("nominal_functionality")), locator=loc)
        add_prop(props, mid, sid, "viscosity", value=f(r.get("viscosity_cp")), unit="cP", temp=f(r.get("viscosity_temperature_c")), locator=loc)
        _, lo, hi, q = parse_range(r.get("storage_temperature_c"))
        add_prop(props, mid, sid, "storage_temperature", lo=lo, hi=hi, qualifier=q, unit="C", condition="recommended storage range", locator=loc)

    for r in read_csv(MATDIR / "stepan_polyols_batch005.csv"):
        mid, sid = f"MAT_STEPAN_{tok(r['grade'])}", f"MFR_STEPAN_{tok(r['grade'])}"
        ov, olo, ohi, oq = parse_range(r.get("hydroxyl_value_mg_koh_g"))
        av, alo, ahi, aq = parse_range(r.get("acid_value_mg_koh_g"))
        materials.append({
            "material_id": mid, "normalized_name": r["grade"], "name_en": r["grade"],
            "category": "polyol", "subcategory": r.get("material_family"),
            "supplier": r["supplier"], "grade": r["grade"], "functionality": f(r.get("functionality")),
            "oh_value_mg_koh_g": ov, "acid_value_mg_koh_g": av,
            "water_content_pct": f(r.get("water_max_wt_pct")), "melting_point_c": f(r.get("melting_point_c")),
            "density_g_cm3": f(r.get("density_25c_g_ml")), "viscosity_value": f(r.get("viscosity_cp")),
            "viscosity_unit": "cP", "viscosity_temperature_c": f(r.get("viscosity_temperature_c")),
            "source_id": sid, "notes": f"Application: {r.get('application') or ''}; {r.get('notes') or ''}",
        })
        loc = r.get("source_url")
        add_prop(props, mid, sid, "hydroxyl_number", value=ov, lo=olo, hi=ohi, qualifier=oq, unit="mg KOH/g", locator=loc)
        add_prop(props, mid, sid, "acid_number", value=av, lo=alo, hi=ahi, qualifier=aq, unit="mg KOH/g", locator=loc)
        if f(r.get("water_max_wt_pct")) is not None:
            add_prop(props, mid, sid, "water_content", hi=f(r.get("water_max_wt_pct")), qualifier="<=", unit="wt.%", locator=loc)
        for key, name, unit, temp_key in [
            ("equivalent_weight_g_eq", "equivalent_weight", "g/eq OH", None),
            ("functionality", "functionality", None, None),
            ("viscosity_cp", "viscosity", "cP", "viscosity_temperature_c"),
            ("melting_point_c", "melting_point", "C", None),
            ("density_25c_g_ml", "density", "g/mL", "_25"),
        ]:
            temp = 25 if temp_key == "_25" else f(r.get(temp_key)) if temp_key else None
            add_prop(props, mid, sid, name, value=f(r.get(key)), unit=unit, temp=temp, locator=loc)

    materials.append({
        "material_id": "MAT_MDI44_REFERENCE", "normalized_name": "4,4'-MDI", "name_en": "4,4'-MDI",
        "chemical_name": "4,4'-diphenylmethane diisocyanate", "category": "isocyanate",
        "subcategory": "monomeric_MDI", "source_id": "MFR_EVO_DYNACOLL7000_2024",
        "notes": "Reference isocyanate in the controlled DYNACOLL RHM table; no unreported specification values inferred.",
    })
    if len(materials) != 37 or len({r["material_id"] for r in materials}) != 37:
        raise SystemExit(f"expected 37 Batch 005 materials, found {len(materials)}")
    if len(props) < 200:
        raise SystemExit(f"material-property reconstruction too small: {len(props)}")
    return materials, props


def metric_value(raw: str):
    s = (raw or "").strip()
    if s.startswith("<"):
        return None, "<", None, f(s[1:])
    v = f(s)
    return v, None if v is not None else "reported_text", None, None


def build_rhm(materials: list[dict]):
    grade_to_mid = {r.get("grade"): r["material_id"] for r in materials if r.get("grade")}
    exps, forms, comps, steps, measurements = [], [], [], [], []
    for r in read_csv(MATDIR / "evonik_rhm_reference_batch005.csv"):
        grade, t, loc = r["polyol_grade"], tok(r["polyol_grade"]), r.get("evidence_locator")
        eid, fid, sample = f"EXP_EVO_RHM_{t}", f"FORM_EVO_RHM_{t}", f"RHM_{t}"
        exps.append({
            "experiment_id": eid, "source_id": r["source_id"], "experiment_number": grade,
            "sample_id": sample, "sample_type": "reference",
            "description": f"Controlled RHM preparation of {grade} with 4,4'-MDI at OH:NCO=1:2.2.",
            "evidence_locator": loc, "quality_level": "A",
        })
        forms.append({
            "formulation_id": fid, "experiment_id": eid, "source_id": r["source_id"], "sample_id": sample,
            "material_class": "reactive_polyurethane_hot_melt", "application": "reactive hot melt adhesive benchmark",
            "formulation_basis": "equivalent_ratio", "nco_oh_index": 2.2,
            "curing_type": "moisture_reactive_isocyanate_terminated_prepolymer",
            "composition_completeness": "equivalent_ratio_only", "evidence_locator": loc,
            "notes": "Source reports OH:NCO=1:2.2; exact masses are not disclosed or reconstructed.",
        })
        if grade not in grade_to_mid:
            raise SystemExit(f"missing material identity for {grade}")
        comps += [
            {"component_record_id": f"COMP_{t}_POLYOL", "formulation_id": fid, "material_id": grade_to_mid[grade],
             "component_name_raw": grade, "component_name_normalized": grade, "role": "polyol",
             "unit": "equivalent", "amount_basis": "source OH:NCO ratio", "equivalent": 1.0, "evidence_locator": loc},
            {"component_record_id": f"COMP_{t}_MDI44", "formulation_id": fid, "material_id": "MAT_MDI44_REFERENCE",
             "component_name_raw": "4,4'-MDI", "component_name_normalized": "4,4'-MDI", "role": "isocyanate",
             "unit": "equivalent", "amount_basis": "source OH:NCO ratio", "equivalent": 2.2, "evidence_locator": loc},
        ]
        steps += [
            {"process_step_id": f"STEP_{t}_01", "experiment_id": eid, "formulation_id": fid, "step_no": 1,
             "operation": "dry_polyester_under_vacuum", "temperature_c": 130, "time_value": 45, "time_unit": "min",
             "atmosphere": "vacuum <10 mbar", "evidence_locator": loc, "notes": r.get("drying_condition")},
            {"process_step_id": f"STEP_{t}_02", "experiment_id": eid, "formulation_id": fid, "step_no": 2,
             "operation": "react_polyester_with_4_4_mdi", "temperature_c": 130, "atmosphere": "dry N2 or CO2",
             "addition_order": "dried polyester then 4,4'-MDI", "evidence_locator": loc, "notes": r.get("reaction_condition")},
            {"process_step_id": f"STEP_{t}_03", "experiment_id": eid, "formulation_id": fid, "step_no": 3,
             "operation": "react_to_theoretical_free_isocyanate_endpoint", "temperature_c": 130,
             "endpoint": "theoretical free isocyanate content", "evidence_locator": loc},
            {"process_step_id": f"STEP_{t}_04", "experiment_id": eid, "formulation_id": fid, "step_no": 4,
             "operation": "vacuum_degas", "endpoint": "bubble-free", "evidence_locator": loc,
             "notes": "After 45 min, vacuum degas until bubble-free."},
        ]
        metrics = [
            ("softening_point", r.get("softening_point_c"), "C", None),
            ("open_time", r.get("open_time"), r.get("open_time_unit") or None, None),
            ("setting_time", r.get("setting_time"), r.get("setting_time_unit") or None, None),
            ("tensile_strength", r.get("tensile_strength_n_mm2"), "N/mm2", None),
            ("elongation", r.get("elongation_pct"), "%", None),
            ("melt_viscosity", r.get("melt_viscosity_130c_pa_s"), "Pa.s", 130),
            ("mechanical_behavior", r.get("mechanical_note"), None, None),
        ]
        for name, raw, unit, temp in metrics:
            raw = (raw or "").strip()
            if not raw:
                continue
            value, qualifier, vmin, vmax = metric_value(raw)
            measurements.append({
                "measurement_id": f"MEAS_{t}_{tok(name)}", "experiment_id": eid, "formulation_id": fid,
                "source_id": r["source_id"], "sample_id": sample, "measurement_stage": "hot_melt",
                "property_name_raw": name, "property_name_normalized": name, "value": value,
                "qualifier": qualifier, "value_min": vmin, "value_max": vmax, "unit": unit,
                "original_value": raw, "original_unit": unit, "temperature_c": temp,
                "condition": "manufacturer-controlled RHM reference preparation", "evidence_type": "reported",
                "evidence_locator": loc, "extraction_method": "structured_official_product_range",
                "quality_level": "A", "notes": "Manufacturer-controlled reference; not an independent replicate.",
            })
    got = tuple(map(len, (exps, forms, comps, steps, measurements)))
    if got != (21, 21, 42, 84, 117):
        raise SystemExit(f"unexpected RHM counts: {got}")
    return exps, forms, comps, steps, measurements


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default="releases/pur_core_integration_v006_rebuilt.zip")
    args = ap.parse_args()
    out = Path(args.output)
    if not out.is_absolute():
        out = ROOT / out

    legacy = recover_legacy()
    sources = build_sources()
    materials, props = build_materials()
    exps, forms, comps, steps, measurements = build_rhm(materials)
    generated = {
        "data/materials/sources.csv": csv_bytes(sources),
        "data/materials/materials.csv": csv_bytes(materials),
        "data/materials/material_property_values.csv": csv_bytes(props),
        "data/materials/experiments.csv": csv_bytes(exps),
        "data/materials/formulations.csv": csv_bytes(forms),
        "data/materials/formulation_components.csv": csv_bytes(comps),
        "data/materials/process_steps.csv": csv_bytes(steps),
        "data/materials/measurements.csv": csv_bytes(measurements),
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for name, raw in {**legacy, **generated}.items():
            zf.writestr(name, raw)
    with zipfile.ZipFile(out) as zf:
        if zf.testzip():
            raise SystemExit("rebuilt integration ZIP failed CRC validation")
    print("Rebuilt PUR integration release: PASS")
    print(f"  Batch 005 sources               {len(sources)}")
    print(f"  Batch 005 materials             {len(materials)}")
    print(f"  Batch 005 material properties   {len(props)}")
    print(f"  Batch 005 RHM experiments       {len(exps)}")
    print(f"  Batch 005 RHM measurements      {len(measurements)}")
    print(f"  output                          {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
