# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/lang/zh-CN/).

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

### Data Sources
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
