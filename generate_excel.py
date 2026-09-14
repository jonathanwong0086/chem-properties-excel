# -*- coding: utf-8 -*-
"""Generate the chemical-properties workbook defined by this skill."""

from __future__ import annotations

import json
import os
import re
import tempfile
import unicodedata
import zipfile
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

import openpyxl
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter


# Fill this list when running the module directly. Each property may have a
# matching entry in ``sources``; for CAS use the key ``cas_no``.
chemicals: list[dict[str, Any]] = []

PROJECT_NAME = "示例项目"
OUTPUT_DIR = os.path.expanduser("~/Desktop")

FIELDS = [
    ("序号", "id"), ("化学品名称", "name"), ("CAS号", "cas_no"),
    ("熔点(°C)", "mp"), ("沸点(°C)", "bp"), ("闪点(°C)", "fp"),
    ("密度", "density"), ("常温物态", "state"), ("火灾危险性类别", "fire"),
    ("水溶性", "sol"), ("密度>水？", "den_water"), ("禁用水灭火？", "water_ext"),
    ("爆炸极限(LEL~UEL)", "explosion"), ("蒸汽>空气？", "vapor"),
    ("职业接触限值(mg/m³)", "oel"), ("危化品类别", "danger_cat"),
    ("毒理数据(LD50/LC50)", "toxicology"), ("是否被列入有毒气体检测目录", "toxic_gas"),
    ("毒性(GB/T42594)", "gbt_toxicity"), ("燃烧爆炸特性(GB/T42594)", "gbt_combustion"),
    ("介质与金属材料相容性提示(GB/T42594)", "gbt_compatibility"),
    ("反应和稳定性提示(GB/T42594)", "gbt_reactivity"),
    ("危害提示(GB/T42594)", "gbt_hazard"),
    ("GHS健康和环境危害类别(GB/T42594)", "gbt_ghs"),
    ("是否易制毒", "is_precursor"), ("是否易制爆", "is_explosive_precursor"),
]

CHEMICAL_LIST_FIELDS = [
    ("序号", "id"), ("化学品名称", "name"), ("分类", "category"),
    ("涉及工段", "sections"), ("出现设备数(去重)", "device_count"),
    ("原表介质写法(变体归并)", "variants"), ("备注", "remarks"),
    ("是否被列入有毒气体检测目录", "toxic_gas"),
    ("是否易制毒", "is_precursor"), ("是否易制爆", "is_explosive_precursor"),
]

EQUIPMENT_FIELDS = [
    ("序号", "id"), ("化学品名称", "name"), ("分类", "category"),
    ("设备位号", "equipment_tag"), ("设备名称", "equipment_name"), ("工段", "section"),
    ("设备类型", "equipment_type"), ("火灾危险性类别", "fire"),
    ("是否被列入有毒气体检测目录", "toxic_gas"),
    ("是否易制毒", "is_precursor"), ("是否易制爆", "is_explosive_precursor"),
]

