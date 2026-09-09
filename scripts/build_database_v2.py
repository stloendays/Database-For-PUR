#!/usr/bin/env python3
"""Build Database-For-PUR v2 from the validated Batch 005 master plus Batch 006+ staging data.

Design goals:
- preserve every staging row losslessly as JSON;
- promote high-value scientific relationships into typed relational tables;
- keep patent-family duplicate mappings explicit;
- add small ground-truth decision benchmarks for Agent evaluation;
- never coerce censored or cross-temperature values into false exact measurements.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sqlite3
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATERIALS = ROOT / "data" / "materials"
V2_SCHEMA = ROOT / "schema" / "pur_v2_extensions.sql"
BATCH_RE = re.compile(r"batch(\d{3})", re.IGNORECASE)

OUTCOME_HINTS = (
    "viscos", "strength", "peel", "shear", "open_time", "density",
    "nco", "modulus", "tensile", "elongation", "hardness", "creep",
    "crystall", "softening", "setting", "set_time", "stability",
)

ID_KEYS = (
    "record_id", "pair_id", "contrast_id", "link_id", "series_id",
    "formulation_id", "material_id", "measurement_id", "method_id",
    "sample_id", "example_id", "product_example_id", "source_example",
)


def rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return [dict(r) for r in csv.DictReader(fh)]


def f(value: object) -> float | None:
    if value is None:
        return None
    s = str(value).strip().replace(",", "")
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def batch_from_path(path: Path) -> int | None:
    m = BATCH_RE.search(path.name)
    return int(m.group(1)) if m else None


def json_text(obj: object) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True)


def native_id(row: dict[str, str], index: int) -> str:
    for key in ID_KEYS:
        value = (row.get(key) or "").strip()
        if value:
            if key == "series_id" and row.get("example_id"):
                return f"{value}:{row['example_id']}"
            return value
    return f"row_{index:04d}"


def import_batch_sources(conn: sqlite3.Connection) -> int:
    added = 0
    for path in sorted(MATERIALS.glob("batch*_sources.csv")):
        batch = batch_from_path(path)
        if batch is None or batch < 6:
            continue
        for r in rows(path):
            source_id = (r.get("source_id") or "").strip()
            source_type = (r.get("source_type") or "").strip()
            title = (r.get("title") or "").strip()
            if not source_id or not source_type or not title:
                continue
            pub = (r.get("publication_number") or "").strip()
            notes_parts = [x for x in [(r.get("notes") or "").strip()] if x]
            if r.get("patent_family"):
                notes_parts.append(f"Patent family: {r['patent_family']}")
            before = conn.total_changes
            conn.execute(
                """
                INSERT OR IGNORE INTO sources(
                  source_id, source_type, title, authors, institution,
                  journal_or_publisher, year, language, doi, patent_number,
                  publication_number, source_url, access_date, quality_level,
                  extraction_status, notes
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    source_id, source_type, title, r.get("authors") or None,
                    r.get("institution") or r.get("assignee_or_institution") or None,
                    r.get("journal_or_publisher") or r.get("publisher") or None,
                    f(r.get("year")), r.get("language") or None, r.get("doi") or None,
                    pub if source_type == "patent" and pub else r.get("patent_number") or None,
                    pub or None, r.get("source_url") or None, r.get("access_date") or None,
                    r.get("quality_level") or None, r.get("extraction_status") or None,
                    " | ".join(notes_parts) or None,
                ),
            )
            if conn.total_changes > before:
                added += 1
    return added


