# SPDX-License-Identifier: LicenseRef-chem-properties-excel-1.0
# Copyright (C) 2026 Jonathan Wong (jonathanwong0086). All rights reserved.
"""Public attribution shared by data files, builders and generated workbooks."""

SKILL = "chem-properties-excel"
AUTHOR = "Jonathan Wong (jonathanwong0086)"
CONTACT = "wjc0086@163.com"
REPO_URL = "https://github.com/jonathanwong0086/chem-properties-excel"
LICENSE_ID = "LicenseRef-chem-properties-excel-1.0"
LICENSE_NAME = "chem-properties-excel 使用许可协议 1.0"
NOTICE = (
    f"本文件属于 {SKILL}（{REPO_URL}），由 {AUTHOR} 整理、校验和结构化。"
    f"按 {LICENSE_NAME} 授权：免费使用，未经作者书面同意不得再分发或修改。"
    "原始出版物或标准的权利归原权利人所有。"
)

MD_MARKER = "<!-- chem-properties-excel attribution -->"


ROW_TAG = f"{SKILL} · {LICENSE_ID} · {REPO_URL}"


def json_meta() -> dict:
    """Value for the `_meta` key of JSON reference files. Lookups never read it."""
    return {
        "skill": SKILL,
        "author": AUTHOR,
        "contact": CONTACT,
        "repository": REPO_URL,
        "license": LICENSE_ID,
        "notice": NOTICE,
    }


def md_block() -> str:
    """Attribution block placed right after the first heading of reference .md files."""
    return (
        f"{MD_MARKER}\n"
        f"> **版权与许可**：{NOTICE}\n"
        f"> 来源仓库：{REPO_URL} ｜ 许可标识：`{LICENSE_ID}` ｜ 联系：{CONTACT}\n"
    )


def workbook_description(version: str) -> str:
    return f"由 {SKILL} v{version} 生成。{REPO_URL}（{LICENSE_ID}）"
