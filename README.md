<div align="center">

# chem-properties-excel

**从任意格式的化学品输入，一键生成全程可追溯的物性数据Excel表**

[![Claude Code Skill](https://img.shields.io/badge/Claude%20Code-Skill-blue?logo=anthropic)](https://claude.ai/code)
[![GitHub Release](https://img.shields.io/github/v/release/jonathanwong0086/chem-properties-excel)](https://github.com/jonathanwong0086/chem-properties-excel/releases)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python)](https://www.python.org/)
[![openpyxl](https://img.shields.io/badge/openpyxl-3.1%2B-green)](https://openpyxl.readthedocs.io/)
[![License: GPL-3.0-only](https://img.shields.io/badge/License-GPL--3.0-only-blue.svg)](LICENSE)

</div>

---

## 这是什么

一个 [Claude Code](https://claude.ai/code) / [Codex](https://openai.com/zh-Hans-CN/codex/) / [Workbuddy](https://www.codebuddy.cn/work/) / [Trae](https://www.trae.cn/) Skill，用于从工艺流程文本、设备一览表、SDS摘要、或化学品列表中提取化学品，查询物性数据，交叉比对中国法规标准，生成带来源注释的 Excel 物性数据表。

## 核心特性

- **吃脏数据** — 接收大段工艺描述、SDS全文、会议记录，自动提取化学品
- **人类可读的原文引用** — 输入是 OCR 转换的报告时，来源位置一律转成"章节号 + 表/图题 + 原文摘录"（如 `第4.5.3节表4.5.3-2《报警仪设置情况表》："105车间……三乙胺、甲苯、丙酮等"`），不再输出 `P* T* IMAGE***` 这类看不懂的内部标记
- **吃设备一览表** — 从设备表的"物料介质"列自动提取、归并变体（异体字/错别字/浓度前缀）、去重，生成介质-设备对照表
- **也吃干净列表** — 已整理好的名称列表直接用
- **14项物性数据** — CAS号、熔点、沸点、闪点、密度、物态、火灾类别、水溶性、爆炸极限、OEL等，**优先从本地结构化提取库查询**，未命中或字段缺失再联网补充
- **毒理数据（LD50/LC50）** — 同样优先查本地《危险化学品安全技术全书》库，未命中再联网补充
- **有毒气体检测目录** — 自动对照高毒物品目录、GB/T 50493-2019附录B、HG/T 20660-2017附录A、危化品目录剧毒物质
- **GB/T 42594-2023 介质危害** — 毒性、燃烧爆炸特性、材料相容性、反应稳定性、危害提示、GHS类别6列，按CAS/UN/名称从本地JSON原样抄录
- **易制毒/易制爆判定** — 对照本地结构化法定名录，输出管制类别或条件核实状态；浓度、形态、盐类信息不足时不会误判为“否”
- **本地离线参考数据** — SDS、OEL、危化品、有毒气体、GB/T 42594、易制毒和易制爆目录均提供本地参考文件及索引
- **来源注释** — 每个数据字段记录真实来源；同一可靠来源可以支持多个字段，鼠标悬停即可查看
- **智能着色** — 甲类红/乙类橙/丙类黄/非可燃白；标黄暂不设报警

## 快速开始

### 安装

Codex（Windows PowerShell）：

```powershell
New-Item -ItemType Directory -Force "$HOME\.codex\skills" | Out-Null
git clone https://github.com/jonathanwong0086/chem-properties-excel.git "$HOME\.codex\skills\chem-properties-excel"
pip install -r "$HOME\.codex\skills\chem-properties-excel\requirements.txt"
```

Codex（Linux/macOS）：

```bash
mkdir -p ~/.codex/skills
git clone https://github.com/jonathanwong0086/chem-properties-excel.git ~/.codex/skills/chem-properties-excel
pip install -r ~/.codex/skills/chem-properties-excel/requirements.txt
```

Claude Code：

```bash
mkdir -p ~/.claude/skills
git clone https://github.com/jonathanwong0086/chem-properties-excel.git ~/.claude/skills/chem-properties-excel
pip install -r ~/.claude/skills/chem-properties-excel/requirements.txt
```

### 使用

在 Codex 中使用 `$chem-properties-excel`，在 Claude Code 中使用 `/chem-properties-excel`，也可以直接说明任务：

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
| **物性数据主表** | 26列数据 + 来源注释 + 颜色标注 + 毒理数据列 + 有毒气体检测列 + GB/T42594 6列 + 易制毒/易制爆2列 | 26 |
| **数据来源汇总** | 18个数据来源机构、标准或法定目录 + 超链接 | 4 |
| **化学品清单** | 去重化学品列表 + 分类 + 涉及工段 + 有毒气体/易制毒/易制爆判定 | 10 |
| **介质-设备对照表** | 每种化学品对应的设备清单 + 火灾类别 + 有毒气体/易制毒/易制爆判定 | 11 |

后两个 Sheet 在输入为设备一览表时自动生成。

## 输入格式支持

| 形态 | 示例 | 处理方式 |
|------|------|----------|
| **设备一览表** | 含"物料介质"列的xlsx | 自动提取 → 归并变体 → 生成对照表 |
| **脏数据** | 大段工艺描述 | 自动提取 → 用户确认 → 查询 |
| **干净列表** | `乙腈、甲苯、甲醇` | 直接查询 |
| **半成品** | 名称+部分属性已有 | 仅补缺字段 |

## 本地离线参考数据

`SKILL.md` 同目录下的参考文件，agent 按 CAS 号直接比对，无需联网：

| 文件 | 内容 | 条目数 |
|------|------|--------|
| `gbz2.1-oel-reference.md` | GBZ 2.1-2007 职业接触限值（MAC/TWA/STEL） | 295种 |
| `hazcat-2015-reference.md` | 危险化学品目录(2015版) CAS + 危险性类别 + 剧毒标记 | 2552个CAS索引条目 |
| `toxic-gas-directory-reference.md` | 有毒气体检测目录（高毒目录 + GB/T50493 + HG/T20660 + 剧毒CAS） | 271种 |
| `gbt42594-2023-reference.json` | GB/T 42594-2023附录A 介质危害分类（毒性/燃烧爆炸/材料相容/反应稳定/危害/GHS，按CAS/UN/名称索引） | 601种 |
| `sds-handbook-reference.jsonl` + `sds-handbook-index.json` | 《危险化学品安全技术全书·通用卷》(第三版) 理化特性+毒理学信息(LD50/LC50)+消防措施原文摘录，按CAS/中英文名/别名索引 | 1006种（其中33种经人工核实，973种为OCR自动识别，命中后需在批注中标注可信度） |
| `precursor-chemicals-reference.md` | 易制毒化学品名录：类别、法定序号、名称/别名、CAS、盐类及范围条件 | 按法定目录完整收录 |
| `explosive-precursor-chemicals-reference.md` | 易制爆危险化学品名录(2017年版)：名称/别名、CAS、浓度/形态条件、燃爆分类 | 按法定目录完整收录 |
| `regulated-chemicals-index.json` | 易制毒与易制爆统一机器索引，支持CAS、规范名和别名查询 | 由上述两目录生成 |

> 本地GBZ数据仅来自2007版，不能引用为GBZ 2.1-2019。需要2019版结论时须另行核对原文或可靠现行数据库，并在批注中写明实际版本。
> 《危险化学品安全技术全书》数据经作者授权转载，仅提取"理化特性"、"毒理学信息"与"消防措施"三节原文，未经人工核实的条目在Excel批注中会有明确标注，正式合规文件请核对原书或联网复核。

## 数据来源

每个字段记录其真实来源。同一份SDS、数据库记录或法规条目确实提供多个字段时，允许重复引用该来源：

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
| GBZ 2.1-2007 / GBZ 2.1-2019 | 职业接触限值（本地2007版；2019版须另行核实） |
| GB 15603-1995 | 储存禁忌 |
| GB/T 42594-2023 | 毒性、燃烧爆炸特性、材料相容性、反应稳定性、危害提示、GHS类别 |
| GB/T 50493-2019附录B | 有毒气体蒸气特性表 |
| HG/T 20660-2017附录A | 毒物危害分类I/II级 |
| 《高毒物品目录》(2003) | 高毒物质OEL |
| 《危险化学品目录》(2015版) | 危化品类别、剧毒 |
| 《危险化学品安全技术全书·通用卷》(第三版) | 毒理数据 LD50/LC50（经作者授权转载） |
| 《易制毒化学品管理条例》及附表 | 是否易制毒、管制类别、盐类/范围条件 |
| 《易制爆危险化学品名录》(2017年版) | 是否易制爆、浓度/形态条件、主要燃爆危险性分类 |

## 目录结构

```
chem-properties-excel/
├── SKILL.md                          # Skill 定义（核心流程，v3.0.0）
├── README.md                         # 本文件
├── CHANGELOG.md                      # 版本历史
├── RELEASE_NOTES.md                  # 当前版本发布说明
├── LICENSE                           # GPL-3.0-only 许可证
├── requirements.txt                  # Python 运行依赖
├── generate_excel.py                 # Excel 生成模板脚本
├── gbz2.1-oel-reference.md           # 本地参考：GBZ 2.1 OEL数据（295种）
├── hazcat-2015-reference.md           # 本地参考：危化品目录（2552个CAS索引条目）
├── toxic-gas-directory-reference.md   # 本地参考：有毒气体检测目录（271种）
├── gbt42594-2023-reference.json       # 本地参考：GB/T 42594-2023 介质危害分类（601种）
├── sds-handbook-reference.jsonl       # 本地参考：《危险化学品安全技术全书》理化特性+毒理学信息+消防措施原文（1006种，经授权转载）
├── sds-handbook-index.json            # 本地参考：上述文件的CAS/中英文名/别名查找索引
├── precursor-chemicals-reference.md   # 本地参考：易制毒化学品名录
├── explosive-precursor-chemicals-reference.md # 本地参考：易制爆危险化学品名录
├── regulated-chemicals-index.json     # 易制毒/易制爆统一机器索引
├── tools/
│   ├── build_sds_reference.py         # 从MinerU RAG提取产物构建SDS参考文件
│   └── build_regulated_index.py       # 校验两类管制目录并重建统一索引
├── tests/                             # 参考库、索引和Excel生成回归测试
├── examples/
│   ├── input_messy.txt               # 脏数据输入示例
│   ├── input_list.txt                # 干净列表输入示例
│   └── output_description.md         # 输出结构说明
└── .gitignore
```

本项目不再维护Dify Chatflow版本；仓库中的历史导出文件不属于v3.0.0交付和验证范围。

## 依赖

```bash
pip install -r requirements.txt
```

## 验证

```bash
python tools/build_regulated_index.py --check
python -m unittest discover -s tests -v
```

监管目录、统一索引、Excel列结构、批注、合并区域、冻结窗格和安全输出文件名均包含回归测试。

## License

除非作者另行给予明确的书面授权，本项目的使用、复制、修改和分发均适用 [GNU General Public License v3.0 only](LICENSE)（GPL-3.0-only）。

如需申请作者特别授权，请联系：[wjc0086@163.com](mailto:wjc0086@163.com)。

### 第三方内容授权说明

Skill附件中包含出版物中的内容，用途限于本Skill的化学品物性数据查询，且仅限用于学习。该原书版权归原出版方/作者所有，本项目不对转载合法性以外的使用场景做背书。如对该数据的授权范围有疑问，请联系上方邮箱确认，或自行删除该文件后使用本项目的其余功能。如需商用，请自行获取相关知识产权授权。


## 特别提醒！！！

- **AI生成提醒** -
按地区法规，由AI生成的内容需明确标注AI生成提示，本项目未内置该标识功能，生成后请自行人工标注。
- **准确性提醒** -
本项目内置部分数据，仅可用于学习目的，如需商用授权，请自行联系出版社。作者不对其准确性负责，亦不对AI搜集及生成内容的准确性负责，请自行核实其准确性。
- **合规性提醒** -
本项目运行时涉及大模型联网等，请自行确认合规性后使用，作者不对本项目合规性、保密性负责。
- **损失自担** -
本项目运行时造成的所有损失由用户自担，请确认同意后安装使用本项目。

可预见本项目用户群体中包含小白用户，特留以上提醒。
