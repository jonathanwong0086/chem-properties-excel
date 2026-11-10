import tempfile
import unittest
from pathlib import Path

from tools.extract_release_notes import changelog_section, extract

CHANGELOG = """# Changelog

## [3.2.0] - 2026-11-09

### Changed
- new

## [3.1.0] - 2026-10-09

### Added
- ait column

## [3.0.0] - 2026-09-14
- old
"""


class ExtractReleaseNotesTest(unittest.TestCase):
    def test_middle_section_stops_at_next_heading(self):
        self.assertEqual(changelog_section(CHANGELOG, "3.1.0"), "### Added\n- ait column")

    def test_last_section(self):
        self.assertEqual(changelog_section(CHANGELOG, "3.0.0"), "- old")

    def test_prefix_version_does_not_match(self):
        self.assertIsNone(changelog_section(CHANGELOG, "3.1"))

    def test_prefers_matching_release_notes(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "CHANGELOG.md").write_text(CHANGELOG, encoding="utf-8")
            (root / "RELEASE_NOTES.md").write_text("# tool v3.2.0\n\nbody\n", encoding="utf-8")
            self.assertEqual(extract("v3.2.0", root), "# tool v3.2.0\n\nbody")
            self.assertEqual(extract("v3.1.0", root), "### Added\n- ait column")

    def test_missing_version_fails(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "CHANGELOG.md").write_text(CHANGELOG, encoding="utf-8")
            with self.assertRaises(SystemExit):
                extract("v9.9.9", root)


if __name__ == "__main__":
    unittest.main()
