# SPDX-License-Identifier: LicenseRef-chem-properties-excel-1.0
# Copyright (C) 2026 Jonathan Wong (jonathanwong0086). All rights reserved.
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OEL_PATH = ROOT / "gbz2.1-oel-reference.md"

HEADER_CHEM = [
    "序号", "化学品名称", "英文名", "CAS号", "MAC(mg/m³)",
    "PC-TWA(mg/m³)", "PC-STEL(mg/m³)", "临界不良健康效应", "备注",
]
HEADER_DUST = [
    "序号", "粉尘名称", "英文名", "CAS号", "PC-TWA 总尘(mg/m³)",
    "PC-TWA 呼尘(mg/m³)", "临界不良健康效应", "备注",
]
LIMIT_RE = re.compile(r"^\d+(\.\d+)?( f/mL| pg TEQ/m³)?$")


def _cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _load_tables() -> dict[str, tuple[list[str], list[list[str]]]]:
    tables: dict[str, list[list[str]]] = {}
    section = None
    for line in OEL_PATH.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^## 表([12])", line)
        if match:
            section = match.group(1)
            tables[section] = []
            continue
        if section and line.startswith("|"):
            cells = _cells(line)
            if all(set(cell) <= {"-", ":"} for cell in cells):
                continue
            tables[section].append(cells)
    return {key: (rows[0], rows[1:]) for key, rows in tables.items()}


def _cas_ok(value: str) -> bool:
    match = re.fullmatch(r"(\d{2,7})-(\d{2})-(\d)", value)
    if not match:
        return False
    body = match.group(1) + match.group(2)
    checksum = sum(int(ch) * i for i, ch in enumerate(reversed(body), 1)) % 10
    return checksum == int(match.group(3))


class OelReferenceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tables = _load_tables()
        cls.h1, cls.chem = tables["1"]
        cls.h2, cls.dust = tables["2"]

    def _by_cas(self, cas: str) -> list[list[str]]:
        found = []
        for row in self.chem + self.dust:
            for part in row[3].split(";"):
                if re.sub(r"\(.*?\)", "", part).strip() == cas:
                    found.append(row)
                    break
        return found

    def test_headers(self):
        self.assertEqual(self.h1, HEADER_CHEM)
        self.assertEqual(self.h2, HEADER_DUST)

    def test_row_counts(self):
        self.assertEqual(len(self.chem), 374)
        self.assertEqual(len({row[0] for row in self.chem}), 358)
        self.assertEqual(len(self.dust), 58)
        self.assertEqual(len({row[0] for row in self.dust}), 49)

    def test_benzene_uses_2022_amendment(self):
        benzene = self._by_cas("71-43-2")
        self.assertEqual(len(benzene), 1)
        row = benzene[0]
        self.assertEqual(row[4], "—")
        self.assertEqual(row[5], "3")
        self.assertEqual(row[6], "6")

    def test_toluene_values(self):
        toluene = self._by_cas("108-88-3")
        self.assertEqual(len(toluene), 1)
        row = toluene[0]
        self.assertEqual(row[4], "—")
        self.assertEqual(row[5], "50")
        self.assertEqual(row[6], "100")
        self.assertEqual(row[8], "皮")

    def test_nickel_uses_twa(self):
        nickel = self._by_cas("7440-02-0")
        self.assertEqual(len(nickel), 1)
        row = nickel[0]
        self.assertEqual(row[4], "—")
        self.assertEqual(row[5], "1")
        self.assertEqual(row[6], "—")

    def test_formaldehyde_mac(self):
        formaldehyde = self._by_cas("50-00-0")
        self.assertEqual(len(formaldehyde), 1)
        self.assertEqual(formaldehyde[0][4], "0.5")
        self.assertEqual(formaldehyde[0][5], "—")

    def test_asbestos_rows_split(self):
        rows = [row for row in self.dust if row[0] == "34"]
        self.assertEqual(len(rows), 2)
        self.assertEqual((rows[0][4], rows[0][5]), ("0.8", "—"))
        self.assertEqual((rows[1][4], rows[1][5]), ("—", "0.8 f/mL"))

    def test_silica_rows_split(self):
        rows = [row for row in self.dust if row[0] == "40"]
        self.assertEqual(len(rows), 3)
        self.assertEqual([(row[4], row[5]) for row in rows],
                         [("1", "0.7"), ("0.7", "0.3"), ("0.5", "0.2")])

    def test_cas_numbers_pass_check_digit(self):
        for row in self.chem + self.dust:
            raw = row[3]
            if raw in ("—", "-"):
                continue
            for part in raw.split(";"):
                core = re.sub(r"\(.*?\)", "", part).strip()
                self.assertTrue(_cas_ok(core), f"{row[0]} {raw!r}")

    def test_limit_columns_hold_only_numbers(self):
        for header, rows in ((self.h1, self.chem), (self.h2, self.dust)):
            limit_idx = [i for i, name in enumerate(header) if "MAC" in name or "PC-TWA" in name]
            for row in rows:
                for idx in limit_idx:
                    value = row[idx]
                    self.assertTrue(value in ("—", "-") or LIMIT_RE.match(value),
                                    f"{row[0]} {header[idx]}={value!r}")


if __name__ == "__main__":
    unittest.main()
