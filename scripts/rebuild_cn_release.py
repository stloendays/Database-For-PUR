#!/usr/bin/env python3
"""Rebuild the cumulative Chinese PUR release from recoverable seed archives.

Historical ``cn_seed_batch_*.zip`` files may have a damaged or truncated central
ZIP directory even when their local file entries are intact. This builder does
not trust the archive container. It:

1. reads every seed archive with ``zipfile`` when possible;
2. otherwise recovers complete local entries and validates size + CRC32;
3. chooses the most complete cumulative CSV candidate for each canonical table;
4. reconstructs sources/measurements from committed incremental CSVs when useful;
5. overlays the committed cumulative thesis/standard indexes;
6. requires the Batch 004 documented cumulative row counts; and
7. writes a deterministic, clean ZIP with a valid central directory.

No missing numerical rows are invented. If the documented Batch 004 totals
cannot be recovered exactly, the script fails instead of silently degrading the
Chinese corpus.
"""
from __future__ import annotations

import argparse
import csv
import io
import struct
import zlib
import zipfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CN_DIR = ROOT / "data" / "cn"
RELEASES = ROOT / "releases"

EXPECTED_ROWS = {
    "sources.csv": 36,
    "experiments.csv": 42,
    "formulation_components.csv": 252,
    "formulations.csv": 41,
    "measurements.csv": 131,
    "patents.csv": 10,
    "process_steps.csv": 137,
    "protocols.csv": 29,
    "evidence.csv": 58,
    "thesis_index.csv": 10,
    "standard_index.csv": 8,
}


def decode_name(raw: bytes, flags: int) -> str:
    encoding = "utf-8" if flags & 0x800 else "cp437"
    return raw.decode(encoding)


def inflate(method: int, payload: bytes) -> bytes:
    if method == 0:
        return payload
    if method == 8:
        return zlib.decompress(payload, -zlib.MAX_WBITS)
    raise ValueError(f"unsupported ZIP compression method {method}")


def recover_local_entries(path: Path) -> dict[str, bytes]:
    """Recover every complete local entry before the first damaged ZIP member.

    A damaged seed archive is treated as a prefix container: every entry admitted
    here has passed decompression, uncompressed-size and CRC32 checks. The first
    incomplete/corrupt member terminates recovery for that archive, but does not
    invalidate already verified entries because later seed archives may contain
    cumulative replacements.
    """
    data = path.read_bytes()
    out: dict[str, bytes] = {}
    pos = 0
    local_sig = b"PK\x03\x04"

    while True:
        pos = data.find(local_sig, pos)
        if pos < 0:
            break
        if pos + 30 > len(data):
            break

        (
            version,
            flags,
            method,
            _mtime,
            _mdate,
            crc32_expected,
            compressed_size,
            uncompressed_size,
            name_len,
            extra_len,
        ) = struct.unpack_from("<HHHHHIIIHH", data, pos + 4)
        _ = version

        if flags & 0x08:
            print(f"stop {path.name}: unsupported data-descriptor entry at byte {pos}")
            break

        name_start = pos + 30
        name_end = name_start + name_len
        payload_start = name_end + extra_len
        payload_end = payload_start + compressed_size
        if payload_end > len(data):
            print(f"stop {path.name}: truncated payload at byte {pos}")
            break

        name = decode_name(data[name_start:name_end], flags)
        payload = data[payload_start:payload_end]
        try:
            raw = inflate(method, payload)
        except (ValueError, zlib.error) as exc:
            print(f"stop {path.name}:{name}: decompression failed: {exc}")
            break
        if len(raw) != uncompressed_size:
            print(
                f"stop {path.name}:{name}: size mismatch "
                f"{len(raw)} != {uncompressed_size}"
            )
            break
        crc32_actual = zlib.crc32(raw) & 0xFFFFFFFF
        if crc32_actual != crc32_expected:
            print(
                f"stop {path.name}:{name}: CRC mismatch "
                f"{crc32_actual:08x} != {crc32_expected:08x}"
            )
            break
        if not name.endswith("/"):
            out[name] = raw
        pos = payload_end

    return out


def archive_entries(path: Path) -> tuple[dict[str, bytes], str]:
    try:
        with zipfile.ZipFile(path) as zf:
            bad = zf.testzip()
            if bad is not None:
                raise zipfile.BadZipFile(f"CRC failure in {bad}")
            return {n: zf.read(n) for n in zf.namelist() if not n.endswith("/")}, "central_directory"
    except (zipfile.BadZipFile, EOFError):
        recovered = recover_local_entries(path)
        if not recovered:
            raise SystemExit(f"no recoverable local entries in {path}")
        return recovered, "local_header_recovery"


def parse_csv_bytes(raw: bytes) -> tuple[list[str], list[dict[str, str]]]:
    text = raw.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text, newline=""))
    fieldnames = list(reader.fieldnames or [])
    return fieldnames, [dict(r) for r in reader]


def count_rows(raw: bytes) -> int:
    return len(parse_csv_bytes(raw)[1])


