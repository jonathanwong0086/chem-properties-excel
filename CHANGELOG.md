# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/lang/zh-CN/).

## [2.1.0] - 2026-07-22

### Added
- **本地离线参考数据**：新增3个 `.md` 参考文件，agent按CAS号直接比对，无需联网
  - `gbz2.1-oel-reference.md`：GBZ 2.1-2007 职业接触限值（295种化学品，MAC/TWA/STEL）
  - `hazcat-2015-reference.md`：危险化学品目录(2015版)（2674种，CAS+危险性类别+剧毒标记）
  - `toxic-gas-directory-reference.md`：有毒气体检测目录（高毒54种+GB/T50493补充3种+HG/T20660 66种标黄+剧毒148种CAS）
- §3.2/§3.3 优先读取本地参考文件，未命中时再联网查

### Changed
- **设备表介质列识别改为通用方法**：不再硬编码8种设备类型列号，改为动态读取表头行按关键字匹配（`介质`/`物料`/`主要介质`/`主要成分`），适用于任何项目的设备一览表
- SKILL.md 中 §3.2（GBZ OEL）、§3.3（危化品目录）、§3.4（有毒气体）均增加本地参考文件读取指引

## [2.0.0] - 2026-07-21

### Added
- **设备一览表介质提取**（§0.5）：从设备表"物料介质"列自动提取化学品，支持变体归并（异体字/错别字/浓度前缀剥离）
- **有毒气体检测目录**（§3.4）：对照高毒物品目录、GB/T 50493-2019附录B、HG/T 20660-2017附录A、危化品目录剧毒物质
  - 命中高毒/剧毒：`是，应设报警，来自《高毒物品目录》`
  - 命中HG/T 20660/GB/T 50493（标黄）：`是，暂不设报警，来自HG/T 20660-2017`
- **Excel四Sheet输出**：
  - Sheet 1 物性数据主表：16列 → 17列（新增"是否被列入有毒气体检测目录"）
  - Sheet 2 数据来源汇总：12项 → 16项（新增GB/T 50493、HG/T 20660、高毒物品目录、FAO/WHO JMPR）
  - Sheet 3 化学品清单（可选）：去重化学品+分类+涉及工段+有毒气体列
  - Sheet 4 介质-设备对照表（可选）：化学品-设备映射+火灾类别+有毒气体列+交替底色
- **Agent并行批次查询**（§2）：结果写入JSON文件避免上下文截断，4批并行
- **数据源扩充至16项**：新增 GB/T 50493-2019、HG/T 20660-2017、《高毒物品目录》、FAO/WHO JMPR

### Removed
- DLP透明加密处理章节（不应出现在skill中）

### Changed
- SKILL.md版本从1.0.0升级至2.0.0
- 流程图更新为5步完整流程

## [1.0.0] - 2026-07-13

### Added
- 初始版本发布
- 支持三种输入形态：脏数据、干净列表、半成品
- 14项物性数据字段（CAS号、熔点、沸点、闪点、密度、物态、火灾类别、水溶性、密度对比、禁用水灭火、爆炸极限、蒸气密度对比、OEL、危化品类别）
- 12个数据来源（7个国际数据库 + 5部中国法规标准）
- Excel双Sheet输出（物性数据主表 + 数据来源汇总）
- 每个单元格独立来源注释，同行不同列来源不同
- 火灾危险性着色（甲类红/乙类橙/丙类黄/非可燃白），仅3列着色
- Windows中文文件名安全写入机制（ASCII临时文件 + rename）
- 详细的SKILL.md流程定义和查询指南
- generate_excel.py 模板脚本

### Data Sources (v1.0.0)
- PubChem (NCBI) — CAS号、密度、水溶性
- NIST Chemistry WebBook — 熔点、沸点、蒸气相对密度
- Sigma-Aldrich / MilliporeSigma — SDS、闪点、密度
- ChemicalBook — CAS号、沸点、闪点、物态
- ChemSpider (RSC) — 常温物态
- CAMEO Chemicals (NOAA) — 遇水反应性、灭火禁忌
- NIOSH Pocket Guide (CDC) — 爆炸极限、蒸气密度
- GB 50016-2014 — 火灾危险性类别
- GBZ 2.1-2019 — 职业接触限值
- GB 15603-1995 — 储存禁忌
- GB/T 42594-2023 — 毒性分级
- 《危险化学品目录》(2015版) — 危化品类别
