#!/usr/bin/env python3
"""Populate the SQLite FTS5 index from normalized PUR master tables."""
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
        "INSERT INTO rag_fts(document_id, source_id, doc_type, title, content, metadata_json) VALUES (?,?,?,?,?,?)",
        (document_id, source_id, doc_type, title, content,
         json.dumps(metadata, ensure_ascii=False, sort_keys=True)),
    )


def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone() is not None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("db")
    args = ap.parse_args()
    db = Path(args.db)
    if not db.exists():
        raise SystemExit(f"database not found: {db}")

    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    if not table_exists(conn, "rag_fts"):
        raise SystemExit("rag_fts table not found; build the database schema first")

    conn.execute("DELETE FROM rag_fts")
    counts: dict[str, int] = {}

    n = 0
    for r in conn.execute("SELECT * FROM sources"):
        title = clean(r["title"], r["title_en"] if "title_en" in r.keys() else None)
        content = clean(
            title, r["authors"] if "authors" in r.keys() else None,
            r["journal_or_publisher"] if "journal_or_publisher" in r.keys() else None,
            r["year"], r["doi"] if "doi" in r.keys() else None,
            r["patent_number"] if "patent_number" in r.keys() else None,
            r["standard_number"] if "standard_number" in r.keys() else None,
            r["notes"],
        )
        insert_doc(conn, f"source:{r['source_id']}", r["source_id"], "source", title, content,
                   {"source_type": r["source_type"], "source_url": r["source_url"]})
        n += 1
    counts["source"] = n

    if table_exists(conn, "materials"):
        n = 0
        for r in conn.execute("SELECT * FROM materials"):
            title = clean(r["supplier"], r["grade"], r["normalized_name"])
            content = clean(
                title, r["chemical_name"], r["cas_number"], r["category"], r["subcategory"],
                f"Mn={r['mn_g_mol']} g/mol" if r["mn_g_mol"] is not None else None,
                f"OH={r['oh_value_mg_koh_g']} mg KOH/g" if r["oh_value_mg_koh_g"] is not None else None,
                f"NCO={r['nco_pct']} wt%" if r["nco_pct"] is not None else None,
                f"Tg={r['tg_c']} C" if r["tg_c"] is not None else None,
                r["notes"],
            )
            insert_doc(conn, f"material:{r['material_id']}", r["source_id"], "material", title, content,
                       {"material_id": r["material_id"], "supplier": r["supplier"], "grade": r["grade"]})
            n += 1
        counts["material"] = n

    if table_exists(conn, "experiments"):
        n = 0
        for r in conn.execute("SELECT * FROM experiments"):
            title = clean(r["sample_id"], r["example_number"], r["sample_type"])
            content = clean(title, r["description"], r["evidence_locator"], r["notes"])
            insert_doc(conn, f"experiment:{r['experiment_id']}", r["source_id"], "experiment", title, content,
                       {"experiment_id": r["experiment_id"], "quality_level": r["quality_level"]})
            n += 1
        counts["experiment"] = n

    if table_exists(conn, "formulations"):
        n = 0
        query = """
        SELECT f.*, GROUP_CONCAT(
            COALESCE(fc.component_name_normalized, fc.component_name_raw) || '=' ||
            COALESCE(CAST(fc.amount AS TEXT), CAST(fc.wt_pct AS TEXT), '?') ||
            COALESCE(' ' || fc.unit, ''), '; '
        ) AS components_text
        FROM formulations f
        LEFT JOIN formulation_components fc ON fc.formulation_id=f.formulation_id
        GROUP BY f.formulation_id
        """
        for r in conn.execute(query):
            title = clean(r["sample_id"], r["formulation_id"], r["application"])
            content = clean(
                title, r["material_class"], r["formulation_basis"], r["components_text"],
                f"NCO/OH={r['nco_oh_index']}" if r["nco_oh_index"] is not None else None,
                f"free NCO={r['free_nco_pct']} wt%" if r["free_nco_pct"] is not None else None,
                r["composition_completeness"], r["evidence_locator"], r["notes"],
            )
            insert_doc(conn, f"formulation:{r['formulation_id']}", r["source_id"], "formulation", title, content,
                       {"formulation_id": r["formulation_id"], "experiment_id": r["experiment_id"]})
            n += 1
        counts["formulation"] = n

    if table_exists(conn, "measurements"):
        n = 0
        for r in conn.execute("SELECT * FROM measurements"):
            value_text = clean(r["qualifier"], r["value"], r["unit"])
            title = clean(r["sample_id"], r["property_name_normalized"], value_text)
            content = clean(
                title, r["property_name_raw"], r["measurement_stage"],
                f"temperature={r['temperature_c']} C" if r["temperature_c"] is not None else None,
                f"time={r['time_value']} {r['time_unit']}" if r["time_value"] is not None else None,
                r["condition"], r["method_or_standard"], r["substrate_1"], r["substrate_2"],
                r["failure_mode"], r["evidence_type"], r["evidence_locator"], r["notes"],
            )
            insert_doc(conn, f"measurement:{r['measurement_id']}", r["source_id"], "measurement", title, content,
                       {"measurement_id": r["measurement_id"], "formulation_id": r["formulation_id"],
                        "experiment_id": r["experiment_id"], "quality_level": r["quality_level"]})
            n += 1
        counts["measurement"] = n

    if table_exists(conn, "evidence"):
        n = 0
        for r in conn.execute("SELECT * FROM evidence"):
            title = clean(r["entity_type"], r["entity_id"], r["evidence_type"])
            content = clean(title, r["excerpt"], r["evidence_locator"], r["notes"])
            insert_doc(conn, f"evidence:{r['evidence_id']}", r["source_id"], "evidence", title, content,
                       {"evidence_id": r["evidence_id"], "verified": r["verified"],
                        "quality_level": r["quality_level"]})
            n += 1
        counts["evidence"] = n

    conn.commit()
    total = conn.execute("SELECT COUNT(*) FROM rag_fts").fetchone()[0]
    conn.close()
    print(f"rag_fts documents: {total}")
    for kind, n in counts.items():
        print(f"  {kind:<14} {n}")


if __name__ == "__main__":
    main()
