from __future__ import annotations

import csv, hashlib, json, re, sqlite3
from pathlib import Path
from typing import Mapping

BATCH_RE = re.compile(r"batch(\d{3})", re.I)
NUM_RE = re.compile(r"^\s*(<=|>=|<|>|~|≈)?\s*([-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)\s*$")
REL_HINTS = ("contrast", "series", "pair", "amplification", "link", "overlap", "audit")
OUTCOME_HINTS = ("viscos", "open_time", "green_strength", "peel", "lap_shear", "bond_strength", "tensile", "elongation", "modulus", "shore", "creep", "density", "setting_time", "set_time", "crystall", "enthalpy", "softening", "yield_strength", "storage_modulus", "free_nco", "actual_nco", "measured_nco", "water_content", "acid_value", "oh_value")


def pick(row: Mapping[str, str], *names: str) -> str | None:
    for name in names:
        value = row.get(name)
        if value is not None and str(value).strip():
            return str(value).strip()
    return None


def parse_num(value: str | None) -> tuple[float | None, str | None]:
    if value is None:
        return None, None
    m = NUM_RE.match(str(value))
    return (float(m.group(2)), m.group(1) or None) if m else (None, None)


def known_source(conn: sqlite3.Connection, source_id: str | None) -> str | None:
    if not source_id:
        return None
    return source_id if conn.execute("SELECT 1 FROM sources WHERE source_id=?", (source_id,)).fetchone() else None


def upsert_source(conn: sqlite3.Connection, row: Mapping[str, str]) -> None:
    sid, title, stype = pick(row, "source_id"), pick(row, "title"), pick(row, "source_type")
    if not (sid and title and stype):
        return
    pub = pick(row, "publication_number", "patent_number")
    quality = pick(row, "quality_level")
    if quality not in {"A", "B", "C", "D"}:
        quality = None
    vals = {
        "source_id": sid, "source_type": stype, "title": title,
        "authors": pick(row, "authors"),
        "institution": pick(row, "institution", "assignee_or_institution"),
        "journal_or_publisher": pick(row, "journal_or_publisher", "publisher", "assignee_or_institution"),
        "year": pick(row, "year"), "language": pick(row, "language"), "doi": pick(row, "doi"),
        "patent_number": pub if stype.lower() == "patent" else pick(row, "patent_number"),
        "publication_number": pub, "source_url": pick(row, "source_url", "url"),
        "access_date": pick(row, "access_date"), "quality_level": quality,
        "extraction_status": pick(row, "extraction_status"), "notes": pick(row, "notes"),
    }
    cols = list(vals)
    qcols = ",".join(f'"{c}"' for c in cols)
    placeholders = ",".join("?" for _ in cols)
    updates = ",".join(f'"{c}"=COALESCE(excluded."{c}",sources."{c}")' for c in cols if c != "source_id")
    conn.execute(f"INSERT INTO sources ({qcols}) VALUES ({placeholders}) ON CONFLICT(source_id) DO UPDATE SET {updates}", [vals[c] or None for c in cols])


def record_type(name: str) -> str:
    s = name.lower()
    if "sources" in s: return "source_registry"
    if "method" in s or "protocol" in s: return "method"
    if any(h in s for h in REL_HINTS): return "relationship"
    if "material" in s or "polyol" in s or "polyester" in s: return "material_or_property"
    if "formulation" in s or "benchmark" in s or "performance" in s: return "formulation_or_performance"
    if "peel" in s or "shear" in s or "strength" in s: return "performance"
    return "dataset_record"


def entity_key(row: Mapping[str, str]) -> str | None:
    return pick(row, "record_id", "pair_id", "contrast_id", "series_id", "link_id", "sample_id", "formulation_id", "material_id", "experiment_id", "source_id", "example_label", "grade")


def evidence(row: Mapping[str, str]) -> str | None:
    return pick(row, "evidence_locator", "evidence_location", "source_location", "source_table", "table", "table_id", "source_section", "source_page")