SRC_DATA = [
    ("国际数据库", "PubChem (NCBI)", "CAS号、密度、水溶性", "https://pubchem.ncbi.nlm.nih.gov/"),
    ("国际数据库", "NIST Chemistry WebBook", "熔点、沸点、蒸气相对密度", "https://webbook.nist.gov/"),
    ("化学品供应商", "Sigma-Aldrich / MilliporeSigma", "SDS、闪点、密度", "https://www.sigmaaldrich.com/"),
    ("化学品数据库", "ChemicalBook", "CAS号、沸点、闪点、物态", "https://www.chemicalbook.com/"),
    ("化学品数据库", "ChemSpider (RSC)", "常温物态、结构验证", "https://www.chemspider.com/"),
    ("应急响应数据库", "CAMEO Chemicals (NOAA)", "遇水反应性、灭火禁忌", "https://cameochemicals.noaa.gov/"),
    ("职业安全数据库", "NIOSH Pocket Guide (CDC)", "爆炸极限、蒸气密度", "https://www.cdc.gov/niosh/npg/"),
    ("农药评价", "FAO/WHO JMPR、BASF SDS", "农药原药物化及毒性", "https://www.fao.org/"),
    ("中国国家标准", "GB 50016-2014《建筑设计防火规范》", "火灾危险性类别", "https://openstd.samr.gov.cn/"),
    ("中国国家标准", "GBZ 2.1-2007 / GBZ 2.1-2019", "职业接触限值（本地2007版；2019版须另行核实）", "https://openstd.samr.gov.cn/"),
    ("中国国家标准", "GB 15603-1995《常用危险化学品贮存通则》", "储存禁忌", "https://openstd.samr.gov.cn/"),
    ("中国国家标准", "GB/T 42594-2023《承压设备介质危害分类导则》", "介质危害六项", "https://openstd.samr.gov.cn/"),
    ("中国国家标准", "GB/T 50493-2019附录B", "有毒气体蒸气特性", "https://openstd.samr.gov.cn/"),
    ("中国行业标准", "HG/T 20660-2017附录A", "毒物危害分类I/II级", "https://openstd.samr.gov.cn/"),
    ("中国部门规章", "《高毒物品目录》(卫法监发[2003]142号)", "高毒物质、职业接触限值", "https://www.gov.cn/"),
    ("中国部门规章", "《危险化学品目录》(2015版)", "危化品类别、剧毒", "https://www.mem.gov.cn/"),
    ("中国管制目录", "《易制毒化学品管理条例》及增补目录", "是否易制毒、类别", "https://www.gov.cn/"),
    ("中国管制目录", "《易制爆危险化学品名录》(2017年版)", "是否易制爆、适用条件", "https://www.mps.gov.cn/"),
]

_INVALID_SHEET_CHARS = re.compile(r"[\\/*?:\[\]]")
_INVALID_FILE_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_CAS_NORMALIZER = re.compile(r"[^0-9]")
_NAME_NORMALIZER = re.compile(r"[\s·•・,，、()（）\[\]【】_-]+")
_GBT_KEYS = [field for _, field in FIELDS[18:24]]
_GBT_REFERENCE_MISS = "本地参考未命中，需核对GB/T 42594-2023原文"
_GBT_MISSING = {
    "", "-", "—", "未列入GB/T 42594-2023", "未列入GB/T42594-2023",
    _GBT_REFERENCE_MISS,
}


def _string(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple, set)):
        return "、".join(str(item) for item in value)
    return str(value)


def _normalise_cas(value: Any) -> str:
    digits = _CAS_NORMALIZER.sub("", _string(value))
    if len(digits) < 3:
        return ""
    return f"{digits[:-3]}-{digits[-3:-1]}-{digits[-1]}"


def _normalise_name(value: Any) -> str:
    text = unicodedata.normalize("NFKC", _string(value)).strip().lower()
    text = text.replace("α", "alpha").replace("β", "beta").replace("γ", "gamma")
    text = text.replace("－", "-").replace("—", "-").replace("–", "-")
    return re.sub(r"[\s,，;；:：·.。'\"`´^_()（）\[\]【】{}<>《》/\\-]+", "", text)


def load_regulated_index(path: str | os.PathLike[str] | None = None) -> dict[str, Any]:
    """Load the required unified precursor index."""
    index_path = Path(path) if path else Path(__file__).with_name("regulated-chemicals-index.json")
    if not index_path.exists():
        raise FileNotFoundError(f"缺少监管化学品索引: {index_path}")
    with index_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict) or not isinstance(data.get("records", data.get("entries")), list):
        raise ValueError(f"监管化学品索引结构无效: {index_path}")
    return data


