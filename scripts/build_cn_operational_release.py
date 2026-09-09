#!/usr/bin/env python3
"""Build an FK-closed operational Chinese release without inventing lost facts.

The historical Batch 002/004 ZIPs are truncated. We preserve every recoverable
row, then create only two kinds of minimal structural records:

* experiment/formulation parents whose IDs are already referenced by preserved
  measurement rows; and
* patent index rows whose publication identity is already present in a preserved
  source row.

No component amount, process condition, protocol parameter, performance value or
evidence excerpt is synthesized. Missing auxiliary rows remain missing and are
reported in ``data/cn/recovery_status.csv`` inside the release.
"""
from __future__ import annotations

import argparse
import csv
import io
from pathlib import Path

import audit_cn_recovery as audit
import rebuild_cn_release_salvage as s

CORE_EXPECTED = {
    "sources.csv": 36,
    "experiments.csv": 42,
    "formulations.csv": 41,
    "measurements.csv": 131,
    "patents.csv": 10,
    "standard_index.csv": 8,
    "thesis_index.csv": 10,
}
AUX_EXPECTED = {
    "formulation_components.csv": 252,
    "process_steps.csv": 137,
    "protocols.csv": 29,
    "evidence.csv": 58,
}


def table(store, name: str) -> tuple[list[str], list[dict[str, str]]]:
    if name not in store:
        return [], []
    raw, _ = s.merge_table(name, store[name])
    return s.parse(raw)


def ensure_field(fields: list[str], name: str) -> None:
    if name not in fields:
        fields.append(name)


def add_parent_stubs(
    exp_fields: list[str],
    experiments: list[dict[str, str]],
    form_fields: list[str],
    formulations: list[dict[str, str]],
    measurements: list[dict[str, str]],
) -> tuple[int, int]:
    for f in (
        "experiment_id", "source_id", "sample_id", "sample_type", "description",
        "evidence_locator", "quality_level", "notes",
    ):
        ensure_field(exp_fields, f)
    for f in (
        "formulation_id", "experiment_id", "source_id", "sample_id",
        "formulation_basis", "composition_completeness", "evidence_locator", "notes",
    ):
        ensure_field(form_fields, f)

    exp_by_id = {r.get("experiment_id", ""): r for r in experiments if r.get("experiment_id")}
    form_by_id = {r.get("formulation_id", ""): r for r in formulations if r.get("formulation_id")}
    exp_added = 0
    form_added = 0

    # One row per preserved child ID. The child already proves the parent identity,
    # source link and sample label; all unavailable descriptive fields remain blank.
    for m in measurements:
        eid = (m.get("experiment_id") or "").strip()
        if eid and eid not in exp_by_id:
            row = {f: "" for f in exp_fields}
            row.update({
                "experiment_id": eid,
                "source_id": m.get("source_id", ""),
                "sample_id": m.get("sample_id", ""),
                "sample_type": "unknown",
                "description": "Structural parent restored from preserved measurement reference",
                "evidence_locator": m.get("evidence_locator", ""),
                "quality_level": m.get("quality_level", ""),
                "notes": "recovery_parent_stub; no experimental detail inferred",
            })
            experiments.append(row)
            exp_by_id[eid] = row
            exp_added += 1

        fid = (m.get("formulation_id") or "").strip()
        if fid and fid not in form_by_id:
            row = {f: "" for f in form_fields}
            row.update({
                "formulation_id": fid,
                "experiment_id": eid,
                "source_id": m.get("source_id", ""),
                "sample_id": m.get("sample_id", ""),
                "formulation_basis": "recovered structural parent only",
                "composition_completeness": "unknown",
                "evidence_locator": m.get("evidence_locator", ""),
                "notes": "recovery_parent_stub; component composition intentionally not inferred",
            })
            formulations.append(row)
            form_by_id[fid] = row
            form_added += 1

    return exp_added, form_added


def add_patent_stubs(
    source_rows: list[dict[str, str]],
    patent_fields: list[str],
    patents: list[dict[str, str]],
) -> int:
    for f in (
        "patent_id", "source_id", "application_number", "publication_number",
        "grant_number", "priority_date", "filing_date", "publication_date",
        "applicant", "inventors", "family_id", "jurisdiction", "notes",
    ):
        ensure_field(patent_fields, f)
    existing_sources = {r.get("source_id", "") for r in patents}
    existing_ids = {r.get("patent_id", "") for r in patents}
    added = 0
    for src in source_rows:
        source_id = (src.get("source_id") or "").strip()
        source_type = (src.get("source_type") or "").strip().lower()
        is_patent = source_type.startswith("patent") or source_id.startswith("CN_PAT_")
        pub = (src.get("publication_number") or src.get("patent_number") or "").strip()
        # The historical source key itself encodes the official publication number,
        # e.g. CN_PAT_CN111217992A. This fallback is identity reconstruction only;
        # no bibliographic or experimental metadata is inferred from it.
        if not pub and source_id.startswith("CN_PAT_"):
            pub = source_id.removeprefix("CN_PAT_")
        if not is_patent or not source_id or not pub or source_id in existing_sources:
            continue
        pid = f"PAT_{pub}"
        if pid in existing_ids:
            continue
        row = {f: "" for f in patent_fields}
        row.update({
            "patent_id": pid,
            "source_id": source_id,
            "publication_number": pub,
            "grant_number": pub if pub.endswith("B") else "",
            "jurisdiction": "CN",
            "notes": "recovery_patent_stub; identity reconstructed only from preserved source metadata",
        })
        patents.append(row)
        existing_sources.add(source_id)
        existing_ids.add(pid)
        added += 1
    return added


