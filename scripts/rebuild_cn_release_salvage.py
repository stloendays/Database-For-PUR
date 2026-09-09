#!/usr/bin/env python3
"""Byte-salvage and deterministically rebuild the Batch 004 Chinese PUR corpus.

This is stricter than ordinary ZIP repair. Historical seed archives were
truncated during binary publication. Complete ZIP members are CRC checked; for
the first truncated deflate member, only the decompressed prefix ending at the
last complete CSV record is retained. Recovered rows are then unioned by the
original primary key across Batch 001/002/004 and committed Batch 003/004 text
deltas. The rebuild is accepted only when every documented Batch 004 cumulative
row count matches exactly.
"""
from __future__ import annotations

import argparse
import csv
import io
import re
import struct
import zlib
import zipfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CN = ROOT / "data" / "cn"
RELEASES = ROOT / "releases"

EXPECTED = {
    "evidence.csv": 58,
    "experiments.csv": 42,
    "formulation_components.csv": 252,
    "formulations.csv": 41,
    "measurements.csv": 131,
    "patents.csv": 10,
    "process_steps.csv": 137,
    "protocols.csv": 29,
    "sources.csv": 36,
    "standard_index.csv": 8,
    "thesis_index.csv": 10,
}

KEYS = {
    "evidence.csv": "evidence_id",
    "experiments.csv": "experiment_id",
    "formulation_components.csv": "component_record_id",
    "formulations.csv": "formulation_id",
    "measurements.csv": "measurement_id",
    "patents.csv": "patent_id",
    "process_steps.csv": "process_step_id",
    "protocols.csv": "protocol_id",
    "sources.csv": "source_id",
    "standard_index.csv": "source_id",
    "thesis_index.csv": "source_id",
    "materials.csv": "material_id",
}

LOCAL = b"PK\x03\x04"


def batch_no(path: Path) -> int:
    m = re.search(r"batch_(\d{3})", path.name)
    return int(m.group(1)) if m else 0


def decode_name(raw: bytes, flags: int) -> str:
    return raw.decode("utf-8" if flags & 0x800 else "cp437")


def inflate_prefix(method: int, payload: bytes) -> tuple[bytes, bool]:
    if method == 0:
        return payload, True
    if method != 8:
        raise ValueError(f"unsupported compression method {method}")
    dec = zlib.decompressobj(-zlib.MAX_WBITS)
    raw = dec.decompress(payload)
    raw += dec.flush()
    return raw, dec.eof


def complete_csv_prefix(raw: bytes) -> bytes | None:
    """Return only a UTF-8 CSV prefix ending after a structurally complete row."""
    if not raw:
        return None
    # Try successively earlier newline boundaries. This handles a truncated row
    # containing an open quoted field without altering any earlier source bytes.
    ends = [i + 1 for i, b in enumerate(raw) if b == 0x0A]
    for end in reversed(ends):
        candidate = raw[:end]
        try:
            text = candidate.decode("utf-8-sig")
            parsed = list(csv.reader(io.StringIO(text, newline=""), strict=True))
        except (UnicodeDecodeError, csv.Error):
            continue
        if len(parsed) < 2:
            continue
        width = len(parsed[0])
        if width and all(len(r) == width for r in parsed[1:]):
            return candidate
    return None


def local_fragments(path: Path) -> list[tuple[str, bytes, str]]:
    data = path.read_bytes()
    out: list[tuple[str, bytes, str]] = []
    pos = 0
    while True:
        pos = data.find(LOCAL, pos)
        if pos < 0 or pos + 30 > len(data):
            break
        (
            _version, flags, method, _mtime, _mdate, crc_expected,
            compressed_size, uncompressed_size, name_len, extra_len,
        ) = struct.unpack_from("<HHHHHIIIHH", data, pos + 4)
        if flags & 0x08:
            print(f"  stop {path.name}: data descriptor at byte {pos}")
            break
        ns = pos + 30
        ne = ns + name_len
        ps = ne + extra_len
        pe = ps + compressed_size
        name = decode_name(data[ns:ne], flags)
        available_end = min(pe, len(data))
        payload = data[ps:available_end]
        try:
            raw, eof = inflate_prefix(method, payload)
        except (ValueError, zlib.error) as exc:
            print(f"  stop {path.name}:{name}: inflate error {exc}")
            break

        exact = (
            pe <= len(data)
            and eof
            and len(raw) == uncompressed_size
            and (zlib.crc32(raw) & 0xFFFFFFFF) == crc_expected
        )
        if exact:
            out.append((name, raw, "crc_verified"))
            pos = pe
            continue

        prefix = complete_csv_prefix(raw) if name.endswith(".csv") else None
        if prefix is not None:
            out.append((name, prefix, "truncated_prefix"))
            try:
                n = len(list(csv.DictReader(io.StringIO(prefix.decode("utf-8-sig"), newline=""))))
            except Exception:
                n = -1
            print(
                f"  salvaged {path.name}:{name}: {len(prefix)} bytes, "
                f"{n} complete rows; declared {uncompressed_size} bytes"
            )
        else:
            print(f"  stop {path.name}:{name}: no structurally complete CSV prefix")
        # The physical archive ends inside this member, so no later local member
        # can be trusted to exist.
        break
    return out