def ingest_staging(conn: sqlite3.Connection) -> tuple[int, int]:
    by_batch_files: dict[int, int] = defaultdict(int)
    by_batch_rows: dict[int, int] = defaultdict(int)
    total = 0
    now = datetime.now(timezone.utc).isoformat()

    csv_paths = []
    for path in MATERIALS.glob("*.csv"):
        batch = batch_from_path(path)
        if batch is not None and batch >= 6:
            csv_paths.append(path)

    documented = set()
    for md in MATERIALS.glob("BATCH_*.md"):
        m = re.search(r"BATCH_(\d{3})", md.name)
        if m and int(m.group(1)) >= 6:
            documented.add(int(m.group(1)))

    file_rows: list[tuple[Path, int, list[dict[str, str]]]] = []
    for path in sorted(csv_paths):
        batch = batch_from_path(path)
        assert batch is not None
        rws = rows(path)
        by_batch_files[batch] += 1
        by_batch_rows[batch] += len(rws)
        file_rows.append((path, batch, rws))

    all_batches = sorted(documented | set(by_batch_files))
    for batch in all_batches:
        conn.execute(
            """
            INSERT OR REPLACE INTO staging_batches(
              batch_id, batch_name, status, source_file_count, record_count, integrated_at, notes
            ) VALUES (?,?,?,?,?,?,?)
            """,
            (
                batch, f"Batch {batch:03d}", "integrated_v2_staging",
                by_batch_files.get(batch, 0), by_batch_rows.get(batch, 0), now,
                "All CSV rows preserved losslessly in staging_records; selected relationships promoted into typed v2 tables.",
            ),
        )

    for path, batch, rws in file_rows:
        record_type = BATCH_RE.sub("", path.stem).strip("_-")
        for i, r in enumerate(rws, 1):
            nid = native_id(r, i)
            rid = f"B{batch:03d}:{path.stem}:{i:05d}"
            conn.execute(
                """
                INSERT OR REPLACE INTO staging_records(
                  staging_record_id, batch_id, source_file, record_type, source_id,
                  native_id, evidence_locator, quality_level, payload_json
                ) VALUES (?,?,?,?,?,?,?,?,?)
                """,
                (
                    rid, batch, str(path.relative_to(ROOT)), record_type,
                    r.get("source_id") or None, nid,
                    r.get("evidence_locator") or None,
                    r.get("quality_level") or r.get("evidence_strength") or r.get("control_quality") or None,
                    json_text(r),
                ),
            )
            total += 1
    return len(all_batches), total


