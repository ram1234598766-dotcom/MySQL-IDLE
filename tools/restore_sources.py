#!/usr/bin/env python3
"""Restore the initial compressed source payload once, then remove it."""
from __future__ import annotations

import base64
import io
import tarfile
from pathlib import Path

ROOT = Path.cwd().resolve()
PAYLOAD_DIR = ROOT / "bootstrap"
PART_PATTERN = "mysql_idle_sources.part-*"


def main() -> None:
    parts = sorted(PAYLOAD_DIR.glob(PART_PATTERN)) if PAYLOAD_DIR.exists() else []
    if not parts:
        if (ROOT / "mysql_idle.py").is_file() and (ROOT / "mobile_companion.py").is_file():
            print("Project sources already restored.")
            return
        raise SystemExit("Source payload is missing and project sources are not present.")

    encoded = "".join(part.read_text(encoding="ascii").strip() for part in parts)
    compressed = base64.b64decode(encoded, validate=True)
    with tarfile.open(fileobj=io.BytesIO(compressed), mode="r:xz") as archive:
        members = archive.getmembers()
        for member in members:
            target = (ROOT / member.name).resolve()
            if target != ROOT and ROOT not in target.parents:
                raise SystemExit(f"Unsafe archive path rejected: {member.name}")
            if member.issym() or member.islnk() or member.isdev():
                raise SystemExit(f"Unsupported archive member rejected: {member.name}")
        archive.extractall(ROOT, members=members)

    for part in parts:
        part.unlink()
    try:
        PAYLOAD_DIR.rmdir()
    except OSError:
        pass
    print(f"Restored {len(members)} project files from the compressed bootstrap payload.")


if __name__ == "__main__":
    main()
