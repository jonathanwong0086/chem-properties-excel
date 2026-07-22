<div align="center">

# 🧪 chem-properties-excel

**从任意格式的化学品输入，一键生成全程可追溯的物性数据Excel表**

[![Claude Code Skill](https://img.shields.io/badge/Claude%20Code-Skill-blue?logo=anthropic)](https://claude.ai/code)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python)](https://www.python.org/)
[![openpyxl](https://img.shields.io/badge/openpyxl-3.1%2B-green)](https://openpyxl.readthedocs.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

[English](#english) · [中文](#中文)

</div>

---

## 中文

### 这是什么

一个 [Claude Code](https://claude.ai/code) Skill，用于从工艺流程文本、SDS摘要、或化学品列表中提取化学品，联网查询物性数据，交叉比对中国法规标准，生成带来源注释的 Excel 物性数据表。

**核心特性：**
- 🗑️ **吃脏数据** — 接收大段工艺描述、SDS全文、会议记录，自动提取化学品
- 📋 **也吃干净列表** — 已整理好的名称列表直接用
- 🔍 **14项物性数据** — CAS号、熔点、沸点、闪点、密度、物态、火灾类别、水溶性、爆炸极限、OEL等
- 📐 **4部中国法规** — GB 50016-2014、GBZ 2.1-2019、危化品目录(2015版)、GB/T 42594-2023
- 🏷️ **351+来源注释** — 每个数据单元格独立标注来源URL，鼠标悬停即可查看
- 🎨 **智能着色** — 甲类红/乙类橙/丙类黄/非可燃白，仅3列着色不干扰

### 快速开始

#### 1. 安装 Skill

```bash
# 复制到 Claude Code skills 目录
cp -r . ~/.claude/skills/chem-properties-excel
```

#### 2. 使用

在 Claude Code 中输入：

```
/chem-properties-excel
```

或者直接说：

```
帮我把这些化学品生成物性Excel：乙腈、甲苯、甲醇、三乙胺
```

```
这是一段工艺流程文本，帮我提取所有化学品并生成物性表：
[粘贴你的工艺描述...]
```

#### 3. 输出

在桌面生成 `<项目名>化学品物性数据.xlsx`，包含两个Sheet：

| Sheet | 内容 |
|-------|------|
| **物性数据主表** | 16列数据 + 来源注释 + 颜色标注 |
| **数据来源汇总** | 12个数据来源机构/网站 + 超链接 |

### 输入格式支持

| 形态 | 示例 | 处理方式 |
|------|------|----------|
| **脏数据** | 大段工艺描述 | 自动提取 → 用户确认 → 查询 |
| **干净列表** | `乙腈、甲苯、甲醇` | 直接查询 |
| **半成品** | 名称+部分属性已有 | 仅补缺字段 |

### 数据来源

每个数据单元格来自不同来源，确保全程可追溯：

| 来源 | 提供数据 |
|------|----------|
| PubChem (NCBI) | CAS号、密度、水溶性 |
| NIST Chemistry WebBook | 熔点、沸点、蒸气相对密度 |
| Sigma-Aldrich | SDS、闪点、密度 |
| ChemicalBook | 物态、沸点、闪点 |
| CAMEO Chemicals (NOAA) | 遇水反应性、灭火禁忌 |
| NIOSH Pocket Guide (CDC) | 爆炸极限、蒸气密度 |
| GB 50016-2014 | 火灾危险性类别 |
| GBZ 2.1-2019 | 职业接触限值 |
| GB/T 42594-2023 | 毒性分级 |
| 危险化学品目录(2015版) | 危化品类别 |

### 示例

查看 [`examples/`](examples/) 目录：

- [`input_messy.txt`](examples/input_messy.txt) — 脏数据输入示例（工艺流程文本）
- [`input_list.txt`](examples/input_list.txt) — 干净列表输入示例
- [`output_description.md`](examples/output_description.md) — 输出Excel结构说明

### 目录结构

```
chem-properties-excel/
├── README.md                    # 本文件
├── SKILL.md                     # Claude Code Skill 定义（核心流程）
├── generate_excel.py            # Excel 生成模板脚本
├── CHANGELOG.md                 # 版本历史
├── LICENSE                      # MIT 许可证
├── examples/
│   ├── input_messy.txt          # 脏数据输入示例
│   ├── input_list.txt           # 干净列表输入示例
│   └── output_description.md    # 输出结构说明
└── .gitignore
```

### 依赖

```bash
pip install openpyxl
```

---

## English

### What is this

A [Claude Code](https://claude.ai/code) Skill that extracts chemicals from any format of input (process descriptions, SDS excerpts, or clean lists), queries physical property data online, cross-references Chinese regulatory standards, and generates an Excel spreadsheet with traceable source annotations.

### Key Features

- **Accepts messy input** — Process descriptions, SDS full text, meeting notes
- **Accepts clean lists** — Pre-organized chemical name lists
- **14 property fields** — CAS, melting point, boiling point, flash point, density, state, fire class, water solubility, explosion limits, OEL, etc.
- **4 Chinese regulations** — GB 50016-2014, GBZ 2.1-2019, Dangerous Chemicals Catalog (2015), GB/T 42594-2023
- **351+ source annotations** — Each cell annotated with its source URL
- **Smart color coding** — Red (Class A) / Orange (B) / Yellow (C) / White (non-combustible)

### Quick Start

```bash
# Install the skill
cp -r . ~/.claude/skills/chem-properties-excel

# Use in Claude Code
/chem-properties-excel
```

### Data Sources

| Source | Data Provided |
|--------|--------------|
| PubChem (NCBI) | CAS, density, solubility |
| NIST Chemistry WebBook | Melting/boiling points, vapor density |
| Sigma-Aldrich | SDS, flash point, density |
| ChemicalBook | State, boiling point, flash point |
| CAMEO Chemicals (NOAA) | Water reactivity, extinguishing |
| NIOSH Pocket Guide (CDC) | Explosion limits, vapor density |
| GB 50016-2014 | Fire hazard classification |
| GBZ 2.1-2019 | Occupational exposure limits |
| GB/T 42594-2023 | Toxicity classification |
| Dangerous Chemicals Catalog (2015) | Hazard category |

### License

[MIT](LICENSE)
