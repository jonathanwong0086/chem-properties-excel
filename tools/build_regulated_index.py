#!/usr/bin/env python3
"""Build and validate the unified precursor/explosive chemical index.

The two Markdown reference files are the maintained source of truth. This
script parses their normalized tables, validates legal-item counts and record
integrity, then writes regulated-chemicals-index.json deterministically.
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "regulated-chemicals-index.json"

SOURCE_CONFIG = (
    {
        "path": ROOT / "precursor-chemicals-reference.md",
        "list_type": "易制毒",
        "expected_legal_items": 38,
        "expected_records": 45,
        "expected_categories": 3,
        "expected_conditional_records": 0,
        "columns": (
            "record_id",
            "category",
            "item_no",
            "name",
            "aliases",
            "cas_no",
            "scope_condition",
            "salt_rule",
            "drug_precursor",
            "source_locator",
        ),
    },
    {
        "path": ROOT / "explosive-precursor-chemicals-reference.md",
        "list_type": "易制爆",
        "expected_legal_items": 74,
        "expected_records": 95,
        "expected_categories": 9,
        "expected_conditional_records": 27,
        "columns": (
            "record_id",
            "category",
            "item_no",
            "name",
            "aliases",
            "cas_no",
            "scope_condition",
            "hazard_classification",
            "condition_required",
            "source_row",
        ),
    },
)

CAS_RE = re.compile(r"^\d{2,7}-\d{2}-\d$")
DATA_START = "<!-- DATA-START -->"
DATA_END = "<!-- DATA-END -->"


def normalize_name(value: str) -> str:
    """Return a stable lookup key for Chinese/English chemical names."""
    text = unicodedata.normalize("NFKC", value).strip().lower()
    text = text.replace("α", "alpha").replace("β", "beta").replace("γ", "gamma")
    text = text.replace("－", "-").replace("—", "-").replace("–", "-")
    return re.sub(r"[\s,，;；:：·.。'\"`´^_()（）\[\]【】{}<>《》/\\-]+", "", text)


def split_values(value: str) -> list[str]:
    if not value.strip():
        return []
    return [part.strip() for part in value.split("；") if part.strip()]


def valid_cas_checksum(value: str) -> bool:
    digits, check = value.replace("-", "")[:-1], int(value[-1])
    total = sum(int(digit) * weight for weight, digit in enumerate(reversed(digits), 1))
    return total % 10 == check


def parse_table(path: Path, config: dict[str, Any]) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    try:
        block = text.split(DATA_START, 1)[1].split(DATA_END, 1)[0]
    except IndexError as exc:
        raise ValueError(f"{path.name}: missing DATA markers") from exc

    rows = [line.strip() for line in block.splitlines() if line.strip().startswith("|")]
    if len(rows) < 3:
        raise ValueError(f"{path.name}: data table is empty")

    records: list[dict[str, Any]] = []
    for line_no, line in enumerate(rows[2:], start=1):
        cells = [cell.strip().replace("\\|", "|") for cell in line.strip("|").split("|")]
        if len(cells) != len(config["columns"]):
            raise ValueError(
                f"{path.name}: data row {line_no} has {len(cells)} cells; "
                f"expected {len(config['columns'])}"
            )
        record = dict(zip(config["columns"], cells))
        record["list_type"] = config["list_type"]
        record["aliases"] = split_values(record.get("aliases", ""))
        record["cas_no"] = split_values(record.get("cas_no", ""))
        if config["list_type"] == "易制毒":
            record["salt_rule"] = record["salt_rule"] == "是"
            record["drug_precursor"] = record["drug_precursor"] == "是"
            record["requires_condition_check"] = False
        else:
            record["requires_condition_check"] = record.pop("condition_required") == "是"
        records.append(record)
    return records


def validate_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    ids = [record["record_id"] for record in records]
    duplicate_ids = sorted(key for key, count in Counter(ids).items() if count > 1)
    if duplicate_ids:
        errors.append(f"duplicate record_id: {duplicate_ids}")

    identities = [
        (record["list_type"], normalize_name(record["name"]), record["scope_condition"])
        for record in records
    ]
    duplicate_identities = sorted(key for key, count in Counter(identities).items() if count > 1)
    if duplicate_identities:
        errors.append(f"duplicate normalized records: {duplicate_identities}")

    for record in records:
        if not record["record_id"] or not record["item_no"] or not record["name"]:
            errors.append(f"incomplete required fields: {record!r}")
        for cas in record["cas_no"]:
            if not CAS_RE.fullmatch(cas):
                errors.append(f"invalid CAS {cas!r} in {record['record_id']}")
            elif not valid_cas_checksum(cas):
                errors.append(f"invalid CAS checksum {cas!r} in {record['record_id']}")

    summary: dict[str, Any] = {"errors": errors, "warnings": warnings, "lists": {}}
    for config in SOURCE_CONFIG:
        subset = [r for r in records if r["list_type"] == config["list_type"]]
        legal_items = {(r["category"], r["item_no"]) for r in subset}
        categories = {r["category"] for r in subset}
        conditional_records = sum(bool(r["requires_condition_check"]) for r in subset)
        if len(subset) != config["expected_records"]:
            errors.append(
                f"{config['list_type']}: {len(subset)} records, "
                f"expected {config['expected_records']}"
            )
        if len(legal_items) != config["expected_legal_items"]:
            errors.append(
                f"{config['list_type']}: {len(legal_items)} legal items, "
                f"expected {config['expected_legal_items']}"
            )
        if len(categories) != config["expected_categories"]:
            errors.append(
                f"{config['list_type']}: {len(categories)} categories, "
                f"expected {config['expected_categories']}"
            )
        if conditional_records != config["expected_conditional_records"]:
            errors.append(
                f"{config['list_type']}: {conditional_records} conditional records, "
                f"expected {config['expected_conditional_records']}"
            )
        if config["list_type"] == "易制爆":
            expected_source_rows = set(range(3, 8))
            for start, end in (
                (9, 19), (21, 25), (27, 30), (32, 35), (37, 52),
                (54, 74), (76, 87), (89, 101),
            ):
                expected_source_rows.update(range(start, end + 1))
            try:
                actual_source_rows = {int(r["source_row"]) for r in subset}
            except ValueError:
                errors.append("易制爆: source_row must be an integer")
            else:
                if actual_source_rows != expected_source_rows:
                    errors.append(
                        "易制爆: source row coverage mismatch; "
                        f"missing={sorted(expected_source_rows - actual_source_rows)}, "
                        f"extra={sorted(actual_source_rows - expected_source_rows)}"
                    )
        summary["lists"][config["list_type"]] = {
            "records": len(subset),
            "legal_items": len(legal_items),
            "categories": len(categories),
            "records_with_cas": sum(bool(r["cas_no"]) for r in subset),
            "conditional_records": conditional_records,
        }

    return summary


def build_index(records: list[dict[str, Any]]) -> dict[str, Any]:
    cas_index: dict[str, set[str]] = defaultdict(set)
    name_index: dict[str, set[str]] = defaultdict(set)
    alias_index: dict[str, set[str]] = defaultdict(set)

    for record in records:
        record_id = record["record_id"]
        for cas in record["cas_no"]:
            cas_index[cas].add(record_id)
        name_key = normalize_name(record["name"])
        if name_key:
            name_index[name_key].add(record_id)
        for alias in record["aliases"]:
            alias_key = normalize_name(alias)
            if alias_key:
                alias_index[alias_key].add(record_id)

    def sorted_index(values: dict[str, set[str]]) -> dict[str, list[str]]:
        return {key: sorted(ids) for key, ids in sorted(values.items())}

    list_counts = {
        list_type: sum(record["list_type"] == list_type for record in records)
        for list_type in ("易制毒", "易制爆")
    }
    return {
        "schema_version": "1.0",
        "sources": [
            {
                "list_type": "易制毒",
                "reference_file": "precursor-chemicals-reference.md",
                "source_document": "易制毒化学品管理条例 国办函〔2021〕58号-更新至2021年5月.docx",
                "scope": "附件所载截至2021年5月目录",
            },
            {
                "list_type": "易制爆",
                "reference_file": "explosive-precursor-chemicals-reference.md",
                "source_document": "易制爆危险化学品名录（2017年版）.doc",
                "scope": "2017年版目录",
            },
        ],
        "lookup_policy": {
            "order": ["cas_no", "name", "alias"],
            "name_normalization": "Unicode NFKC、转小写、统一希腊字母并移除空白和常见标点",
            "multiple_matches": "返回全部记录，不静默择一",
            "conditional_explosive_match": "命中含浓度、含水量、涂层、粒径、物态或配方条件的记录时，条件未知应返回需核实浓度/形态",
            "precursor_salt_rule": "第一类、第二类记录的可能盐类同样受管制；盐类名称命中需关联母体记录并标注盐类规则",
        },
        "statistics": {
            "total_records": len(records),
            "precursor_records": list_counts["易制毒"],
            "explosive_precursor_records": list_counts["易制爆"],
            "cas_keys": len(cas_index),
            "name_keys": len(name_index),
            "alias_keys": len(alias_index),
        },
        "records": sorted(records, key=lambda item: item["record_id"]),
        "search_index": {
            "by_cas": sorted_index(cas_index),
            "by_name": sorted_index(name_index),
            "by_alias": sorted_index(alias_index),
        },
    }


def validate_index(index: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    record_ids = {record["record_id"] for record in index["records"]}
    referenced: set[str] = set()
    for index_name, mapping in index["search_index"].items():
        for key, ids in mapping.items():
            if not key:
                errors.append(f"empty key in index.{index_name}")
            for record_id in ids:
                referenced.add(record_id)
                if record_id not in record_ids:
                    errors.append(f"dangling index pointer: {index_name}.{key} -> {record_id}")
    missing = sorted(record_ids - referenced)
    if missing:
        errors.append(f"records missing from all indexes: {missing}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="validate without writing output")
    args = parser.parse_args()

    records: list[dict[str, Any]] = []
    for config in SOURCE_CONFIG:
        records.extend(parse_table(config["path"], config))

    validation = validate_records(records)
    index = build_index(records)
    validation["errors"].extend(validate_index(index))

    if validation["errors"]:
        for error in validation["errors"]:
            print(f"ERROR: {error}")
        return 1

    rendered = json.dumps(index, ensure_ascii=False, indent=2) + "\n"
    if args.check:
        if not OUTPUT_PATH.exists():
            print(f"ERROR: missing {OUTPUT_PATH.name}")
            return 1
        if OUTPUT_PATH.read_text(encoding="utf-8") != rendered:
            print(f"ERROR: {OUTPUT_PATH.name} is stale; rebuild it")
            return 1
    else:
        OUTPUT_PATH.write_text(rendered, encoding="utf-8", newline="\n")

    print(json.dumps(validation["lists"], ensure_ascii=False, sort_keys=True))
    print(
        json.dumps(
            {
                "total_records": len(records),
                "cas_keys": len(index["search_index"]["by_cas"]),
                "name_keys": len(index["search_index"]["by_name"]),
                "alias_keys": len(index["search_index"]["by_alias"]),
                "duplicate_record_ids": 0,
                "dangling_index_pointers": 0,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
