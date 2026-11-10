# SPDX-License-Identifier: LicenseRef-chem-properties-excel-1.0
# Copyright (C) 2026 Jonathan Wong (jonathanwong0086). All rights reserved.
"""License gate for chem-properties-excel.

- Install confirmation: before first use the user must confirm they hold a
  written license from 新华院. Only the yes answer is recorded locally; no
  credential is uploaded or stored.
- Integrity manifest: SHA-256 of every distributed file. A copy whose files
  differ from the manifest runs only when the GitHub CLI on this machine is
  logged in as the author account.
- Modifier check: modifying the skill requires `gh` logged in as the author.

Usage:
  python license_gate.py status
  python license_gate.py accept [--yes]
  python license_gate.py check-modifier
  python license_gate.py manifest        # author only: regenerate manifest
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

AUTHOR_LOGIN = "jonathanwong0086"
LICENSE_ID = "LicenseRef-chem-properties-excel-1.0"
SKILL_ROOT = Path(__file__).resolve().parent
MARKER_NAME = ".license-accepted"
MANIFEST_NAME = "integrity-manifest.json"
QUESTION = "是否已取得新华院的书面许可？"
YES_ANSWERS = {"是", "y", "yes"}
EXCLUDED_DIRS = {".git", ".github", ".claude", "__pycache__", ".venv", "venv", "ENV", ".idea", ".vscode"}
EXCLUDED_NAMES = {MARKER_NAME, MANIFEST_NAME, ".DS_Store", "Thumbs.db", "Desktop.ini"}
EXCLUDED_SUFFIXES = {".xlsx", ".pyc", ".pyo", ".swp", ".swo"}


class LicenseError(RuntimeError):
    """Raised when the license conditions are not met."""


def skill_version(root: Path = SKILL_ROOT) -> str:
    text = (root / "SKILL.md").read_text(encoding="utf-8")
    match = re.search(r'^\s*version:\s*"([^"]+)"', text, re.MULTILINE)
    return match.group(1) if match else "unknown"


# ---------- install confirmation ----------

def is_accepted(root: Path = SKILL_ROOT) -> bool:
    marker = root / MARKER_NAME
    if not marker.is_file():
        return False
    try:
        return json.loads(marker.read_text(encoding="utf-8")).get("answer") == "是"
    except (OSError, ValueError, AttributeError):
        return False


def record_acceptance(root: Path = SKILL_ROOT) -> Path:
    marker = root / MARKER_NAME
    payload = {
        "question": QUESTION,
        "answer": "是",
        "accepted_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "skill_version": skill_version(root),
    }
    marker.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return marker


# ---------- integrity manifest ----------

def distributed_files(root: Path = SKILL_ROOT) -> list[Path]:
    files = []
    for path in root.rglob("*"):
        rel = path.relative_to(root)
        if any(part in EXCLUDED_DIRS for part in rel.parts):
            continue
        if not path.is_file() or path.name in EXCLUDED_NAMES or path.suffix in EXCLUDED_SUFFIXES:
            continue
        if path.name.startswith("~$"):
            continue
        files.append(path)
    return sorted(files, key=lambda p: p.relative_to(root).as_posix())


def file_digest(path: Path) -> str:
    # Normalise CRLF so Windows checkouts (core.autocrlf) hash the same as Linux.
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def build_manifest(root: Path = SKILL_ROOT) -> dict:
    return {
        "skill": "chem-properties-excel",
        "version": skill_version(root),
        "author": AUTHOR_LOGIN,
        "license": LICENSE_ID,
        "files": {p.relative_to(root).as_posix(): file_digest(p) for p in distributed_files(root)},
    }


def integrity_problems(root: Path = SKILL_ROOT) -> list[str]:
    """Return modified or missing manifest entries. Extra local files are ignored."""
    manifest_path = root / MANIFEST_NAME
    if not manifest_path.is_file():
        return [f"缺少 {MANIFEST_NAME}"]
    try:
        expected = json.loads(manifest_path.read_text(encoding="utf-8"))["files"]
    except (OSError, ValueError, KeyError, TypeError):
        return [f"{MANIFEST_NAME} 无法解析"]
    problems = []
    for rel, digest in expected.items():
        path = root / rel
        if not path.is_file():
            problems.append(f"缺失: {rel}")
        elif file_digest(path) != digest:
            problems.append(f"已修改: {rel}")
    return problems


# ---------- modifier check ----------

def gh_login() -> str | None:
    """Login of the account the local GitHub CLI is authenticated as, verified online."""
    try:
        result = subprocess.run(
            ["gh", "api", "user", "--jq", ".login"],
            capture_output=True, text=True, timeout=30, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    login = result.stdout.strip()
    return login if result.returncode == 0 and login else None


def is_author() -> bool:
    return gh_login() == AUTHOR_LOGIN


# ---------- runtime enforcement ----------

def enforce(root: Path = SKILL_ROOT) -> None:
    if not is_accepted(root):
        raise LicenseError(
            "未完成安装确认。请先询问用户：“" + QUESTION + "”"
            "用户回答“是”后运行 `python license_gate.py accept --yes`；"
            "回答“否”则不得使用本技能。详见 LICENSE 第三条。"
        )
    problems = integrity_problems(root)
    if problems and not is_author():
        raise LicenseError(
            "本技能文件与发布版本不一致，且本机 GitHub CLI 未登录作者账号 "
            f"{AUTHOR_LOGIN}。根据 LICENSE 第四条，只有作者可以修改本技能，"
            "请从官方仓库重新安装。差异：" + "；".join(problems[:5])
        )


# ---------- CLI ----------

def _cmd_status(_: argparse.Namespace) -> int:
    accepted = is_accepted()
    problems = integrity_problems()
    print(f"安装确认: {'已确认' if accepted else '未确认'}")
    print(f"文件完整性: {'一致' if not problems else f'不一致（{len(problems)} 处）'}")
    for item in problems[:10]:
        print(f"  - {item}")
    return 0 if accepted and not problems else 1


def _cmd_accept(args: argparse.Namespace) -> int:
    if not args.yes:
        answer = input(QUESTION + "（是/否）: ").strip().lower()
        if answer not in YES_ANSWERS:
            print("未取得新华院书面许可，不得安装或使用本技能。")
            return 1
    print(f"已记录确认: {record_acceptance()}")
    return 0


def _cmd_check_modifier(_: argparse.Namespace) -> int:
    login = gh_login()
    if login == AUTHOR_LOGIN:
        print(f"OK: 本机 GitHub CLI 已登录作者账号 {AUTHOR_LOGIN}，允许修改。")
        return 0
    print(f"拒绝: 修改本技能须在本机 GitHub CLI 登录 {AUTHOR_LOGIN}（当前: {login or '未登录或无法验证'}）。")
    return 1


def _cmd_manifest(args: argparse.Namespace) -> int:
    if _cmd_check_modifier(args) != 0:
        return 1
    manifest = build_manifest()
    (SKILL_ROOT / MANIFEST_NAME).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"已写入 {MANIFEST_NAME}: {len(manifest['files'])} 个文件，版本 {manifest['version']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="chem-properties-excel license gate")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status").set_defaults(func=_cmd_status)
    accept = sub.add_parser("accept")
    accept.add_argument("--yes", action="store_true", help="用户已在对话中明确回答“是”")
    accept.set_defaults(func=_cmd_accept)
    sub.add_parser("check-modifier").set_defaults(func=_cmd_check_modifier)
    sub.add_parser("manifest").set_defaults(func=_cmd_manifest)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