def add_pair(conn: sqlite3.Connection, values: tuple) -> None:
    conn.execute(
        """
        INSERT OR REPLACE INTO paired_measurements(
          pair_id,batch_id,source_id,pair_type,series_id,precursor_id,product_id,
          precursor_stage,product_stage,property_name,precursor_value,precursor_unit,
          precursor_temperature_c,product_value,product_unit,product_temperature_c,
          same_temperature,composition_match_class,derived_ratio,derivation_status,
          isocyanate,isocyanate_index,target_nco_pct,reaction_method_id,
          evidence_strength,evidence_locator,notes,payload_json
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        values,
    )


def ingest_pairs(conn: sqlite3.Connection) -> int:
    n = 0
    path = MATERIALS / "prepolymer_pair_benchmarks_batch006.csv"
    if path.exists():
        for r in rows(path):
            pv, qv = f(r.get("polyol_viscosity_cp")), f(r.get("prepolymer_viscosity_cp"))
            pt, qt = f(r.get("polyol_viscosity_temperature_c")), f(r.get("prepolymer_viscosity_temperature_c"))
            same = int(pt is not None and qt is not None and abs(pt - qt) < 1e-9)
            ratio = qv / pv if same and pv not in (None, 0) and qv is not None else None
            add_pair(conn, (
                r["pair_id"], 6, r.get("source_id"), r.get("pair_type") or "single_polyol_mdi_prepolymer",
                None, r.get("polyol_grade"), r.get("pair_id"), "polyol", "MDI_prepolymer", "viscosity",
                pv, "cP", pt, qv, "cP", qt, same,
                "single_polyol_same_temperature" if same else "single_polyol_cross_temperature",
                ratio, "derived_exact_same_temperature" if ratio is not None else "not_derived_cross_temperature",
                r.get("isocyanate_name"), None, f(r.get("target_nco_pct")), None,
                r.get("quality_level"), r.get("evidence_locator"), r.get("notes"), json_text(r),
            ))
            n += 1

    path = MATERIALS / "evonik_matched_130c_amplification_batch007.csv"
    if path.exists():
        for r in rows(path):
            add_pair(conn, (
                r["record_id"], 7, r.get("source_id"), "single_polyol_mdi_prepolymer", None,
                r.get("material_id") or r.get("polyol_grade"), r.get("record_id"),
                r.get("precursor_stage"), r.get("product_stage"), "viscosity",
                f(r.get("precursor_viscosity_pa_s")), "Pa.s", f(r.get("precursor_temperature_c")),
                f(r.get("prepolymer_viscosity_pa_s")), "Pa.s", f(r.get("prepolymer_temperature_c")),
                int(f(r.get("same_temperature_pair")) or 0), "single_polyol_same_temperature",
                f(r.get("viscosity_amplification_factor")), r.get("factor_status"),
                r.get("isocyanate"), None, None, None, "A", r.get("evidence_locator"), r.get("notes"), json_text(r),
            ))
            n += 1

    path = MATERIALS / "us8394868_same_temp_amplification_batch011.csv"
    if path.exists():
        for r in rows(path):
            add_pair(conn, (
                r["record_id"], 11, r.get("source_id"), "polyol_blend_to_prepolymer",
                r.get("series_id"), r.get("reference_id"), r.get("product_example_id"),
                "polyol_blend", "urethane_prepolymer", "viscosity",
                f(r.get("precursor_viscosity_mpa_s")), "mPa.s", f(r.get("precursor_temperature_c")),
                f(r.get("prepolymer_viscosity_mpa_s")), "mPa.s", f(r.get("prepolymer_temperature_c")),
                int(f(r.get("same_temperature_pair")) or 0), r.get("composition_match_class"),
                f(r.get("viscosity_amplification_factor")), r.get("factor_status"),
                r.get("isocyanate"), f(r.get("isocyanate_index")), None, r.get("reaction_method_id"),
                "A", r.get("evidence_locator"), r.get("notes"), json_text(r),
            ))
            n += 1
    return n


def infer_unit(metric: str) -> str | None:
    suffixes = [
        ("_mpa_s", "mPa.s"), ("_pa_s", "Pa.s"), ("_cps", "cP"),
        ("_kg_cm", "kg/cm"), ("_psi", "psi"), ("_pli", "pli"),
        ("_g_ml", "g/mL"), ("_wt_pct", "wt.%"), ("_pct", "%"),
        ("_min", "min"), ("_h", "h"),
    ]
    for suffix, unit in suffixes:
        if metric.endswith(suffix):
            return unit
    return None


def metric_context(metric: str) -> tuple[float | None, float | None, str | None]:
    temp = None
    time_value = None
    time_unit = None
    mt = re.search(r"_(\d+(?:\.\d+)?)c(?:_|$)", metric)
    if mt:
        temp = float(mt.group(1))
    mm = re.search(r"_(\d+(?:\.\d+)?)min(?:_|$)", metric)
    mh = re.search(r"_(\d+(?:\.\d+)?)h(?:_|$)", metric)
    if mm:
        time_value, time_unit = float(mm.group(1)), "min"
    elif mh:
        time_value, time_unit = float(mh.group(1)), "h"
    return temp, time_value, time_unit


def outcome_ok(metric: str) -> bool:
    low = metric.lower()
    return any(h in low for h in OUTCOME_HINTS)


def insert_outcome(conn: sqlite3.Connection, contrast_id: str, metric: str,
                   raw_a: str | None, raw_b: str | None, ratio_only: float | None = None) -> int:
    if not outcome_ok(metric):
        return 0
    va, vb = f(raw_a), f(raw_b)
    delta = vb - va if va is not None and vb is not None else None
    ratio = vb / va if va not in (None, 0) and vb is not None else ratio_only
    temp, time_value, time_unit = metric_context(metric)
    oid = f"{contrast_id}:{metric}"
    conn.execute(
        """
        INSERT OR REPLACE INTO controlled_contrast_outcomes(
          outcome_id,contrast_id,metric_name,value_a,value_b,raw_a,raw_b,unit,
          delta_b_minus_a,ratio_b_over_a,temperature_c,time_value,time_unit,notes
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (oid, contrast_id, metric, va, vb, raw_a or None, raw_b or None, infer_unit(metric),
         delta, ratio, temp, time_value, time_unit, "Derived only when both source values are numeric."),
    )
    return 1


def paired_outcomes(conn: sqlite3.Connection, contrast_id: str, r: dict[str, str]) -> int:
    n = 0
    used: set[str] = set()
    for key in list(r):
        if key.startswith("baseline_"):
            metric = key[len("baseline_"):]
            other = "variant_" + metric
            if other in r and metric not in {"record_id", "polyester"}:
                n += insert_outcome(conn, contrast_id, metric, r.get(key), r.get(other))
                used.update({key, other})
    for key in list(r):
        if key in used:
            continue
        if "_a_" in key:
            other = key.replace("_a_", "_b_", 1)
            if other in r:
                metric = key.replace("_a_", "_", 1)
                n += insert_outcome(conn, contrast_id, metric, r.get(key), r.get(other))
                used.update({key, other})
        elif key.endswith("_a"):
            other = key[:-2] + "_b"
            if other in r:
                metric = key[:-2]
                n += insert_outcome(conn, contrast_id, metric, r.get(key), r.get(other))
                used.update({key, other})
    for key, value in r.items():
        if key.endswith("_ratio_vs_control") and key not in used:
            metric = key[:-len("_ratio_vs_control")]
            ratio = f(value)
            if ratio is not None and outcome_ok(metric):
                oid = f"{contrast_id}:{metric}"
                temp, time_value, time_unit = metric_context(metric)
                conn.execute(
                    """
                    INSERT OR REPLACE INTO controlled_contrast_outcomes(
                      outcome_id,contrast_id,metric_name,ratio_b_over_a,temperature_c,time_value,time_unit,notes
                    ) VALUES (?,?,?,?,?,?,?,?)
                    """,
                    (oid, contrast_id, metric, ratio, temp, time_value, time_unit,
                     "Source-file ratio versus control; absolute values live in the linked formulation/measurement table."),
                )
                n += 1
    return n


def contrast_files() -> list[Path]:
    return sorted(MATERIALS.glob("*controlled_contrasts_batch*.csv"))


def ingest_contrasts(conn: sqlite3.Connection) -> tuple[int, int]:
    nc = no = 0
    for path in contrast_files():
        batch = batch_from_path(path)
        if batch is None or batch < 6:
            continue
        for r in rows(path):
            cid = (r.get("contrast_id") or "").strip()
            if not cid:
                continue
            a = r.get("baseline_record_id") or r.get("sample_a") or r.get("control_sample")
            b = r.get("variant_record_id") or r.get("sample_b") or r.get("modified_sample")
            cclass = r.get("contrast_type") or r.get("contrast_class") or "controlled_contrast"
            changed = (
                r.get("primary_composition_change") or r.get("controlled_axis") or
                r.get("changed_factors") or r.get("main_change") or
                (f"microsphere dose = {r.get('microsphere_wt_pct')} wt.%" if r.get("microsphere_wt_pct") else None)
            )
            held = (
                r.get("approximately_held_constant") or r.get("near_held_factors") or
                r.get("controlled_features")
            )
            strength = r.get("evidence_strength") or r.get("control_quality") or r.get("control_confidence")
            conn.execute(
                """
                INSERT OR REPLACE INTO controlled_contrasts(
                  contrast_id,batch_id,source_id,sample_a,sample_b,contrast_class,
                  changed_factors,held_factors,evidence_strength,evidence_locator,notes,payload_json
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (cid, batch, r.get("source_id"), a, b, cclass, changed, held, strength,
                 r.get("evidence_locator"), r.get("notes"), json_text(r)),
            )
            nc += 1
            no += paired_outcomes(conn, cid, r)
    return nc, no


def ingest_series(conn: sqlite3.Connection) -> int:
    n = 0
    path = MATERIALS / "us8394868_controlled_index_series_batch011.csv"
    if path.exists():
        grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
        for r in rows(path):
            grouped[r["series_id"]].append(r)
        for sid, group in grouped.items():
            members = [r.get("example_id") for r in group if r.get("example_id")]
            conn.execute(
                """
                INSERT OR REPLACE INTO series_definitions(
                  series_id,batch_id,source_id,series_type,members_json,held_features,
                  covarying_features,primary_outcomes,evidence_strength,notes,payload_json
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
                """,
                (sid, 11, group[0].get("source_id"), "controlled_isocyanate_index_series",
                 json_text(members), "same 50/50 VORANOL CP 3008 / NOPB A precursor blend; same 70 C / 6 h reaction protocol",
                 "TDI index and TDI loading", "prepolymer viscosity at 25 C; viscosity amplification vs unreacted blend",
                 "very_high", "Exact same precursor blend; controlled TDI-index sweep.", json_text(group)),
            )
            n += 1

    path = MATERIALS / "us6136136_controlled_series_batch015.csv"
    if path.exists():
        for r in rows(path):
            members = [x for x in (r.get("members") or "").split(";") if x]
            conn.execute(
                """
                INSERT OR REPLACE INTO series_definitions(
                  series_id,batch_id,source_id,series_type,members_json,held_features,
                  covarying_features,primary_outcomes,evidence_strength,notes,payload_json
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
                """,
                (r["series_id"], 15, r.get("source_id"), r.get("series_type") or "controlled_series",
                 json_text(members), r.get("held_or_near_held_features"), r.get("co_varying_features"),
                 r.get("primary_outcomes"), r.get("evidence_strength"), r.get("notes"), json_text(r)),
            )
            n += 1

    path = MATERIALS / "us20070155859_formulations_batch016.csv"
    if path.exists():
        rws = rows(path)
        members = [r["sample_id"] for r in rws]
        conn.execute(
            """
            INSERT OR REPLACE INTO series_definitions(
              series_id,batch_id,source_id,series_type,members_json,held_features,
              covarying_features,primary_outcomes,evidence_strength,notes,payload_json
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """,
            ("US20070155859_MICROSPHERE_DOSE", 16, rws[0].get("source_id") if rws else None,
             "controlled_additive_dose_series", json_text(members), "same commercial QR-4668 reactive PUR hot-melt base",
             "DUALITE E-136-040D hollow microsphere loading: 0/1/3/5 wt.%",
             "viscosity@121C; open_time; density; time-resolved cross_peel", "very_high",
             "Clean four-level additive-dose panel.", json_text(rws)),
        )
        n += 1
    return n


def ingest_scientific_links(conn: sqlite3.Connection) -> int:
    path = MATERIALS / "us6365700_mechanistic_links_batch013.csv"
    if not path.exists():
        return 0
    n = 0
    for r in rows(path):
        conn.execute(
            """
            INSERT OR REPLACE INTO scientific_links(
              link_id,batch_id,source_id,link_type,entity_a,entity_b,metric_a,metric_b,
              derived_value,derived_semantics,evidence_strength,notes,payload_json
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (r["link_id"], 13, r.get("source_id"), r.get("link_type") or "link",
             r.get("sample_a"), r.get("sample_b"), r.get("metric_a"), r.get("metric_b"),
             f(r.get("derived_value")), r.get("derived_semantics"), r.get("evidence_strength"),
             r.get("notes"), json_text(r)),
        )
        n += 1
    return n


def ingest_equivalence(conn: sqlite3.Connection) -> int:
    path = MATERIALS / "us6136136_family_overlap_batch015.csv"
    if not path.exists():
        return 0
    n = 0
    for i, r in enumerate(rows(path), 1):
        eid = f"B015_EQ_{i:03d}"
        conn.execute(
            """
            INSERT OR REPLACE INTO record_equivalence(
              equivalence_id,batch_id,source_id,source_record_id,canonical_source_id,
              canonical_record_id,overlap_status,matching_basis,action,payload_json
            ) VALUES (?,?,?,?,?,?,?,?,?,?)
            """,
            (eid, 15, r.get("source_id"), r.get("source_example"), r.get("existing_source_id"),
             r.get("existing_record_id"), r.get("overlap_status"), r.get("matching_basis"),
             r.get("action") or "review", json_text(r)),
        )
        n += 1
    return n


def rank_candidates(values: dict[str, float], direction: str, feasible: dict[str, bool] | None = None) -> dict[str, int | None]:
    feasible = feasible or {k: True for k in values}
    items = [(k, v) for k, v in values.items() if feasible.get(k, True)]
    items.sort(key=lambda kv: kv[1], reverse=(direction == "maximize"))
    ranks: dict[str, int | None] = {k: None for k in values}
    for i, (k, _) in enumerate(items, 1):
        ranks[k] = i
    return ranks


def add_benchmark(conn: sqlite3.Connection, *, benchmark_id: str, source_id: str, title: str,
                  objective_name: str, direction: str, unit: str, values: dict[str, float],
                  payloads: dict[str, dict], condition: dict | None = None,
                  constraints: dict | None = None, feasible: dict[str, bool] | None = None,
                  notes: str | None = None) -> None:
    feasible = feasible or {k: True for k in values}
    ranks = rank_candidates(values, direction, feasible)
    ranked = [(k, rank) for k, rank in ranks.items() if rank is not None]
    best = min(ranked, key=lambda x: x[1])[0] if ranked else None
    conn.execute(
        """
        INSERT OR REPLACE INTO decision_benchmarks(
          benchmark_id,batch_id,source_id,title,task_type,objective_name,objective_direction,
          objective_unit,condition_json,constraints_json,candidate_scope,ground_truth_candidate_id,notes
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (benchmark_id, 16, source_id, title, "candidate_selection", objective_name, direction, unit,
         json_text(condition or {}), json_text(constraints or {}), "US20070155859A1 EX1-EX4",
         best, notes),
    )
    for cid, value in values.items():
        conn.execute(
            """
            INSERT OR REPLACE INTO decision_candidates(
              benchmark_id,candidate_id,objective_value,objective_raw,unit,feasible,rank,is_optimal,candidate_payload_json
            ) VALUES (?,?,?,?,?,?,?,?,?)
            """,
            (benchmark_id, cid, value, str(value), unit, int(feasible.get(cid, True)), ranks[cid],
             int(cid == best), json_text(payloads.get(cid, {}))),
        )


def ingest_decision_benchmarks(conn: sqlite3.Connection) -> int:
    fpath = MATERIALS / "us20070155859_formulations_batch016.csv"
    ppath = MATERIALS / "us20070155859_cross_peel_batch016.csv"
    if not fpath.exists() or not ppath.exists():
        return 0
    form = {r["sample_id"]: r for r in rows(fpath)}
    peel_rows = rows(ppath)
    source_id = next(iter(form.values())).get("source_id") if form else "PAT_US20070155859A1"
    payloads = form
    n = 0

    def peel_at(minutes: float) -> dict[str, float]:
        out = {}
        for r in peel_rows:
            if f(r.get("time_after_assembly_min")) == minutes and f(r.get("cross_peel_strength_psi")) is not None:
                out[r["sample_id"]] = f(r["cross_peel_strength_psi"])
        return out

    for minutes in (5.0, 20.0):
        vals = peel_at(minutes)
        add_benchmark(
            conn, benchmark_id=f"B016_MAX_CROSSPEEL_{int(minutes)}MIN", source_id=source_id,
            title=f"Maximize cross-peel strength at {int(minutes)} min", objective_name="cross_peel_strength",
            direction="maximize", unit="psi", values=vals, payloads=payloads,
            condition={"time_after_assembly_min": minutes},
            notes="Ground truth derived directly from the four reported candidates in Table II.",
        )
        n += 1

    viscosity = {k: f(v.get("viscosity_cps")) for k, v in form.items()}
    viscosity = {k: v for k, v in viscosity.items() if v is not None}
    add_benchmark(conn, benchmark_id="B016_MIN_VISCOSITY_121C", source_id=source_id,
                  title="Minimize melt viscosity at 121 C", objective_name="viscosity_121c",
                  direction="minimize", unit="cP", values=viscosity, payloads=payloads,
                  condition={"temperature_c": 121}, notes="Single-property processability benchmark.")
    n += 1

    open_time = {k: f(v.get("open_time_min")) for k, v in form.items()}
    open_time = {k: v for k, v in open_time.items() if v is not None}
    add_benchmark(conn, benchmark_id="B016_MAX_OPEN_TIME", source_id=source_id,
                  title="Maximize source-defined open time", objective_name="open_time",
                  direction="maximize", unit="min", values=open_time, payloads=payloads,
                  notes="Method-specific open time; valid only within this source protocol.")
    n += 1

    density = {k: f(v.get("density_g_ml")) for k, v in form.items()}
    density = {k: v for k, v in density.items() if v is not None}
    add_benchmark(conn, benchmark_id="B016_MIN_DENSITY", source_id=source_id,
                  title="Minimize adhesive density", objective_name="density",
                  direction="minimize", unit="g/mL", values=density, payloads=payloads,
                  notes="Single-property density benchmark.")
    n += 1

    peel5 = peel_at(5.0)
    feas = {
        k: (f(form[k].get("viscosity_cps")) is not None and f(form[k].get("density_g_ml")) is not None
            and f(form[k].get("viscosity_cps")) <= 32000 and f(form[k].get("density_g_ml")) <= 0.90)
        for k in peel5
    }
    add_benchmark(conn, benchmark_id="B016_CONSTRAINED_5MIN_STRENGTH", source_id=source_id,
                  title="Maximize 5-min cross-peel under viscosity and density constraints",
                  objective_name="cross_peel_strength", direction="maximize", unit="psi",
                  values=peel5, payloads=payloads, condition={"time_after_assembly_min": 5},
                  constraints={"viscosity_cps_max": 32000, "density_g_ml_max": 0.90}, feasible=feas,
                  notes="Constraint benchmark is deterministic from the same four-candidate panel; EX3 is the unique feasible optimum.")
    n += 1

    feas2 = {k: f(form[k].get("open_time_min")) is not None and f(form[k].get("open_time_min")) >= 2.5 for k in peel5}
    add_benchmark(conn, benchmark_id="B016_OPEN_TIME_GATED_5MIN_STRENGTH", source_id=source_id,
                  title="Maximize 5-min cross-peel with open time at least 2.5 min",
                  objective_name="cross_peel_strength", direction="maximize", unit="psi",
                  values=peel5, payloads=payloads, condition={"time_after_assembly_min": 5},
                  constraints={"open_time_min_min": 2.5}, feasible=feas2,
                  notes="Tests whether an Agent respects a processability constraint instead of choosing the unconstrained 5-min maximum.")
    n += 1
    return n


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default="database/pur_master_v2.db")
    ap.add_argument("--base-output", default=None)
    args = ap.parse_args()

    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    base_output = ROOT / args.base_output if args.base_output else output

    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "build_database.py"), "--output", str(base_output.relative_to(ROOT))],
        cwd=ROOT, check=True,
    )
    if base_output != output:
        output.write_bytes(base_output.read_bytes())

    conn = sqlite3.connect(output)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(V2_SCHEMA.read_text(encoding="utf-8"))

    new_sources = import_batch_sources(conn)
    batch_count, staging_rows = ingest_staging(conn)
    pair_count = ingest_pairs(conn)
    contrast_count, outcome_count = ingest_contrasts(conn)
    series_count = ingest_series(conn)
    link_count = ingest_scientific_links(conn)
    equivalence_count = ingest_equivalence(conn)
    benchmark_count = ingest_decision_benchmarks(conn)

    conn.commit()
    integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
    fk = conn.execute("PRAGMA foreign_key_check").fetchall()
    conn.close()
    if integrity != "ok":
        raise SystemExit(f"integrity check failed: {integrity}")
    if fk:
        raise SystemExit(f"foreign-key violations: {fk[:10]}")

    print("PUR master v2 build: PASS")
    print(f"  Batch 006+ source identities added: {new_sources}")
    print(f"  staging batches:                   {batch_count}")
    print(f"  staging rows preserved:            {staging_rows}")
    print(f"  paired measurements:               {pair_count}")
    print(f"  controlled contrasts:              {contrast_count}")
    print(f"  contrast outcomes:                 {outcome_count}")
    print(f"  series definitions:                {series_count}")
    print(f"  scientific links:                  {link_count}")
    print(f"  record equivalence mappings:       {equivalence_count}")
    print(f"  decision benchmarks:               {benchmark_count}")
    print(f"  output: {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
