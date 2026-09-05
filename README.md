<div align="center">

# Database for PUR

### Evidence-grounded knowledge base for PU / PUR / HMPUR research

**把分散在论文、学位论文、专利、标准与工业资料中的 PUR 数据，转化为可检索、可追溯、可建模的实验级数据库。**

[![Status](https://img.shields.io/badge/status-active%20development-2ea44f?style=flat-square)](https://github.com/stloendays/Database-For-PUR)
[![Data](https://img.shields.io/badge/data-Batch%20004-0969da?style=flat-square)](data/cn/BATCH_004.md)
[![SQLite](https://img.shields.io/badge/database-SQLite-07405e?style=flat-square)](schema/pur_cn_v1.sql)
[![RAG](https://img.shields.io/badge/RAG-evidence--grounded-7b61ff?style=flat-square)](#rag--agent)
[![Inverse Design](https://img.shields.io/badge/use-inverse%20design-d97706?style=flat-square)](#research-focus)
[![Last Commit](https://img.shields.io/github/last-commit/stloendays/Database-For-PUR?style=flat-square)](https://github.com/stloendays/Database-For-PUR/commits/main)

[Overview](#overview) · [Data Snapshot](#data-snapshot) · [Schema](#data-model) · [Research](#research-focus) · [Quick Start](#quick-start) · [Evidence Policy](#evidence-policy) · [Roadmap](#roadmap)

</div>

---

## Overview

`Database-For-PUR` 是一个面向 **polyurethane / reactive polyurethane hot-melt adhesive (PUR/HMPUR)** 的结构化科研数据库。

它不是 PDF 收藏夹，也不是简单的文献索引。项目的核心是把公开资料拆解到实验层级：

> **Source → Experiment → Formulation → Material → Process → Measurement → Standard → Evidence**

目标是让每一个可用于分析或建模的数值，都能回答三个问题：

1. **它是什么？** — 物性、单位、测试温度、基材、固化时间等语义明确；
2. **它从哪里来？** — 保留 `source_id`、`evidence_locator`、原始链接与证据等级；
3. **它能不能用于模型？** — measured / claimed / inferred / secondary evidence 严格区分。

最终服务于：

- PUR 配方与工艺规律挖掘
- SQL / FTS / Vector RAG 检索
- 数据驱动的 property prediction
- formulation screening
- inverse design
- Agent-based evidence retrieval

---

## Data Snapshot

### Legacy HMPUR base

| Data layer | Records |
|---|---:|
| Sources | **21** |
| Standardized formulations | **85** |
| Formulation components | **278** |
| Property / performance observations | **547** |
| Experimental protocols | **22** |
| Temperature–viscosity points | **4,559** |
| Descriptor records | **1,599** |
| PU Tg ML samples | **226** |

### Chinese structured corpus — Batch 004

| Data layer | Records |
|---|---:|
| Chinese sources | **36** |
| Experiments | **42** |
| Formulations | **41** |
| Formulation components | **252** |
| Process steps | **137** |
| Measurements | **131** |
| Protocol records | **29** |
| Evidence records | **58** |
| CN patents | **10** |
| MSc thesis index | **10** |
| Chinese standards | **8** |

> 最新批次说明：[`data/cn/BATCH_004.md`](data/cn/BATCH_004.md)

---

## Data Model

```mermaid
flowchart LR
    A[Source] --> B[Experiment]
    B --> C[Formulation]
    C --> D[Formulation Component]
    D --> E[Material Master]
    B --> F[Process Step]
    B --> G[Measurement]
    G --> H[Protocol / Standard]
    A --> I[Evidence]
    B --> I
    C --> I
    G --> I

    E --> J[Descriptors]
    F --> K[ML / RAG / Inverse Design]
    G --> K
    J --> K
    I --> K
```

### Core tables

| Table | Purpose |
|---|---|
| `sources` | 论文、专利、学位论文、标准、TDS/SDS、报告等来源 |
| `experiments` | 一篇来源内部的 sample / example / comparative example |
| `materials` | 原料主表与标准化材料实体 |
| `formulations` | 配方级记录 |
| `formulation_components` | component-level 配方组成 |
| `process_steps` | 脱水、加料、预聚、扩链、真空脱泡等工艺步骤 |
| `measurements` | 黏度、NCO、open time、peel、lap shear、DSC 等观测值 |
| `protocols` | 测试方法、条件与标准 |
| `standard_index` | GB / HG/T 等标准索引 |
| `evidence` | 原始证据定位、证据类型与可信度 |
| `viscosity_curves` | 温度–黏度曲线点 |
| `thesis_index` | 中文硕博论文追踪与全文状态 |
| `rag_fts` | SQLite FTS5 全文检索入口 |

---

## Research Focus

### 1. Polyol blend → MDI prepolymer amplification

本数据库特别支持当前 HMPUR 研究中的核心假设：

> **多元醇共混物层面的微小性质差异，在进入 MDI 预聚物阶段后可能被系统性放大，而放大程度本身受 blend composition 调制。**

```text
raw material
    ↓
polyol blend
    ↓
pre-reaction state
    ↓
MDI prepolymer
    ↓
hot melt
    ↓
cured adhesive
```

优先变量：

`blend viscosity` · `prepolymer viscosity` · `NCO/OH` · `free NCO` · `OH value` · `acid value` · `Mn` · `polyol chemistry` · `reaction temperature` · `reaction time` · `DSC/crystallization` · `open time` · `green strength` · `peel` · `lap shear`

### 2. Mixing-law failure

数据库用于检验简单加性混合律是否能够闭合：

$$
X_{blend} \rightarrow X_{prepolymer} \rightarrow Y_{adhesive}
$$

并研究 composition-dependent amplification：

$$
A = \frac{\Delta \eta_{prepolymer}}{\Delta \eta_{blend}}
$$

### 3. Evidence-constrained inverse design

```text
Target properties
    ↓
Evidence-filtered formulation space
    ↓
Material + composition + process descriptors
    ↓
Candidate ranking
    ↓
Experimentally testable PUR formulations
```

---

## What is being collected?

### Literature

- 中文 / 英文期刊论文
- MSc / PhD 学位论文
- 会议论文与技术资料

### Patents

- CN patents
- WO / US / EP patent families
- example / comparative example / claimed range 分离

### Standards

当前已建立包括以下标准的结构化索引：

- `HG/T 3660-1999` — melt viscosity
- `HG/T 3716-2003` — open time
- `GB/T 16998-1997` — thermal stability
- `GB/T 15332-1994` — softening point
- `HG/T 5052-2016` — heat-fail temperature in shear
- `HG/T 3697-2016` — textile hot-melt adhesive
- `GB/T 2790-1995` — 180° peel
- `GB/T 7124-2008` — tensile lap-shear

### Industrial data

后续重点扩充：

- polyester polyol / polyether polyol / polycarbonate polyol TDS
- MDI grades
- tackifiers
- acrylic resins
- catalysts
- silanes
- supplier property sheets

---

## Repository Structure

```text
Database-For-PUR/
│
├── data/
│   ├── cn/                     # Chinese structured corpus
│   │   ├── BATCH_002.md
│   │   ├── BATCH_003.md
│   │   ├── BATCH_004.md
│   │   ├── thesis_index.csv
│   │   └── standard_index.csv
│   ├── legacy/                 # Existing HMPUR structured base
│   ├── master/                 # Terminology / material normalization
│   └── rag/                    # RAG-ready evidence units
│
├── schema/
│   └── pur_cn_v1.sql           # Unified SQLite schema
│
├── scripts/
│   ├── build_database.py       # Rebuild SQLite database
│   └── validate_database.py    # Integrity / FK / evidence checks
│
└── releases/
    └── cn_seed_batch_*.zip     # Cumulative structured releases
```

---

## Quick Start

### 1. Clone

```bash
git clone https://github.com/stloendays/Database-For-PUR.git
cd Database-For-PUR
```

### 2. Build SQLite database

```bash
python scripts/build_database.py --output database/pur_master.db
```

The builder automatically uses the latest cumulative Chinese release when needed.

### 3. Validate

```bash
python scripts/validate_database.py database/pur_master.db
```

### 4. Example SQL

Find PUR viscosity records around 120 °C:

```sql
SELECT
    source_id,
    formulation_id,
    sample_id,
    property_name_normalized,
    value,
    unit,
    temperature_c,
    evidence_type,
    quality_level
FROM measurements
WHERE property_name_normalized LIKE '%viscosity%'
  AND temperature_c BETWEEN 115 AND 125
ORDER BY value;
```

Find formulations with measured NCO data:

```sql
SELECT
    f.formulation_id,
    f.source_id,
    f.actual_nco_pct,
    m.value AS measured_nco,
    m.quality_level
FROM formulations f
JOIN measurements m
  ON f.formulation_id = m.formulation_id
WHERE m.property_name_normalized LIKE '%nco%';
```

---

## RAG / Agent

```mermaid
flowchart LR
    Q[User / Agent Query] --> S[SQL metadata filter]
    S --> F[FTS5 keyword recall]
    S --> V[Vector recall]
    F --> R[RRF / reranking]
    V --> R
    R --> E[Evidence-grounded answer]
```

Agent 输出候选配方或数值时，至少应同时返回：

```text
source_id
experiment_id
formulation_id
property / value / unit
measurement condition
evidence_type
quality_level
evidence_locator
source_url
```

---

## Evidence Policy

### Quality level

| Level | Definition | Default modeling use |
|---|---|---|
| **A** | 完整配方 + 工艺 + 测试条件 + 定量结果 + 原始证据定位 | ✅ preferred |
| **B** | 配方和定量结果可靠，但部分工艺/测试条件缺失 | ✅ usable with caution |
| **C** | 部分配方、范围、二手报道或间接信息 | ⚠️ RAG / weak supervision |
| **D** | 综述、背景资料、宣传资料 | ❌ not primary training data |

### Evidence type

```text
measured
example
comparative_example
reported
claimed_range
recommended_range
digitized_from_figure
inferred
secondary_reported
```

**Critical rules**

- Missing / not disclosed **≠ 0**
- 原始值与标准化值同时保留
- 测试温度、时间、基材、固化时间属于 measurement semantics
- patent claimed range 不得伪装成 measured example
- 二手引用不升级为原论文实验数据
- 图片表格无法可靠读取时，不为了增加 row count 猜数

---

## Copyright & Data Ethics

本仓库默认**不公开上传受版权保护的论文或学位论文全文**。

公开仓库主要保存：

- bibliographic metadata
- structured factual observations
- source URLs
- short evidence locators
- normalized experimental records
- legally redistributable open data

受限全文应由研究者在本地合法获取和维护。

---

## Roadmap

- [x] Legacy HMPUR database migration
- [x] PUR-CN relational schema
- [x] Chinese patent seed corpus
- [x] Quantitative Chinese journal extraction
- [x] MSc thesis index
- [x] Chinese test-standard layer
- [ ] Raw-material master database: polyols / MDI / tackifiers / catalysts / silanes
- [ ] Full thesis extraction where legally accessible
- [ ] Unified material descriptor layer
- [ ] Automated FTS + vector hybrid retrieval
- [ ] ML-ready export pipeline
- [ ] Blend → prepolymer amplification dataset
- [ ] Evidence-constrained inverse-design benchmark

---

## Current Development Direction

```text
Literature / Patents / Standards / TDS
                ↓
        Evidence extraction
                ↓
      Structured PUR database
                ↓
     Material + Process descriptors
                ↓
        RAG / ML / Agent layer
                ↓
          Inverse Design
                ↓
      Experimental validation
```

<div align="center">

**Database-For-PUR**  
*From scattered formulation evidence to machine-readable polyurethane design knowledge.*

</div>
