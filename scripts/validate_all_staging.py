#!/usr/bin/env python3
"""Run every committed Batch 006+ staging validator in numeric order."""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
PATTERN = re.compile(r"validate_batch(\d+)\.py$")


def batch_number(path: Path) -> int:
    match = PATTERN.search(path.name)
    return int(match.group(1)) if match else -1


def main() -> None:
    validators = [p for p in SCRIPTS.glob("validate_batch*.py") if batch_number(p) >= 6]
    validators.sort(key=batch_number)
    if not validators:
        raise SystemExit("no Batch 006+ validators found")

    failures: list[tuple[str, int]] = []
    print(f"running {len(validators)} staging validators")
    for path in validators:
        label = f"Batch {batch_number(path):03d}"
        print(f"\n=== {label}: {path.name} ===")
        result = subprocess.run([sys.executable, str(path)], cwd=ROOT, check=False)
        if result.returncode:
            failures.append((path.name, result.returncode))

    print("\n=== staging validation summary ===")
    print(f"validators: {len(validators)}")
    print(f"passed:     {len(validators) - len(failures)}")
    print(f"failed:     {len(failures)}")
    if failures:
        for name, code in failures:
            print(f"  FAIL {name} (exit {code})")
        raise SystemExit(1)
    print("all staging validators passed")


if __name__ == "__main__":
    main()
