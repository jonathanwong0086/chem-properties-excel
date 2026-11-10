# SPDX-License-Identifier: LicenseRef-chem-properties-excel-1.0
# Copyright (C) 2026 Jonathan Wong (jonathanwong0086). All rights reserved.
"""Extract release notes for a version tag.

Prefers RELEASE_NOTES.md when its first heading names the version;
otherwise falls back to the matching section of CHANGELOG.md.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def changelog_section(text: str, version: str) -> str | None:
    pattern = re.compile(
        rf"^## \[{re.escape(version)}\][^\n]*\n(.*?)(?=^## \[|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(text)
    return match.group(1).strip() if match else None


def release_notes_file(text: str, version: str) -> str | None:
    first = text.lstrip().splitlines()[0] if text.strip() else ""
    if re.search(rf"\bv?{re.escape(version)}\b", first):
        return text.strip()
    return None


def extract(version: str, root: Path = ROOT) -> str:
    version = version.lstrip("v")
    notes = root / "RELEASE_NOTES.md"
    if notes.exists():
        found = release_notes_file(notes.read_text(encoding="utf-8"), version)
        if found:
            return found
    changelog = root / "CHANGELOG.md"
    found = changelog_section(changelog.read_text(encoding="utf-8"), version)
    if not found:
        raise SystemExit(f"No release notes found for version {version}")
    return found


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: extract_release_notes.py <tag>")
    sys.stdout.reconfigure(encoding="utf-8")
    print(extract(sys.argv[1]))


if __name__ == "__main__":
    main()
