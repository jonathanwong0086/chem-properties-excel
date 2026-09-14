import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from tools.build_sds_reference import build, find_entries_path


def make_entry(entry_id, name, cas):
    return {
        "entry_id": entry_id,
        "name_zh": name,
        "aliases_zh": [name + "别名"],
        "name_en": None,
        "aliases_en": [],
        "cas_no": [cas],
        "formula_raw": None,
        "source_page_start": 1,
        "source_page_end": 2,
        "identity_verification": {"status": "verified"},
        "raw_text": "## 理化特性\n液体\n## 毒理学信息\nLD50 1 mg/kg\n## 消防措施\n用雾状水灭火",
    }


class BuildSdsReferenceTest(unittest.TestCase):
    def test_build_supports_rootless_archive_and_valid_indexes(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            archive = tmp_path / "source.zip"
            entries = [
                make_entry("a", "甲", "1-11-1"),
                make_entry("b", "乙", "2-22-2"),
            ]
            with zipfile.ZipFile(archive, "w") as zf:
                zf.writestr(
                    "entries.jsonl",
                    "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in entries),
                )

            output = tmp_path / "out"
            build(str(archive), str(output))

            rows = [
                json.loads(line)
                for line in (output / "sds-handbook-reference.jsonl").read_text(
                    encoding="utf-8"
                ).splitlines()
            ]
            index = json.loads(
                (output / "sds-handbook-index.json").read_text(encoding="utf-8")
            )
            self.assertEqual([row["entry_id"] for row in rows], ["a", "b"])
            self.assertEqual(index["index"]["cas_no"]["1-11-1"], [0])
            self.assertEqual(index["index"]["name_zh"]["乙"], [1])

    def test_multiple_entries_files_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "source.zip"
            with zipfile.ZipFile(archive, "w") as zf:
                zf.writestr("a/entries.jsonl", "")
                zf.writestr("b/entries.jsonl", "")
            with zipfile.ZipFile(archive) as zf:
                with self.assertRaisesRegex(ValueError, "多个 entries.jsonl"):
                    find_entries_path(zf)


if __name__ == "__main__":
    unittest.main()