def archive_fragments(path: Path) -> list[tuple[str, bytes, str]]:
    try:
        with zipfile.ZipFile(path) as zf:
            bad = zf.testzip()
            if bad is not None:
                raise zipfile.BadZipFile(bad)
            return [(n, zf.read(n), "crc_verified") for n in zf.namelist() if not n.endswith("/")]
    except (zipfile.BadZipFile, EOFError):
        return local_fragments(path)


def parse(raw: bytes) -> tuple[list[str], list[dict[str, str]]]:
    text = raw.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text, newline=""))
    fields = list(reader.fieldnames or [])
    return fields, [dict(r) for r in reader]


def emit(fields: list[str], rows: list[dict[str, str]]) -> bytes:
    sio = io.StringIO(newline="")
    w = csv.DictWriter(sio, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
    w.writeheader()
    for row in rows:
        w.writerow({k: row.get(k, "") for k in fields})
    return sio.getvalue().encode("utf-8")


def add_fragment(
    store: dict[str, list[tuple[int, int, str, list[str], list[dict[str, str]]]]],
    filename: str,
    raw: bytes,
    batch: int,
    rank: int,
    label: str,
) -> None:
    if filename not in KEYS:
        return
    try:
        fields, rows = parse(raw)
    except Exception as exc:
        print(f"  skip {label}:{filename}: CSV parse error {exc}")
        return
    key = KEYS[filename]
    if key not in fields:
        print(f"  skip {label}:{filename}: missing key column {key}")
        return
    store[filename].append((batch, rank, label, fields, rows))


def merge_table(
    filename: str,
    fragments: list[tuple[int, int, str, list[str], list[dict[str, str]]]],
) -> tuple[bytes, list[str]]:
    key = KEYS[filename]
    fields: list[str] = []
    records: dict[str, dict[str, str]] = {}
    provenance: dict[str, str] = {}
    # Ascending batch/rank: later cumulative/delta records overwrite earlier rows
    # only when they share the exact original primary key.
    for batch, rank, label, flds, rows in sorted(fragments, key=lambda x: (x[0], x[1], x[2])):
        for f in flds:
            if f not in fields:
                fields.append(f)
        for row in rows:
            rid = (row.get(key) or "").strip()
            if not rid:
                continue
            records[rid] = row
            provenance[rid] = label
    labels = sorted(set(provenance.values()))
    return emit(fields, list(records.values())), labels


def write_zip(path: Path, files: dict[str, bytes]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for name in sorted(files):
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, files[name])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default="releases/cn_seed_batch_004_rebuilt.zip")
    args = ap.parse_args()
    output = ROOT / args.output

    store: dict[str, list[tuple[int, int, str, list[str], list[dict[str, str]]]]] = defaultdict(list)
    archives = sorted(
        p for p in RELEASES.glob("cn_seed_batch_*.zip")
        if "rebuilt" not in p.name and "recovered" not in p.name
    )
    for archive in archives:
        batch = batch_no(archive)
        frags = archive_fragments(archive)
        print(f"archive {archive.name}: {len(frags)} recoverable members")
        for member, raw, mode in frags:
            if member.startswith("data/cn/") and member.endswith(".csv"):
                add_fragment(store, Path(member).name, raw, batch, 0, f"{archive.name}:{mode}")

    # Text files committed outside the binary archives are preferred as later,
    # auditable deltas/cumulative indexes.
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
        path = CN / name
        if not path.exists():
            continue
        canonical_name = name
        if name.startswith("batch003_") or name.startswith("batch004_"):
            canonical_name = name.split("_", 1)[1]
        add_fragment(store, canonical_name, path.read_bytes(), batch, rank, f"data/cn/{name}")

    canonical: dict[str, bytes] = {}
    prov: dict[str, list[str]] = {}
    failures: list[str] = []
    for filename, expected in EXPECTED.items():
        if filename not in store:
            failures.append(f"missing {filename}")
            continue
        raw, labels = merge_table(filename, store[filename])
        canonical[filename] = raw
        prov[filename] = labels
        actual = len(parse(raw)[1])
        print(f"merged {filename:<30} rows={actual:>4} expected={expected:>4}")
        if actual != expected:
            failures.append(f"{filename}: {actual} != {expected}")

    if failures:
        print("Chinese cumulative byte-salvage rebuild: FAIL")
        for filename in sorted(canonical):
            print(f"  {filename}: {len(parse(canonical[filename])[1])} rows <- {'; '.join(prov[filename])}")
        for msg in failures:
            print(f"  ERROR {msg}")
        raise SystemExit(1)

    # Include any fully merged optional material table without inventing a target
    # row count, plus the original batch documentation.
    if "materials.csv" in store:
        canonical["materials.csv"], prov["materials.csv"] = merge_table("materials.csv", store["materials.csv"])

    files = {f"data/cn/{name}": raw for name, raw in canonical.items()}
    for md in ("BATCH_002.md", "BATCH_003.md", "BATCH_004.md"):
        p = CN / md
        if p.exists():
            files[f"data/cn/{md}"] = p.read_bytes()
    write_zip(output, files)
    with zipfile.ZipFile(output) as zf:
        bad = zf.testzip()
        if bad is not None:
            raise SystemExit(f"rebuilt ZIP CRC failure: {bad}")

    print("Chinese cumulative byte-salvage rebuild: PASS")
    for filename, expected in EXPECTED.items():
        print(f"  {filename:<30} {expected:>4} rows")
    print(f"  output: {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
