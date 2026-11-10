# SPDX-License-Identifier: LicenseRef-chem-properties-excel-1.0
# Copyright (C) 2026 Jonathan Wong (jonathanwong0086). All rights reserved.
import json
import unittest
from pathlib import Path

from attribution import LICENSE_ID, MD_MARKER, REPO_URL, ROW_TAG, json_meta, md_block

ROOT = Path(__file__).resolve().parent.parent
MD_FILES = sorted(ROOT.glob("*-reference.md"))
JSON_FILES = ["regulated-chemicals-index.json", "gbt42594-2023-reference.json", "sds-handbook-index.json"]
CODE_FILES = sorted([*ROOT.glob("*.py"), *ROOT.glob("tools/*.py"), *ROOT.glob("tests/*.py")])


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


class AttributionTest(unittest.TestCase):
    def test_markdown_references_carry_block_after_title(self):
        self.assertEqual(len(MD_FILES), 5)
        for path in MD_FILES:
            with self.subTest(path.name):
                first, rest = _text(path).split("\n", 1)
                self.assertTrue(first.startswith("# "))
                self.assertTrue(rest.startswith("\n" + md_block()))
                self.assertEqual(_text(path).count(MD_MARKER), 1)

    def test_json_references_carry_meta(self):
        for name in JSON_FILES:
            with self.subTest(name):
                data = json.loads(_text(ROOT / name))
                self.assertEqual(next(iter(data)), "_meta")
                self.assertEqual(data["_meta"], json_meta())

    def test_every_handbook_row_is_tagged(self):
        rows = _text(ROOT / "sds-handbook-reference.jsonl").splitlines()
        self.assertEqual(len(rows), 1006)
        for number, line in enumerate(rows):
            self.assertEqual(json.loads(line).get("_license"), ROW_TAG, f"row {number}")

    def test_code_files_carry_spdx_header(self):
        for path in CODE_FILES:
            with self.subTest(str(path.relative_to(ROOT))):
                head = "\n".join(_text(path).splitlines()[:3])
                self.assertIn(f"SPDX-License-Identifier: {LICENSE_ID}", head)
                self.assertIn("jonathanwong0086", head)

    def test_meta_names_repository_and_license(self):
        meta = json_meta()
        self.assertEqual(meta["repository"], REPO_URL)
        self.assertEqual(meta["license"], LICENSE_ID)
        self.assertIn(REPO_URL, ROW_TAG)


if __name__ == "__main__":
    unittest.main()
