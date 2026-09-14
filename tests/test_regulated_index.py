import json
import unittest
from pathlib import Path

from generate_excel import lookup_regulated_chemical
from tools.build_regulated_index import (
    SOURCE_CONFIG,
    build_index,
    parse_table,
    validate_index,
    validate_records,
)


ROOT = Path(__file__).resolve().parents[1]


class RegulatedIndexTest(unittest.TestCase):
    def test_reference_files_rebuild_the_committed_index(self):
        records = []
        for config in SOURCE_CONFIG:
            records.extend(parse_table(config["path"], config))
        validation = validate_records(records)
        rebuilt = build_index(records)
        validation["errors"].extend(validate_index(rebuilt))

        self.assertEqual(validation["errors"], [])
        self.assertEqual(rebuilt["statistics"]["total_records"], 140)
        self.assertEqual(rebuilt["statistics"]["precursor_records"], 45)
        self.assertEqual(rebuilt["statistics"]["explosive_precursor_records"], 95)
        committed = json.loads(
            (ROOT / "regulated-chemicals-index.json").read_text(encoding="utf-8")
        )
        self.assertEqual(rebuilt, committed)

    def test_real_index_known_matches(self):
        index = json.loads(
            (ROOT / "regulated-chemicals-index.json").read_text(encoding="utf-8")
        )
        acetone = lookup_regulated_chemical(index, "丙酮", "67-64-1")
        permanganate = lookup_regulated_chemical(index, "高锰酸钾", "7722-64-7")
        peroxide = lookup_regulated_chemical(index, "双氧水", "7722-84-1")
        ethanol = lookup_regulated_chemical(index, "乙醇", "64-17-5")

        self.assertEqual(acetone["is_precursor"], "是（第三类）")
        self.assertEqual(permanganate["is_precursor"], "是（第三类）")
        self.assertEqual(permanganate["is_explosive_precursor"], "是")
        self.assertEqual(peroxide["is_explosive_precursor"], "需核实浓度/形态")
        self.assertEqual(ethanol["is_precursor"], "否")
        self.assertEqual(ethanol["is_explosive_precursor"], "否")


if __name__ == "__main__":
    unittest.main()