def unit_for(field: str) -> str | None:
    f = field.lower()
    for suffix, unit in (("_mpa_s","mPa.s"),("_pa_s","Pa.s"),("_cps","cP"),("_psi","psi"),("_pli","pli"),("_mpa","MPa"),("_kg_cm","kg/cm"),("_g_ml","g/mL"),("_g_cm3","g/cm3"),("_j_g","J/g"),("_wt_pct","wt.%"),("_pct","%"),("_min","min"),("_c","degC")):
        if f.endswith(suffix): return unit
    return None


def temperature_for(field: str, row: Mapping[str, str]) -> float | None:
    m = re.search(r"(?:^|_)(\d{2,3}(?:\.\d+)?)c(?:_|$)", field.lower())
    if m: return float(m.group(1))
    if "viscos" in field.lower():
        return parse_num(pick(row, "viscosity_temperature_c", "prepolymer_viscosity_temperature_c", "temperature_c"))[0]
    return None


def time_for(field: str) -> tuple[float | None, str | None]:
    m = re.search(r"(?:^|_)(\d+(?:\.\d+)?)(min|h|hr|d|day|days)(?:_|$)", field.lower())
    if not m: return None, None
    u = m.group(2)
    return float(m.group(1)), ("h" if u in {"h","hr"} else "d" if u in {"d","day","days"} else "min")


def is_outcome(field: str) -> bool:
    f = field.lower()
    if "nco_oh" in f or "oh_nco" in f: return False
    return any(h in f for h in OUTCOME_HINTS)


def project_method(conn: sqlite3.Connection, row: Mapping[str, str]) -> None:
    pid, sid = pick(row, "method_id", "protocol_id"), known_source(conn, pick(row, "source_id"))
    if not (pid and sid): return
    conn.execute("INSERT OR REPLACE INTO protocols(protocol_id,source_id,protocol_type,method_standard,parameters_json,evidence_locator,notes) VALUES (?,?,?,?,?,?,?)", (pid, sid, pick(row,"measurement_or_process","protocol_type"), pick(row,"apparatus_or_standard","method_standard"), json.dumps(dict(row),ensure_ascii=False,sort_keys=True), evidence(row), pick(row,"semantic_note","notes")))