def _index_entry_map(index: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    return {
        str(entry.get("record_id", entry.get("id"))): entry
        for entry in index.get("records", index.get("entries", []))
        if isinstance(entry, Mapping) and entry.get("record_id", entry.get("id")) is not None
    }


def _entry_ids(index: Mapping[str, Any], name: Any, cas_no: Any) -> list[str]:
    search = index.get("search_index", {})
    if not isinstance(search, Mapping):
        search = {}
    by_cas = search.get("by_cas", {})
    by_name = search.get("by_name", {})
    by_alias = search.get("by_alias", {})
    current_index = index.get("index", {})
    if isinstance(current_index, Mapping):
        by_cas = current_index.get("cas_no", by_cas)
        current_names = current_index.get("name", {})
        current_aliases = current_index.get("alias", {})
    else:
        current_names, current_aliases = {}, {}
    ids: list[str] = []
    cas, normal_name = _normalise_cas(cas_no), _normalise_name(name)
    for mapping, key in (
        (by_cas, cas), (by_name, normal_name), (by_alias, normal_name),
        (current_names, normal_name), (current_aliases, normal_name)
    ):
        if not key or not isinstance(mapping, Mapping):
            continue
        raw_ids = mapping.get(key, [])
        if isinstance(raw_ids, (str, int)):
            raw_ids = [raw_ids]
        for entry_id in raw_ids:
            if str(entry_id) not in ids:
                ids.append(str(entry_id))
    if ids:
        return ids
    for entry in index.get("records", index.get("entries", [])):
        if not isinstance(entry, Mapping):
            continue
        entry_cas = {
            _normalise_cas(item)
            for item in entry.get("cas_no", entry.get("cas_numbers", []))
        }
        entry_names = {_normalise_name(entry.get("name", entry.get("canonical_name")))}
        entry_names.update(_normalise_name(item) for item in entry.get("aliases", []))
        if (cas and cas in entry_cas) or (normal_name and normal_name in entry_names):
            ids.append(str(entry.get("record_id", entry.get("id"))))
    return ids


def _regulatory_source(label: str, records: Sequence[Mapping[str, Any]]) -> str:
    lines: list[str] = []
    for record in records:
        source = _string(record.get("source") or record.get("source_locator") or record.get("source_row"))
        item_no = _string(record.get("item_no"))
        scope = _string(record.get("scope_condition") or record.get("scope") or record.get("condition"))
        detail = "，".join(part for part in (f"条目{item_no}" if item_no else "", scope) if part)
        line = label if not source or source in label else f"{label}，{source}"
        if detail:
            line = f"{line}（{detail}）"
        if line not in lines:
            lines.append(line)
    return "\n".join(lines)


def lookup_regulated_chemical(index: Mapping[str, Any] | None, name: Any, cas_no: Any) -> dict[str, Any]:
    """Return display values and sources for both regulatory columns."""
    result = {"is_precursor": "否", "is_explosive_precursor": "否", "sources": {}, "matched_entry_ids": []}
    if not index:
        result["is_precursor"] = "未核实（缺少目录索引）"
        result["is_explosive_precursor"] = "未核实（缺少目录索引）"
        result["sources"] = {
            "is_precursor": "缺少 regulated-chemicals-index.json，未执行易制毒目录匹配",
            "is_explosive_precursor": "缺少 regulated-chemicals-index.json，未执行易制爆目录匹配",
        }
        return result
    entry_map = _index_entry_map(index)
    ids = _entry_ids(index, name, cas_no)
    entries = [entry_map[item] for item in ids if item in entry_map]
    result["matched_entry_ids"] = ids
    precursor_records = [entry for entry in entries if entry.get("list_type") == "易制毒"]
    precursor_records.extend(
        entry["precursor"] for entry in entries
        if isinstance(entry.get("precursor"), Mapping) and entry["precursor"].get("listed") is True
    )
    if precursor_records:
        categories: list[str] = []
        for record in precursor_records:
            category = _string(record.get("category"))
            if category and category not in categories:
                categories.append(category)
        result["is_precursor"] = f"是（{'、'.join(categories)}）" if categories else "是"
        result["sources"]["is_precursor"] = _regulatory_source(
            "《易制毒化学品管理条例》及附表", precursor_records
        )
    else:
        result["sources"]["is_precursor"] = "易制毒化学品统一索引：按CAS、名称及别名未命中"
    explosive_records = [entry for entry in entries if entry.get("list_type") == "易制爆"]
    explosive_records.extend(
        entry["explosive_precursor"] for entry in entries
        if isinstance(entry.get("explosive_precursor"), Mapping)
        and entry["explosive_precursor"].get("listed") is True
    )
    if explosive_records:
        conditional = all(
            record.get("requires_condition_check") is True
            or bool(_string(record.get("condition")))
            for record in explosive_records
        )
        result["is_explosive_precursor"] = "需核实浓度/形态" if conditional else "是"
        result["sources"]["is_explosive_precursor"] = _regulatory_source(
            "《易制爆危险化学品名录》(2017年版)", explosive_records
        )
    else:
        result["sources"]["is_explosive_precursor"] = "易制爆危险化学品统一索引：按CAS、名称及别名未命中"
    if ids:
        cas = _normalise_cas(cas_no)
        normal_name = _normalise_name(name)
        root_index = index.get("index", index.get("search_index", {}))
        if isinstance(root_index, Mapping):
            cas_map = root_index.get("cas_no", root_index.get("by_cas", {}))
            name_map = root_index.get("name", root_index.get("by_name", {}))
            alias_map = root_index.get("alias", root_index.get("by_alias", {}))

            def match_types(record_ids: Sequence[str]) -> list[str]:
                types: list[str] = []
                if cas and any(item in cas_map.get(cas, []) for item in record_ids):
                    types.append("CAS")
                if normal_name and any(item in name_map.get(normal_name, []) for item in record_ids):
                    types.append("名称")
                if normal_name and any(item in alias_map.get(normal_name, []) for item in record_ids):
                    types.append("别名")
                return types

            precursor_ids = [
                item for item in ids
                if item in entry_map and entry_map[item].get("list_type") == "易制毒"
            ]
            explosive_ids = [
                item for item in ids
                if item in entry_map and entry_map[item].get("list_type") == "易制爆"
            ]
            for key, record_ids in (
                ("is_precursor", precursor_ids),
                ("is_explosive_precursor", explosive_ids),
            ):
                types = match_types(record_ids)
                if types and key in result["sources"]:
                    result["sources"][key] += f"\n匹配依据: {'、'.join(types)}"
    return result


def _enrich_regulatory_fields(record: Mapping[str, Any], index: Mapping[str, Any] | None) -> dict[str, Any]:
    enriched = dict(record)
    sources = dict(record.get("sources", {})) if isinstance(record.get("sources"), Mapping) else {}
    match = lookup_regulated_chemical(index, record.get("name"), record.get("cas_no"))
    for key in ("is_precursor", "is_explosive_precursor"):
        if not _string(enriched.get(key)).strip():
            enriched[key] = match[key]
            if match["sources"].get(key):
                sources[key] = match["sources"][key]
    enriched["sources"] = sources
    return enriched


def _safe_sheet_title(wb: openpyxl.Workbook, requested: str) -> str:
    base = _INVALID_SHEET_CHARS.sub("_", requested).strip(" '") or "Sheet"
    base = base[:31]
    candidate, suffix = base, 2
    while candidate in wb.sheetnames:
        tail = f"_{suffix}"
        candidate = f"{base[:31 - len(tail)]}{tail}"
        suffix += 1
    return candidate


def _safe_file_stem(project_name: Any) -> str:
    stem = _INVALID_FILE_CHARS.sub("_", _string(project_name)).strip(" .") or "化学品"
    if stem.upper() in {"CON", "PRN", "AUX", "NUL", "COM1", "LPT1"}:
        stem = f"_{stem}"
    return stem


def _next_available_path(output_dir: Path, filename: str) -> Path:
    target = output_dir / filename
    if not target.exists():
        return target
    stem, suffix, version = target.stem, target.suffix, 2
    while True:
        candidate = output_dir / f"{stem}_v{version}{suffix}"
        if not candidate.exists():
            return candidate
        version += 1


def _styles() -> dict[str, Any]:
    thin = Side(style="thin", color="808080")
    return {
        "header_font": Font(name="微软雅黑", bold=True, size=10, color="FFFFFF"),
        "header_fill": PatternFill("solid", fgColor="2F5496"),
        "data_font": Font(name="微软雅黑", size=9),
        "title_font": Font(name="微软雅黑", bold=True, size=12, color="FFFFFF"),
        "center": Alignment(horizontal="center", vertical="center", wrap_text=True),
        "left": Alignment(horizontal="left", vertical="center", wrap_text=True),
        "border": Border(left=thin, right=thin, top=thin, bottom=thin),
        "fire": {"甲": PatternFill("solid", fgColor="FFCCCC"), "乙": PatternFill("solid", fgColor="FFE0B2"), "丙": PatternFill("solid", fgColor="FFF9C4"), "default": PatternFill("solid", fgColor="FFFFFF")},
        "zebra": [PatternFill("solid", fgColor=color) for color in ("FFFFFF", "F7FAFD", "EEF4FA", "E4EEF7")],
    }


def _write_title_and_headers(ws, title: str, fields: Sequence[tuple[str, str]], styles: Mapping[str, Any]) -> None:
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(fields))
    title_cell = ws.cell(1, 1, title)
    title_cell.font, title_cell.fill, title_cell.alignment = styles["title_font"], styles["header_fill"], styles["center"]
    ws.row_dimensions[1].height = 32
    for column, (heading, _) in enumerate(fields, 1):
        cell = ws.cell(2, column, heading)
        cell.font, cell.fill, cell.alignment, cell.border = styles["header_font"], styles["header_fill"], styles["center"], styles["border"]
    ws.row_dimensions[2].height = 42


