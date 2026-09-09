#!/usr/bin/env python3
"""Recover a ZIP whose central directory is missing but local entries are intact.

Every recovered entry is decompressed and checked against its local-header CRC and
uncompressed size before a clean ZIP is written. Healthy ZIP files are copied as-is.
"""
from __future__ import annotations

import argparse
import binascii
import struct
import zipfile
import zlib
from pathlib import Path

LOCAL_SIG = b"PK\x03\x04"
CENTRAL_SIG = b"PK\x01\x02"
EOCD_SIG = b"PK\x05\x06"


def recover(src: Path, dst: Path) -> list[tuple[str, int, int]]:
    data = src.read_bytes()
    pos = 0
    recovered: list[tuple[str, int, int]] = []
    dst.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(dst, "w", compression=zipfile.ZIP_DEFLATED) as out:
        while pos + 4 <= len(data):
            sig = data[pos : pos + 4]
            if sig in (CENTRAL_SIG, EOCD_SIG):
                break
            if sig != LOCAL_SIG:
                nxt = data.find(LOCAL_SIG, pos + 1)
                if nxt < 0:
                    break
                pos = nxt
                continue

            if pos + 30 > len(data):
                raise ValueError(f"truncated local header at byte {pos}")

            (
                _sig,
                _version,
                flag,
                method,
                _mtime,
                _mdate,
                crc32_expected,
                compressed_size,
                uncompressed_size,
                name_len,
                extra_len,
            ) = struct.unpack_from("<4s5H3I2H", data, pos)

            if flag & 0x08:
                raise ValueError(
                    f"entry at byte {pos} uses a data descriptor; cannot safely recover without the central directory"
                )

            name_start = pos + 30
            name_end = name_start + name_len
            payload_start = name_end + extra_len
            payload_end = payload_start + compressed_size
            if payload_end > len(data):
                raise ValueError(f"truncated payload for entry at byte {pos}")

            encoding = "utf-8" if flag & 0x800 else "cp437"
            name = data[name_start:name_end].decode(encoding)
            compressed = data[payload_start:payload_end]

            if method == 0:
                raw = compressed
            elif method == 8:
                raw = zlib.decompress(compressed, -15)
            else:
                raise ValueError(f"unsupported compression method {method} for {name}")

            crc32_actual = binascii.crc32(raw) & 0xFFFFFFFF
            if crc32_actual != crc32_expected:
                raise ValueError(
                    f"CRC mismatch for {name}: {crc32_actual:08x} != {crc32_expected:08x}"
                )
            if len(raw) != uncompressed_size:
                raise ValueError(
                    f"size mismatch for {name}: {len(raw)} != {uncompressed_size}"
                )

            out.writestr(name, raw)
            recovered.append((name, compressed_size, uncompressed_size))
            pos = payload_end

    if not recovered:
        raise ValueError("no recoverable local ZIP entries found")

    with zipfile.ZipFile(dst) as rebuilt:
        bad = rebuilt.testzip()
        if bad:
            raise ValueError(f"rebuilt archive failed CRC test at {bad}")

    return recovered


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    args = ap.parse_args()

    src = Path(args.src)
    dst = Path(args.dst)

    if zipfile.is_zipfile(src):
        with zipfile.ZipFile(src) as zf:
            bad = zf.testzip()
            if bad:
                raise SystemExit(f"input ZIP has CRC failure: {bad}")
            names = zf.namelist()
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(src.read_bytes())
        print(f"ZIP already healthy: {src} ({len(names)} entries)")
        return

    recovered = recover(src, dst)
    print(f"Recovered {len(recovered)} entries from local ZIP headers: {src} -> {dst}")
    for name, compressed_size, uncompressed_size in recovered:
        print(f"  {name}: {compressed_size} -> {uncompressed_size} bytes")


if __name__ == "__main__":
    main()