def project_measurements(conn: sqlite3.Connection, record_id: str, filename: str, row: Mapping[str, str]) -> int:
    sid = known_source(conn, pick(row, "source_id"))
    if not sid: return 0
    sample = pick(row, "sample_id", "formulation_id", "example_id", "example_label", "material_id", "grade")
    count = 0
    for field, raw in row.items():
        if not str(raw or "").strip() or not is_outcome(field): continue
        value, qualifier = parse_num(str(raw))
        t, tu = time_for(field)
        mid = "STG_" + hashlib.sha1(f"{record_id}|{field}".encode()).hexdigest()[:24]
        stage_text = (filename + " " + field).lower()
        stage = "prepolymer" if "prepolymer" in stage_text else "raw_material" if ("polyol" in stage_text or "material" in stage_text) else "hot_melt" if any(x in stage_text for x in ("purhm","hot_melt","peel","shear","green_strength","open_time","formulation")) else "unknown"
        conn.execute("""INSERT OR REPLACE INTO measurements(measurement_id,source_id,sample_id,measurement_stage,property_name_raw,property_name_normalized,value,qualifier,unit,original_value,original_unit,temperature_c,time_value,time_unit,evidence_type,evidence_locator,extraction_method,notes) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (mid,sid,sample,stage,field,field,value,qualifier,unit_for(field),str(raw),unit_for(field),temperature_for(field,row),t,tu,"reported",evidence(row),"staging_csv_lossless_import",f"Projected from {filename}; exact row retained in batch_records."))
        count += 1
    return count


def import_staging_batches(conn: sqlite3.Connection, root: Path, start_batch: int = 6, end_batch: int = 16) -> dict[str, int]:
    data = root / "data" / "materials"
    files: list[tuple[int, Path]] = []
    for path in sorted(data.glob("*.csv")):
        m = BATCH_RE.search(path.name)
        if m and start_batch <= int(m.group(1)) <= end_batch:
            files.append((int(m.group(1)), path))

    source_rows: dict[int, list[dict[str,str]]] = {}
    for num, path in files:
        if "sources" not in path.name.lower(): continue
        with path.open(encoding="utf-8-sig", newline="") as fh: rows = list(csv.DictReader(fh))
        source_rows.setdefault(num, []).extend(rows)
        for row in rows: upsert_source(conn, row)

    for num in range(start_batch, end_batch + 1):
        bid = f"BATCH_{num:03d}"; doc = data / f"BATCH_{num:03d}.md"; srcs = source_rows.get(num, [])
        conn.execute("INSERT OR REPLACE INTO batch_registry(batch_id,batch_number,integration_status,document_path,record_count,source_count,integrated_date,notes) VALUES (?,?,?,?,?,?,date('now'),?)", (bid,num,"integrating",str(doc.relative_to(root)) if doc.exists() else None,0,len({r.get('source_id') for r in srcs if r.get('source_id')}),"Registered before row import."))

    stats = {"files":0,"records":0,"values":0,"relations":0,"measurements":0,"protocols":0}
    batch_counts = {n:0 for n in range(start_batch,end_batch+1)}
    for num, path in files:
        bid = f"BATCH_{num:03d}"; stats["files"] += 1
        with path.open(encoding="utf-8-sig", newline="") as fh:
            for rowno, row in enumerate(csv.DictReader(fh), start=2):
                clean = {k:(v or "") for k,v in row.items()}
                payload = json.dumps(clean,ensure_ascii=False,sort_keys=True,separators=(",",":")); sha = hashlib.sha256(payload.encode()).hexdigest()
                rid = f"{bid}:{path.name}:{rowno}"; sid = pick(clean,"source_id")
                if not sid and len(source_rows.get(num,[])) == 1: sid = pick(source_rows[num][0],"source_id")
                sid = known_source(conn,sid)
                conn.execute("INSERT OR REPLACE INTO batch_records(batch_record_id,batch_id,source_id,file_name,record_type,row_number,entity_key,evidence_locator,payload_json,payload_sha256) VALUES (?,?,?,?,?,?,?,?,?,?)", (rid,bid,sid,path.name,record_type(path.name),rowno,entity_key(clean),evidence(clean),payload,sha))
                stats["records"] += 1; batch_counts[num] += 1
                for field, raw in clean.items():
                    if not str(raw).strip(): continue
                    n,q = parse_num(str(raw)); conn.execute("INSERT OR REPLACE INTO batch_record_values(batch_record_id,field_name,value_text,numeric_value,qualifier) VALUES (?,?,?,?,?)", (rid,field,str(raw),n,q)); stats["values"] += 1
                if record_type(path.name) == "method": project_method(conn,clean); stats["protocols"] += 1
                stats["measurements"] += project_measurements(conn,rid,path.name,clean)
                if any(h in path.name.lower() for h in REL_HINTS):
                    rawid = pick(clean,"contrast_id","series_id","pair_id","link_id","record_id") or f"{path.name}:{rowno}"
                    members = {k:v for k,v in clean.items() if v and any(h in k.lower() for h in ("member","sample","control","modified","baseline","source_example","existing_record","from_","to_"))}
                    conn.execute("INSERT OR REPLACE INTO controlled_relations(relation_id,batch_id,source_id,relation_type,members_json,evidence_strength,evidence_locator,payload_json,notes) VALUES (?,?,?,?,?,?,?,?,?)", (f"{bid}:{rawid}",bid,sid,path.stem,json.dumps(members,ensure_ascii=False,sort_keys=True),pick(clean,"evidence_strength"),evidence(clean),payload,pick(clean,"notes")))
                    stats["relations"] += 1

    for num in range(start_batch,end_batch+1):
        bid=f"BATCH_{num:03d}"; srcs=source_rows.get(num,[])
        conn.execute("UPDATE batch_registry SET integration_status='integrated_lossless_plus_canonical',record_count=?,source_count=?,integrated_date=date('now'),notes=? WHERE batch_id=?", (batch_counts[num],len({r.get('source_id') for r in srcs if r.get('source_id')}),"Every committed staging CSV row is preserved in batch_records; sources, methods and recognized outcome fields are also projected into canonical tables.",bid))
    return stats