def _add_comment(cell, source: Any) -> None:
    text = _string(source).strip()
    if not text:
        return
    if not text.startswith("数据来源:"):
        text = f"数据来源:\n{text}"
    cell.comment = Comment(text, "物性查询")
    cell.comment.width, cell.comment.height = 350, 90


def _gbt_is_missing(record: Mapping[str, Any]) -> bool:
    return {_string(record.get(key)).strip() for key in _GBT_KEYS}.issubset(_GBT_MISSING)


def _write_main_sheet(wb, records, project_name: str, index, styles) -> None:
    ws = wb.active
    ws.title = _safe_sheet_title(wb, f"{project_name}化学品物性数据")
    _write_title_and_headers(ws, f"{project_name}化学品物性数据", FIELDS, styles)
    left_fields = {"name", "sol", "water_ext", "explosion", "oel", "danger_cat", "toxicology", "toxic_gas", "gbt_toxicity", "gbt_combustion", "gbt_compatibility", "gbt_reactivity", "gbt_hazard", "gbt_ghs", "is_precursor", "is_explosive_precursor"}
    for offset, raw_record in enumerate(records):
        row = offset + 3
        record = _enrich_regulatory_fields(raw_record, index)
        fire_value = _string(record.get("fire"))
        fire_key = fire_value[0] if fire_value and fire_value[0] in "甲乙丙" else "default"
        fire_fill = styles["fire"][fire_key]
        sources = record.get("sources", {})
        for column, (_, key) in enumerate(FIELDS, 1):
            value: Any = offset + 1 if key == "id" else record.get(key, "")
            cell = ws.cell(row, column, value)
            cell.font, cell.border = styles["data_font"], styles["border"]
            cell.alignment = styles["left"] if key in left_fields else styles["center"]
            cell.fill = fire_fill if column in (2, 3, 9) else styles["zebra"][offset % 4]
            if isinstance(sources, Mapping):
                _add_comment(cell, sources.get(key))
        if _gbt_is_missing(record):
            ws.cell(row, 19, _GBT_REFERENCE_MISS)
            if isinstance(sources, Mapping):
                _add_comment(ws.cell(row, 19), sources.get("gbt_toxicity"))
            ws.merge_cells(start_row=row, start_column=19, end_row=row, end_column=24)
            ws.cell(row, 19).alignment = styles["center"]
        ws.row_dimensions[row].height = 30
    widths = [5, 24, 16, 14, 14, 15, 18, 14, 18, 20, 11, 18, 20, 14, 22, 26, 38, 22, 18, 26, 30, 34, 30, 38, 16, 18]
    for column, width in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(column)].width = width
    ws.freeze_panes = "C3"
    ws.auto_filter.ref = f"A2:{get_column_letter(len(FIELDS))}{len(records) + 2}"
    note_row = len(records) + 5
    notes = [
        "说明:",
        "1. 数据单元格批注记录该字段的真实来源；同一来源可支持多个字段。",
        "2. 火灾危险性类别仅依据闪点及气体爆炸下限作简化判断，正式设计须按完整标准复核。",
        "3. 本地职业接触限值参考库源自GBZ 2.1-2007；采用现行限值时须另行核对最新版标准。",
        "4. 危化品类别依据《危险化学品目录》(2015版)。",
        "5. 有毒气体检测目录依据《高毒物品目录》、GB/T 50493-2019附录B和HG/T 20660-2017附录A。",
        "6. GB/T 42594-2023未命中时仅合并第19至24列；易制毒、易制爆判断保持独立。",
        "7. 易制毒按《易制毒化学品管理条例》及增补目录判断；易制爆按《易制爆危险化学品名录》(2017年版)判断。",
        "8. 易制爆条目含浓度或形态条件且输入无法确认时标记为“需核实浓度/形态”。",
        "9. GB/T 42594毒性分级脚注a、b、c及其他原表注应以标准原文为准。",
    ]
    for index_, note in enumerate(notes):
        ws.cell(note_row + index_, 1, note).font = Font(name="微软雅黑", bold=index_ == 0, size=9)


