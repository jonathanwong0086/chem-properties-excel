# -*- coding: utf-8 -*-
"""
从 MinerU RAG 提取产物（entries.jsonl）构建精简本地参考文件：
    sds-handbook-reference.jsonl  — 每行一个化学品条目（理化特性+毒理学信息+消防措施原文）
    sds-handbook-index.json       — CAS号/中英文名/别名 → jsonl行号 的查找索引

用法:
    python tools/build_sds_reference.py <rag-output-zip路径> [输出目录]

仅抽取"理化特性"、"毒理学信息"与"消防措施"三节原文（原样保留，不做结构化解析），
丢弃 chunks/tables/images/assets 等本 skill 不需要的内容，将 ~57MB 的
entries.jsonl 精简为约1.5MB的参考文件。
"""
import sys
import os
import json
import re
import zipfile

IMG_PATTERN = re.compile(r"\[image:[^\]]*\]\n?")
HEADER_SPLIT = re.compile(r"(^##\s.+$)", re.MULTILINE)

SECTIONS_TO_KEEP = ["理化特性", "毒理学信息", "消防措施"]


def extract_section(raw_text, section_title):
    parts = HEADER_SPLIT.split(raw_text)
    for i in range(1, len(parts), 2):
        header = parts[i].lstrip("#").strip()
        if header == section_title:
            body = parts[i + 1] if i + 1 < len(parts) else ""
            return IMG_PATTERN.sub("", body).strip()
    return None


def find_root(zf):
    names = zf.namelist()
    if not names:
        raise ValueError("zip 为空")
    return names[0].split("/")[0]


def add_to_index(index, key, row_no):
    if not key:
        return
    key = str(key).strip()
    if not key:
        return
    index.setdefault(key, []).append(row_no)


def build(zip_path, out_dir):
    zf = zipfile.ZipFile(zip_path)
    root = find_root(zf)

    jsonl_path = os.path.join(out_dir, "sds-handbook-reference.jsonl")
    index_path = os.path.join(out_dir, "sds-handbook-index.json")

    index = {
        "cas_no": {},
        "name_zh": {},
        "name_en": {},
        "aliases_zh": {},
        "aliases_en": {},
    }

    n_total = 0
    n_written = 0
    n_verified = 0
    with zf.open(root + "/entries.jsonl") as f, open(jsonl_path, "w", encoding="utf-8") as out:
        for row_no, line in enumerate(f):
            n_total += 1
            e = json.loads(line)
            sections = {}
            for title in SECTIONS_TO_KEEP:
                text = extract_section(e.get("raw_text", ""), title)
                if text:
                    sections[title] = text

            verified = e.get("identity_verification", {}).get("status") == "verified"
            if verified:
                n_verified += 1

            rec = {
                "entry_id": e["entry_id"],
                "name_zh": e.get("name_zh"),
                "aliases_zh": e.get("aliases_zh", []),
                "name_en": e.get("name_en"),
                "aliases_en": e.get("aliases_en", []),
                "cas_no": e.get("cas_no", []),
                "formula_raw": e.get("formula_raw"),
                "source_page": [e.get("source_page_start"), e.get("source_page_end")],
                "verified": verified,
                "physchem_text": sections.get("理化特性", ""),
                "toxicology_text": sections.get("毒理学信息", ""),
                "firefighting_text": sections.get("消防措施", ""),
            }
            out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            n_written += 1

            for cas in e.get("cas_no", []) or []:
                add_to_index(index["cas_no"], cas, row_no)
            add_to_index(index["name_zh"], e.get("name_zh"), row_no)
            add_to_index(index["name_en"], e.get("name_en"), row_no)
            for a in e.get("aliases_zh", []) or []:
                add_to_index(index["aliases_zh"], a, row_no)
            for a in e.get("aliases_en", []) or []:
                add_to_index(index["aliases_en"], a, row_no)

    index_doc = {
        "schema_version": "1.0",
        "source": "危险化学品安全技术全书·通用卷第三版SDS（MinerU RAG提取，理化特性+毒理学信息+消防措施三节原文）",
        "row_file": "sds-handbook-reference.jsonl",
        "lookup_order": ["cas_no", "name_zh", "aliases_zh", "name_en", "aliases_en"],
        "note": "index值为 sds-handbook-reference.jsonl 中的0-based行号（可重复出现，需逐行取用）。verified=false 的条目为规则+OCR自动识别，未经人工核实，命中后须在批注中注明可信度。",
        "index": index,
    }
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index_doc, f, ensure_ascii=False, indent=1)

    print(f"OK: {jsonl_path}")
    print(f"OK: {index_path}")
    print(f"  entries read: {n_total}, written: {n_written}, verified: {n_verified}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python build_sds_reference.py <zip路径> [输出目录]")
        sys.exit(1)
    zip_path = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "."
    build(zip_path, out_dir)
