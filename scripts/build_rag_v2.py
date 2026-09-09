#!/usr/bin/env python3
"""Extend rag_fts with v2 scientific relationships and Agent benchmarks."""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path


def clean(*parts: object) -> str:
    return " | ".join(str(x).strip() for x in parts if x is not None and str(x).strip())


def insert_doc(conn: sqlite3.Connection, document_id: str, source_id: str | None,
               doc_type: str, title: str, content: str, metadata: dict) -> None:
    conn.execute(
        "INSERT INTO rag_fts(document_id,source_id,doc_type,title,content,metadata_json) VALUES (?,?,?,?,?,?)",
        (document_id, source_id, doc_type, title, content, json.dumps(metadata, ensure_ascii=False, sort_keys=True)),
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("db")
    args = ap.parse_args()
    db = Path(args.db)
    if not db.exists():
        raise SystemExit(f"database not found: {db}")

    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if "rag_fts" not in tables:
        raise SystemExit("rag_fts missing; run build_rag_fts.py first")

    v2_types = ("paired_measurement", "controlled_contrast", "series", "scientific_link", "decision_benchmark")
    placeholders = ",".join("?" for _ in v2_types)
    conn.execute(f"DELETE FROM rag_fts WHERE doc_type IN ({placeholders})", v2_types)
    counts = {}

    n = 0
    for r in conn.execute("SELECT * FROM paired_measurements ORDER BY batch_id,pair_id"):
        title = clean(r["pair_type"], r["precursor_id"], "->", r["product_id"])
        content = clean(
            title,
            f"precursor viscosity={r['precursor_value']} {r['precursor_unit']} @ {r['precursor_temperature_c']} C",
            f"product viscosity={r['product_value']} {r['product_unit']} @ {r['product_temperature_c']} C",
            f"same_temperature={r['same_temperature']}",
            f"composition_match={r['composition_match_class']}",
            f"amplification={r['derived_ratio']}",
            f"isocyanate={r['isocyanate']}",
            f"isocyanate_index={r['isocyanate_index']}",
            f"target_nco_pct={r['target_nco_pct']}",
            r["evidence_locator"], r["notes"],
        )
        insert_doc(conn, f"pair:{r['pair_id']}", r["source_id"], "paired_measurement", title, content,
                   {"pair_id": r["pair_id"], "batch_id": r["batch_id"], "evidence_strength": r["evidence_strength"]})
        n += 1
    counts["paired_measurement"] = n

    n = 0
    q = """
    SELECT c.*, GROUP_CONCAT(
      o.metric_name || ': ' || COALESCE(o.raw_a, CAST(o.value_a AS TEXT), '?') ||
      ' -> ' || COALESCE(o.raw_b, CAST(o.value_b AS TEXT), '?') ||
      CASE WHEN o.ratio_b_over_a IS NOT NULL THEN ' ratio=' || CAST(o.ratio_b_over_a AS TEXT) ELSE '' END,
      '; '
    ) AS outcomes_text
    FROM controlled_contrasts c
    LEFT JOIN controlled_contrast_outcomes o USING (contrast_id)
    GROUP BY c.contrast_id
    ORDER BY c.batch_id,c.contrast_id
    """
    for r in conn.execute(q):
        title = clean(r["contrast_class"], r["sample_a"], "vs", r["sample_b"])
        content = clean(title, f"changed={r['changed_factors']}", f"held={r['held_factors']}",
                        r["outcomes_text"], f"evidence={r['evidence_strength']}", r["evidence_locator"], r["notes"])
        insert_doc(conn, f"contrast:{r['contrast_id']}", r["source_id"], "controlled_contrast", title, content,
                   {"contrast_id": r["contrast_id"], "batch_id": r["batch_id"], "evidence_strength": r["evidence_strength"]})
        n += 1
    counts["controlled_contrast"] = n

    n = 0
    for r in conn.execute("SELECT * FROM series_definitions ORDER BY batch_id,series_id"):
        title = clean(r["series_type"], r["series_id"])
        content = clean(title, f"members={r['members_json']}", f"held={r['held_features']}",
                        f"covarying={r['covarying_features']}", f"outcomes={r['primary_outcomes']}",
                        f"evidence={r['evidence_strength']}", r["notes"])
        insert_doc(conn, f"series:{r['series_id']}", r["source_id"], "series", title, content,
                   {"series_id": r["series_id"], "batch_id": r["batch_id"]})
        n += 1
    counts["series"] = n

    n = 0
    for r in conn.execute("SELECT * FROM scientific_links ORDER BY batch_id,link_id"):
        title = clean(r["link_type"], r["entity_a"], "->", r["entity_b"])
        content = clean(title, r["metric_a"], r["metric_b"], f"derived={r['derived_value']}",
                        r["derived_semantics"], f"evidence={r['evidence_strength']}", r["notes"])
        insert_doc(conn, f"link:{r['link_id']}", r["source_id"], "scientific_link", title, content,
                   {"link_id": r["link_id"], "batch_id": r["batch_id"]})
        n += 1
    counts["scientific_link"] = n

    n = 0
    for b in conn.execute("SELECT * FROM decision_benchmarks ORDER BY benchmark_id"):
        candidates = [dict(r) for r in conn.execute(
            "SELECT candidate_id,objective_value,unit,feasible,rank,is_optimal FROM decision_candidates WHERE benchmark_id=? ORDER BY rank IS NULL,rank,candidate_id",
            (b["benchmark_id"],),
        )]
        title = b["title"]
        content = clean(
            title,
            f"objective={b['objective_direction']} {b['objective_name']} {b['objective_unit']}",
            f"condition={b['condition_json']}", f"constraints={b['constraints_json']}",
            f"ground_truth={b['ground_truth_candidate_id']}", f"candidates={json.dumps(candidates, ensure_ascii=False)}",
            b["notes"],
        )
        insert_doc(conn, f"benchmark:{b['benchmark_id']}", b["source_id"], "decision_benchmark", title, content,
                   {"benchmark_id": b["benchmark_id"], "batch_id": b["batch_id"], "ground_truth": b["ground_truth_candidate_id"]})
        n += 1
    counts["decision_benchmark"] = n

    conn.commit()
    total = conn.execute("SELECT COUNT(*) FROM rag_fts").fetchone()[0]
    conn.close()
    print(f"rag_fts total documents after v2 extension: {total}")
    for kind, n in counts.items():
        print(f"  {kind:<24} {n}")


if __name__ == "__main__":
    main()