def _write_simple_table(wb, title, sheet_name, fields, records, index, styles, merge_equipment_groups=False) -> None:
    ws = wb.create_sheet(_safe_sheet_title(wb, sheet_name))
    _write_title_and_headers(ws, title, fields, styles)
    enriched_records = [_enrich_regulatory_fields(record, index) for record in records]
    group_numbers: list[int] = []
    current_group = -1
    previous_name = None
    for record in enriched_records:
        name = _string(record.get("name"))
        if name != previous_name:
            current_group += 1
            previous_name = name
        group_numbers.append(current_group)
    equipment_group_fill = PatternFill("solid", fgColor="F2F7FC")
    for offset, record in enumerate(enriched_records):
        row, sources = offset + 3, record.get("sources", {})
        for column, (_, key) in enumerate(fields, 1):
            value: Any = offset + 1 if key == "id" else record.get(key, "")
            cell = ws.cell(row, column, _string(value))
            cell.font, cell.border = styles["data_font"], styles["border"]
            cell.alignment = styles["left"] if column not in (1, 5) else styles["center"]
            if merge_equipment_groups:
                cell.fill = equipment_group_fill if group_numbers[offset] % 2 else styles["zebra"][0]
            else:
                cell.fill = styles["zebra"][offset % 4]
            if isinstance(sources, Mapping):
                _add_comment(cell, sources.get(key))
        ws.row_dimensions[row].height = 30
    if merge_equipment_groups and enriched_records:
        start = 0
        while start < len(enriched_records):
            name, end = _string(enriched_records[start].get("name")), start
            while end + 1 < len(enriched_records) and _string(enriched_records[end + 1].get("name")) == name:
                end += 1
            if end > start:
                for column in range(1, 4):
                    ws.merge_cells(start_row=start + 3, start_column=column, end_row=end + 3, end_column=column)
                    ws.cell(start + 3, column).alignment = styles["center"]
            start = end + 1
    for column, (heading, _) in enumerate(fields, 1):
        ws.column_dimensions[get_column_letter(column)].width = min(max(len(heading) * 2 + 4, 12), 34)
    ws.column_dimensions["B"].width = 24
    ws.freeze_panes = "C3"
    ws.auto_filter.ref = f"A2:{get_column_letter(len(fields))}{len(records) + 2}"


