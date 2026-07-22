<div align="center">

# chem-properties-excel

**从任意格式的化学品输入，一键生成全程可追溯的物性数据Excel表**

[![Claude Code Skill](https://img.shields.io/badge/Claude%20Code-Skill-blue?logo=anthropic)](https://claude.ai/code)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python)](https://www.python.org/)
[![openpyxl](https://img.shields.io/badge/openpyxl-3.1%2B-green)](https://openpyxl.readthedocs.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## 这是什么

一个 [Claude Code](https://claude.ai/code) Skill，用于从工艺流程文本、设备一览表、SDS摘要、或化学品列表中提取化学品，查询物性数据，交叉比对中国法规标准，生成带来源注释的 Excel 物性数据表。

## 核心特性

- **吃脏数据** — 接收大段工艺描述、SDS全文、会议记录，自动提取化学品
- **吃设备一览表** — 从设备表的"物料介质"列自动提取、归并变体（异体字/错别字/浓度前缀）、去重，生成介质-设备对照表
- **也吃干净列表** — 已整理好的名称列表直接用
- **14项物性数据** — CAS号、熔点、沸点、闪点、密度、物态、火灾类别、水溶性、爆炸极限、OEL等
- **有毒气体检测目录** — 自动对照高毒物品目录、GB/T 50493-2019附录B、HG/T 20660-2017附录A、危化品目录剧毒物质
- **本地离线参考数据** — 3个 `.md` 参考文件包含 3000+ 条 CAS 记录，agent 直接读取比对，无需联网
- **714+ 来源注释** — 每个数据单元格独立标注来源URL，鼠标悬停即可查看
- **智能着色** — 甲类红/乙类橙/丙类黄/非可燃白；标黄暂不设报警

## 快速开始

### 安装

```bash
cp -r . ~/.claude/skills/chem-properties-excel
```

### 使用

在 Claude Code 中输入 `/chem-properties-excel`，或直接说：

```
帮我把这些化学品生成物性Excel：乙腈、甲苯、甲醇、三乙胺
```

```
这是设备一览表，帮我提取化学品并生成物性表 + 介质设备对照表
```

### 输出

生成 `<项目名>化学品物性数据.xlsx`，包含四个 Sheet：

| Sheet | 内容 | 列数 |
|-------|------|------|
| **物性数据主表** | 17列数据 + 来源注释 + 颜色标注 + 有毒气体检测列 | 17 |
| **数据来源汇总** | 16个数据来源机构/网站 + 超链接 | 4 |
| **化学品清单** | 去重化学品列表 + 分类 + 涉及工段 + 有毒气体检测列 | 8 |
| **介质-设备对照表** | 每种化学品对应的设备清单 + 火灾类别 + 有毒气体检测列 | 9 |

后两个 Sheet 在输入为设备一览表时自动生成。

## 输入格式支持

| 形态 | 示例 | 处理方式 |
|------|------|----------|
| **设备一览表** | 含"物料介质"列的xlsx | 自动提取 → 归并变体 → 生成对照表 |
| **脏数据** | 大段工艺描述 | 自动提取 → 用户确认 → 查询 |
| **干净列表** | `乙腈、甲苯、甲醇` | 直接查询 |
| **半成品** | 名称+部分属性已有 | 仅补缺字段 |

## 本地离线参考数据

`SKILL.md` 同目录下的3个参考文件，agent 按 CAS 号直接比对，无需联网：

| 文件 | 内容 | 条目数 |
|------|------|--------|
| `gbz2.1-oel-reference.md` | GBZ 2.1-2007 职业接触限值（MAC/TWA/STEL） | 295种 |
| `hazcat-2015-reference.md` | 危险化学品目录(2015版) CAS + 危险性类别 + 剧毒标记 | 2674种 |
| `toxic-gas-directory-reference.md` | 有毒气体检测目录（高毒目录 + GB/T50493 + HG/T20660 + 剧毒CAS） | 271种 |

> GBZ 数据基于 2007 版提取，2019 版为现行版本。未命中的化学品应联网查询 2019 版确认。

## 数据来源

每个数据单元格来自不同来源，同行不同列来源不同：

| 来源 | 提供数据 |
|------|----------|
| PubChem (NCBI) | CAS号、密度、水溶性 |
| NIST Chemistry WebBook | 熔点、沸点、蒸气相对密度 |
| Sigma-Aldrich | SDS、闪点、密度 |
| ChemicalBook | 物态、沸点、闪点 |
| CAMEO Chemicals (NOAA) | 遇水反应性、灭火禁忌 |
| NIOSH Pocket Guide (CDC) | 爆炸极限、蒸气密度 |
| FAO/WHO JMPR | 农药原药物化及毒性 |
| GB 50016-2014 | 火灾危险性类别 |
| GBZ 2.1-2019 | 职业接触限值 |
| GB 15603-1995 | 储存禁忌 |
| GB/T 42594-2023 | 毒性分级 |
| GB/T 50493-2019附录B | 有毒气体蒸气特性表 |
| HG/T 20660-2017附录A | 毒物危害分类I/II级 |
| 《高毒物品目录》(2003) | 高毒物质OEL |
| 《危险化学品目录》(2015版) | 危化品类别、剧毒 |

## 目录结构

```
chem-properties-excel/
├── SKILL.md                          # Skill 定义（核心流程，v2.1.0）
├── README.md                         # 本文件
├── CHANGELOG.md                      # 版本历史
├── LICENSE                           # MIT 许可证
├── generate_excel.py                 # Excel 生成模板脚本
├── gbz2.1-oel-reference.md           # 本地参考：GBZ 2.1 OEL数据（295种）
├── hazcat-2015-reference.md           # 本地参考：危化品目录（2674种）
├── toxic-gas-directory-reference.md   # 本地参考：有毒气体检测目录（271种）
├── examples/
│   ├── input_messy.txt               # 脏数据输入示例
│   ├── input_list.txt                # 干净列表输入示例
│   └── output_description.md         # 输出结构说明
└── .gitignore
```

## 依赖

```bash
pip install openpyxl
```

## License

[MIT](LICENSE)