def csv_bytes(fields: list[str], rows: list[dict[str, str]]) -> bytes:
    sio = io.StringIO(newline="")
    w = csv.DictWriter(sio, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
    w.writeheader()
    for row in rows:
        w.writerow({k: row.get(k, "") for k in fields})
    return sio.getvalue().encode("utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default="releases/cn_seed_batch_004_operational.zip")
    args = ap.parse_args()
    output = s.ROOT / args.output

    store = audit.build_store()
    source_fields, sources = table(store, "sources.csv")
    exp_fields, experiments = table(store, "experiments.csv")
    form_fields, formulations = table(store, "formulations.csv")
    meas_fields, measurements = table(store, "measurements.csv")
    patent_fields, patents = table(store, "patents.csv")

    raw_exp = len(experiments)
    raw_form = len(formulations)
    raw_pat = len(patents)
    exp_stubs, form_stubs = add_parent_stubs(
        exp_fields, experiments, form_fields, formulations, measurements
    )
    patent_stubs = add_patent_stubs(sources, patent_fields, patents)

    core = {
        "sources.csv": (source_fields, sources),
        "experiments.csv": (exp_fields, experiments),
        "formulations.csv": (form_fields, formulations),
        "measurements.csv": (meas_fields, measurements),
        "patents.csv": (patent_fields, patents),
    }
    for name in ("standard_index.csv", "thesis_index.csv"):
        core[name] = table(store, name)

    failures: list[str] = []
    for name, expected in CORE_EXPECTED.items():
        actual = len(core[name][1])
        print(f"core {name:<30} {actual:>4}/{expected}")
        if actual != expected:
            failures.append(f"{name}: {actual} != {expected}")
    if failures:
        for failure in failures:
            print(f"ERROR {failure}")
        raise SystemExit("operational Chinese release cannot close verified core identities")

    files: dict[str, bytes] = {
        f"data/cn/{name}": csv_bytes(fields, rows)
        for name, (fields, rows) in core.items()
    }

    status_rows: list[dict[str, str | int]] = []
    for name, expected in AUX_EXPECTED.items():
        fields, rows = table(store, name)
        actual = len(rows)
        files[f"data/cn/{name}"] = csv_bytes(fields, rows)
        status_rows.append({
            "table_name": name[:-4],
            "documented_batch004_rows": expected,
            "operational_rows": actual,
            "missing_rows": expected - actual,
            "status": "complete" if actual == expected else "historical_metadata_deficit",
            "policy": "no missing factual rows synthesized; re-extraction required",
        })
        print(f"aux  {name:<30} {actual:>4}/{expected} deficit={expected-actual}")

    # Machine-readable provenance for the three structurally reconstructed core layers.
    status_rows.extend([
        {
            "table_name": "experiments",
            "documented_batch004_rows": CORE_EXPECTED["experiments.csv"],
            "operational_rows": len(experiments),
            "missing_rows": 0,
            "status": "fk_closed_with_parent_stubs",
            "policy": f"{raw_exp} original rows + {exp_stubs} parent stubs from preserved measurement IDs",
        },
        {
            "table_name": "formulations",
            "documented_batch004_rows": CORE_EXPECTED["formulations.csv"],
            "operational_rows": len(formulations),
            "missing_rows": 0,
            "status": "fk_closed_with_parent_stubs",
            "policy": f"{raw_form} original rows + {form_stubs} parent stubs; no component amounts inferred",
        },
        {
            "table_name": "patents",
            "documented_batch004_rows": CORE_EXPECTED["patents.csv"],
            "operational_rows": len(patents),
            "missing_rows": 0,
            "status": "identity_index_reconstructed",
            "policy": f"{raw_pat} original rows + {patent_stubs} identity-only rows from preserved source metadata",
        },
    ])
    status_fields = [
        "table_name", "documented_batch004_rows", "operational_rows",
        "missing_rows", "status", "policy",
    ]
    files["data/cn/recovery_status.csv"] = csv_bytes(status_fields, status_rows)  # type: ignore[arg-type]

    for md in ("BATCH_002.md", "BATCH_003.md", "BATCH_004.md"):
        p = s.CN / md
        if p.exists():
            files[f"data/cn/{md}"] = p.read_bytes()

    s.write_zip(output, files)
    with zipfile.ZipFile(output) as zf:  # type: ignore[name-defined]
        bad = zf.testzip()
        if bad is not None:
            raise SystemExit(f"operational ZIP CRC failure: {bad}")

    print("Chinese operational recovery release: PASS")
    print(f"  experiment parent stubs: {exp_stubs}")
    print(f"  formulation parent stubs: {form_stubs}")
    print(f"  patent identity stubs: {patent_stubs}")
    print(f"  output: {output.relative_to(s.ROOT)}")


if __name__ == "__main__":
    import zipfile
    main()