def _write_sources_sheet(wb, project_name: str, source_data, styles) -> None:
    ws = wb.create_sheet(_safe_sheet_title(wb, "数据来源汇总"))
    fields = [("类型", "type"), ("机构 / 网站名称", "name"), ("本次提供数据字段", "fields"), ("网址", "url")]
    _write_title_and_headers(ws, f"{project_name}化学品物性数据 - 数据来源汇总", fields, styles)
    for offset, source in enumerate(source_data):
        if len(source) != 4:
            raise ValueError("数据来源项必须包含类型、名称、字段和网址")
        row = offset + 3
        for column, value in enumerate(source, 1):
            cell = ws.cell(row, column, value)
            cell.font, cell.border, cell.alignment = styles["data_font"], styles["border"], styles["left"]
        url_cell = ws.cell(row, 4)
        if _string(url_cell.value).startswith(("http://", "https://")):
            url_cell.hyperlink = _string(url_cell.value)
            url_cell.font = Font(name="微软雅黑", size=9, color="0563C1", underline="single")
        ws.row_dimensions[row].height = 24
    for column, width in enumerate((18, 48, 50, 48), 1):
        ws.column_dimensions[get_column_letter(column)].width = width
    ws.freeze_panes = "A3"


def build_excel(
    chemicals: Iterable[Mapping[str, Any]], project_name: str, output_dir: str | os.PathLike[str],
    src_data: Sequence[Sequence[Any]] | None = None, *,
    chemical_list: Iterable[Mapping[str, Any]] | None = None,
    equipment_mapping: Iterable[Mapping[str, Any]] | None = None,
    regulatory_index_path: str | os.PathLike[str] | None = None,
) -> str:
    """Build the workbook and return a new, never-overwritten output path."""
    records = list(chemicals)
    chemical_list_records = list(chemical_list) if chemical_list is not None else None
    equipment_records = list(equipment_mapping) if equipment_mapping is not None else None
    source_data = list(src_data if src_data is not None else SRC_DATA)
    if len(source_data) != 18:
        raise ValueError(f"数据来源汇总必须为18项，实际为{len(source_data)}项")
    index, styles = load_regulated_index(regulatory_index_path), _styles()
    workbook = openpyxl.Workbook()
    _write_main_sheet(workbook, records, project_name, index, styles)
    _write_sources_sheet(workbook, project_name, source_data, styles)
    if chemical_list_records is not None:
        _write_simple_table(workbook, f"{project_name}化学品清单", "化学品清单", CHEMICAL_LIST_FIELDS, chemical_list_records, index, styles)
    if equipment_records is not None:
        _write_simple_table(workbook, f"{project_name}介质-设备对照表", "介质-设备对照表", EQUIPMENT_FIELDS, equipment_records, index, styles, True)
    directory = Path(output_dir).expanduser().resolve()
    directory.mkdir(parents=True, exist_ok=True)
    target = _next_available_path(directory, f"{_safe_file_stem(project_name)}化学品物性数据.xlsx")
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(prefix="chem_", suffix=".xlsx", dir=directory, delete=False) as handle:
            temp_path = Path(handle.name)
        workbook.save(temp_path)
        with zipfile.ZipFile(temp_path, "r") as archive:
            bad_member = archive.testzip()
            if bad_member:
                raise ValueError(f"生成的工作簿压缩成员损坏: {bad_member}")
        temp_path.replace(target)
    finally:
        workbook.close()
        if temp_path and temp_path.exists():
            temp_path.unlink()
    print(f"OK: {target}")
    print(f"  {len(records)} chemicals x {len(FIELDS)} fields")
    print(f"  {len(source_data)} sources in summary sheet")
    return str(target)


if __name__ == "__main__":
    if not chemicals:
        print("请先在 chemicals 列表中填入化学品数据")
    else:
        build_excel(chemicals, PROJECT_NAME, OUTPUT_DIR, SRC_DATA)