def write_csv_bytes(fieldnames: list[str], rows: list[dict[str, str]]) -> bytes:
    sio = io.StringIO(newline="")
    writer = csv.DictWriter(sio, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({k: row.get(k, "") for k in fieldnames})
    return sio.getvalue().encode("utf-8")


def merge_csv(base_raw: bytes | None, additions: list[Path], key: str) -> bytes | None:
    fieldnames: list[str] = []
    merged: dict[str, dict[str, str]] = {}
    anonymous: list[dict[str, str]] = []

    sources: list[bytes] = []
    if base_raw is not None:
        sources.append(base_raw)
    for path in additions:
        if path.exists():
            sources.append(path.read_bytes())
    if not sources:
        return None

    for raw in sources:
        fields, rows = parse_csv_bytes(raw)
        for field in fields:
            if field not in fieldnames:
                fieldnames.append(field)
        for row in rows:
            identifier = (row.get(key) or "").strip()
            if identifier:
                merged[identifier] = row
            else:
                anonymous.append(row)

    return write_csv_bytes(fieldnames, list(merged.values()) + anonymous)


def deterministic_zip(output: Path, files: dict[str, bytes]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        output.unlink()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for name in sorted(files):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, files[name])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default="releases/cn_seed_batch_004_rebuilt.zip")
    args = ap.parse_args()
    output = ROOT / args.output

    archives = sorted(RELEASES.glob("cn_seed_batch_*.zip"))
    archives = [p for p in archives if "rebuilt" not in p.name and "recovered" not in p.name]
    if not archives:
        raise SystemExit("no cn_seed_batch_*.zip archives found")

    candidates: dict[str, list[tuple[int, str, bytes]]] = defaultdict(list)
    recovery_modes: list[tuple[str, str, int]] = []

    for archive in archives:
        entries, mode = archive_entries(archive)
        recovery_modes.append((archive.name, mode, len(entries)))
        for member, raw in entries.items():
            if not member.startswith("data/cn/") or not member.endswith(".csv"):
                continue
            filename = Path(member).name
            try:
                nrows = count_rows(raw)
            except Exception as exc:
                print(f"skip malformed candidate {archive.name}::{member}: {exc}")
                continue
            candidates[filename].append((nrows, archive.name, raw))

    canonical: dict[str, bytes] = {}
    selected_from: dict[str, str] = {}
    for filename, choices in candidates.items():
        nrows, source, raw = max(choices, key=lambda x: (x[0], x[1]))
        canonical[filename] = raw
        selected_from[filename] = f"{source} ({nrows} rows)"

    source_base = (
        (CN_DIR / "sources.csv").read_bytes()
        if (CN_DIR / "sources.csv").exists()
        else canonical.get("sources.csv")
    )
    source_merged = merge_csv(
        source_base,
        [CN_DIR / "batch003_sources.csv", CN_DIR / "batch004_sources.csv"],
        "source_id",
    )
    if source_merged is not None and count_rows(source_merged) >= count_rows(canonical.get("sources.csv", b"\n")):
        canonical["sources.csv"] = source_merged
        selected_from["sources.csv"] = "committed Batch 002 base + Batch 003/004 source increments"

    measurement_merged = merge_csv(
        canonical.get("measurements.csv"),
        [CN_DIR / "batch003_measurements.csv", CN_DIR / "batch004_measurements.csv"],
        "measurement_id",
    )
    if measurement_merged is not None and count_rows(measurement_merged) >= count_rows(canonical.get("measurements.csv", b"\n")):
        canonical["measurements.csv"] = measurement_merged
        selected_from["measurements.csv"] = "best recovered cumulative table + committed Batch 003/004 measurement increments"

    for filename in ("thesis_index.csv", "standard_index.csv"):
        direct = CN_DIR / filename
        if direct.exists():
            canonical[filename] = direct.read_bytes()
            selected_from[filename] = f"committed data/cn/{filename}"

    failures: list[str] = []
    for filename, expected in EXPECTED_ROWS.items():
        raw = canonical.get(filename)
        if raw is None:
            failures.append(f"missing {filename} (expected {expected} rows)")
            continue
        actual = count_rows(raw)
        if actual != expected:
            failures.append(f"{filename}: {actual} rows != documented Batch 004 total {expected}")

    if failures:
        print("Chinese cumulative rebuild: FAIL")
        for name, mode, nentries in recovery_modes:
            print(f"  archive {name:<24} {mode:<24} entries={nentries}")
        for filename in sorted(canonical):
            try:
                print(
                    f"  candidate {filename:<30} rows={count_rows(canonical[filename]):>4} "
                    f"from {selected_from.get(filename, 'unknown')}"
                )
            except Exception:
                pass
        for failure in failures:
            print(f"  ERROR {failure}")
        raise SystemExit(1)

    files = {
        f"data/cn/{filename}": raw
        for filename, raw in canonical.items()
        if filename.endswith(".csv")
    }
    for md in ("BATCH_002.md", "BATCH_003.md", "BATCH_004.md"):
        path = CN_DIR / md
        if path.exists():
            files[f"data/cn/{md}"] = path.read_bytes()

    deterministic_zip(output, files)
    with zipfile.ZipFile(output) as zf:
        bad = zf.testzip()
        if bad is not None:
            raise SystemExit(f"rebuilt ZIP CRC failure: {bad}")

    print("Chinese cumulative rebuild: PASS")
    for name, mode, nentries in recovery_modes:
        print(f"  archive {name:<24} {mode:<24} entries={nentries}")
    for filename, expected in EXPECTED_ROWS.items():
        print(
            f"  {filename:<30} {expected:>4} rows <- "
            f"{selected_from.get(filename, 'recovered seed archive')}"
        )
    print(f"  output: {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
