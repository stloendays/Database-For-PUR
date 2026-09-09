#!/usr/bin/env python3
"""Export safe ML/Agent views from pur_master_v2.db."""
from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from collections import defaultdict
from pathlib import Path


def write_query_csv(conn: sqlite3.Connection, path: Path, query: str) -> int:
    cur = conn.execute(query)
    cols = [d[0] for d in cur.description]
    data = cur.fetchall()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        w.writerows(data)
    return len(data)


def export_formulation_matrix(conn: sqlite3.Connection, path: Path) -> int:
    conn.row_factory = sqlite3.Row
    forms = {r["formulation_id"]: dict(r) for r in conn.execute("SELECT * FROM formulations ORDER BY formulation_id")}
    comps: dict[str, list[dict]] = defaultdict(list)
    for r in conn.execute("SELECT * FROM formulation_components ORDER BY formulation_id, component_record_id"):
        comps[r["formulation_id"]].append(dict(r))
    meas: dict[str, list[dict]] = defaultdict(list)
    for r in conn.execute("SELECT * FROM measurements WHERE formulation_id IS NOT NULL ORDER BY formulation_id, measurement_id"):
        meas[r["formulation_id"]].append(dict(r))

    fields = [
        "formulation_id", "source_id", "sample_id", "material_class", "application",
        "formulation_basis", "nco_oh_index", "target_nco_pct", "actual_nco_pct",
        "free_nco_pct", "composition_completeness", "component_count", "measurement_count",
        "components_json", "measurements_json",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for fid, r in forms.items():
            w.writerow({
                "formulation_id": fid,
                "source_id": r.get("source_id"),
                "sample_id": r.get("sample_id"),
                "material_class": r.get("material_class"),
                "application": r.get("application"),
                "formulation_basis": r.get("formulation_basis"),
                "nco_oh_index": r.get("nco_oh_index"),
                "target_nco_pct": r.get("target_nco_pct"),
                "actual_nco_pct": r.get("actual_nco_pct"),
                "free_nco_pct": r.get("free_nco_pct"),
                "composition_completeness": r.get("composition_completeness"),
                "component_count": len(comps[fid]),
                "measurement_count": len(meas[fid]),
                "components_json": json.dumps(comps[fid], ensure_ascii=False, sort_keys=True),
                "measurements_json": json.dumps(meas[fid], ensure_ascii=False, sort_keys=True),
            })
    return len(forms)


def export_decisions(conn: sqlite3.Connection, path: Path) -> int:
    conn.row_factory = sqlite3.Row
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as fh:
        for b in conn.execute("SELECT * FROM decision_benchmarks ORDER BY benchmark_id"):
            candidates = [dict(r) for r in conn.execute(
                "SELECT * FROM decision_candidates WHERE benchmark_id=? ORDER BY rank IS NULL, rank, candidate_id",
                (b["benchmark_id"],),
            )]
            obj = dict(b)
            obj["condition"] = json.loads(obj.pop("condition_json") or "{}")
            obj["constraints"] = json.loads(obj.pop("constraints_json") or "{}")
            obj["candidates"] = candidates
            fh.write(json.dumps(obj, ensure_ascii=False, sort_keys=True) + "\n")
            count += 1
    return count


def export_rag(conn: sqlite3.Connection, path: Path) -> int:
    conn.row_factory = sqlite3.Row
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as fh:
        for r in conn.execute("SELECT document_id,source_id,doc_type,title,content,metadata_json FROM rag_fts ORDER BY document_id"):
            obj = dict(r)
            try:
                obj["metadata"] = json.loads(obj.pop("metadata_json") or "{}")
            except json.JSONDecodeError:
                obj["metadata"] = {"raw": obj.pop("metadata_json")}
            fh.write(json.dumps(obj, ensure_ascii=False, sort_keys=True) + "\n")
            count += 1
    return count


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="database/pur_master_v2.db")
    ap.add_argument("--out-dir", default="exports/v2")
    args = ap.parse_args()

    db = Path(args.db)
    out = Path(args.out_dir)
    conn = sqlite3.connect(db)

    counts = {}
    counts["paired_amplification.csv"] = write_query_csv(conn, out / "paired_amplification.csv", "SELECT * FROM paired_measurements ORDER BY batch_id, pair_id")
    counts["exact_same_temperature_amplification.csv"] = write_query_csv(conn, out / "exact_same_temperature_amplification.csv", "SELECT * FROM v_exact_viscosity_amplification ORDER BY batch_id, pair_id")
    counts["controlled_contrasts.csv"] = write_query_csv(conn, out / "controlled_contrasts.csv", """
        SELECT c.*, o.metric_name, o.value_a, o.value_b, o.raw_a, o.raw_b, o.unit,
               o.delta_b_minus_a, o.ratio_b_over_a, o.temperature_c, o.time_value, o.time_unit
        FROM controlled_contrasts c
        LEFT JOIN controlled_contrast_outcomes o USING (contrast_id)
        ORDER BY c.batch_id, c.contrast_id, o.metric_name
    """)
    counts["staging_manifest.csv"] = write_query_csv(conn, out / "staging_manifest.csv", "SELECT batch_id,batch_name,status,source_file_count,record_count,integrated_at,notes FROM staging_batches ORDER BY batch_id")
    counts["record_equivalence.csv"] = write_query_csv(conn, out / "record_equivalence.csv", "SELECT * FROM record_equivalence ORDER BY batch_id, equivalence_id")
    counts["ml_formulation_matrix.csv"] = export_formulation_matrix(conn, out / "ml_formulation_matrix.csv")
    counts["decision_benchmarks.jsonl"] = export_decisions(conn, out / "decision_benchmarks.jsonl")

    fts_exists = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='rag_fts'").fetchone()
    if fts_exists:
        counts["rag_documents.jsonl"] = export_rag(conn, out / "rag_documents.jsonl")

    conn.close()
    print("PUR v2 exports: PASS")
    for name, n in counts.items():
        print(f"  {name:<42} {n}")


if __name__ == "__main__":
    main()
