#!/usr/bin/env python3
"""Print an auditable structural inventory of recoverable Chinese seed rows."""
from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path

import rebuild_cn_release_salvage as s


def short(value: str | None, n: int = 120) -> str:
    text = (value or "").replace("\n", " ").replace("\r", " ")
    return text if len(text) <= n else text[: n - 3] + "..."


def build_store():
    store = defaultdict(list)
    archives = sorted(
        p for p in s.RELEASES.glob("cn_seed_batch_*.zip")
        if "rebuilt" not in p.name and "recovered" not in p.name
    )
    for archive in archives:
        batch = s.batch_no(archive)
        for member, raw, mode in s.archive_fragments(archive):
            if member.startswith("data/cn/") and member.endswith(".csv"):
                s.add_fragment(store, Path(member).name, raw, batch, 0, f"{archive.name}:{mode}")
    direct = [
        (2, 10, "sources.csv"),
        (3, 20, "batch003_sources.csv"),
        (4, 20, "batch004_sources.csv"),
        (3, 20, "batch003_measurements.csv"),
        (4, 20, "batch004_measurements.csv"),
        (4, 30, "standard_index.csv"),
        (4, 30, "thesis_index.csv"),
    ]
    for batch, rank, name in direct:
        path = s.CN / name
        if not path.exists():
            continue
        canonical = name.split("_", 1)[1] if name.startswith(("batch003_", "batch004_")) else name
        s.add_fragment(store, canonical, path.read_bytes(), batch, rank, f"data/cn/{name}")
    return store


def rows_for(store, filename):
    if filename not in store:
        return []
    raw, _ = s.merge_table(filename, store[filename])
    return s.parse(raw)[1]


def main() -> None:
    store = build_store()

    print("\n=== RECOVERED EXPERIMENTS ===")
    for r in rows_for(store, "experiments.csv"):
        print(" | ".join([
            r.get("experiment_id", ""), r.get("source_id", ""),
            r.get("sample_id", ""), r.get("example_number", ""),
            r.get("sample_type", ""), short(r.get("description"), 80),
        ]))

    print("\n=== RECOVERED FORMULATIONS ===")
    for r in rows_for(store, "formulations.csv"):
        print(" | ".join([
            r.get("formulation_id", ""), r.get("source_id", ""),
            r.get("experiment_id", ""), r.get("sample_id", ""),
            r.get("formulation_basis", ""), r.get("total_reported_amount", ""),
            r.get("nco_oh_index", ""), r.get("actual_nco_pct", ""),
        ]))

    print("\n=== COMPONENT COUNTS BY FORMULATION ===")
    components = rows_for(store, "formulation_components.csv")
    cc = Counter(r.get("formulation_id", "") for r in components)
    for k in sorted(cc):
        print(f"{k} | components={cc[k]}")

    print("\n=== PROCESS COUNTS BY LINK ===")
    process = rows_for(store, "process_steps.csv")
    pc = Counter((r.get("experiment_id", ""), r.get("formulation_id", "")) for r in process)
    for (eid, fid), n in sorted(pc.items()):
        print(f"{eid} | {fid} | steps={n}")

    print("\n=== RECOVERED PATENTS ===")
    for r in rows_for(store, "patents.csv"):
        print(" | ".join([
            r.get("patent_id", ""), r.get("source_id", ""),
            r.get("publication_number", ""), r.get("grant_number", ""),
            r.get("applicant", ""),
        ]))

    print("\n=== RECOVERED PROTOCOLS ===")
    for r in rows_for(store, "protocols.csv"):
        print(" | ".join([
            r.get("protocol_id", ""), r.get("source_id", ""),
            r.get("protocol_type", ""), r.get("method_standard", ""),
            short(r.get("parameters_json"), 100),
        ]))

    print("\n=== RECOVERED EVIDENCE ===")
    for r in rows_for(store, "evidence.csv"):
        print(" | ".join([
            r.get("evidence_id", ""), r.get("source_id", ""),
            r.get("experiment_id", ""), r.get("entity_type", ""),
            r.get("entity_id", ""), r.get("evidence_type", ""),
            short(r.get("evidence_locator"), 70), short(r.get("excerpt"), 110),
        ]))

    print("\n=== SOURCE COVERAGE IN RELATIONAL TABLES ===")
    source_ids = [r.get("source_id", "") for r in rows_for(store, "sources.csv")]
    tables = ["experiments.csv", "formulations.csv", "measurements.csv", "patents.csv", "protocols.csv", "evidence.csv"]
    table_rows = {t: rows_for(store, t) for t in tables}
    for sid in source_ids:
        if not sid:
            continue
        counts = [sum(1 for r in table_rows[t] if r.get("source_id") == sid) for t in tables]
        print(sid + " | " + " | ".join(f"{t[:-4]}={n}" for t, n in zip(tables, counts)))


if __name__ == "__main__":
    main()
