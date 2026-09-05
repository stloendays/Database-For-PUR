<div align="center">

# Database for PUR

### Evidence-grounded knowledge base for PU / PUR / HMPUR research

**Turning scattered PUR evidence from papers, theses, patents, standards and industrial documents into an experiment-level database that is searchable, traceable and model-ready.**

**English** | [简体中文](README.zh-CN.md)

<p align="center">
  <img src="assets/pur_overview_banner.svg" alt="Database for PUR overview banner" width="100%">
</p>

[![Status](https://img.shields.io/badge/status-active%20development-2ea44f?style=flat-square)](https://github.com/stloendays/Database-For-PUR)
[![Data](https://img.shields.io/badge/data-Batch%20005-0969da?style=flat-square)](data/materials/BATCH_005.md)
[![SQLite](https://img.shields.io/badge/database-SQLite-07405e?style=flat-square)](schema/pur_cn_v1.sql)
[![RAG](https://img.shields.io/badge/RAG-evidence--grounded-7b61ff?style=flat-square)](#rag--agent)
[![Inverse Design](https://img.shields.io/badge/use-inverse%20design-d97706?style=flat-square)](#research-focus)
[![Last Commit](https://img.shields.io/github/last-commit/stloendays/Database-For-PUR?style=flat-square)](https://github.com/stloendays/Database-For-PUR/commits/main)

[Overview](#overview) · [Data Snapshot](#data-snapshot) · [Data Model](#data-model) · [Research](#research-focus) · [Quick Start](#quick-start) · [Evidence Policy](#evidence-policy) · [Roadmap](#roadmap)

</div>

---

## Overview

`Database-For-PUR` is a structured research database for **polyurethane / reactive polyurethane hot-melt adhesive (PUR/HMPUR)** studies.

It is not a PDF collection and not merely a bibliography. The project decomposes public sources into an experiment-level chain:

> **Source → Experiment → Formulation → Material → Process → Measurement → Standard → Evidence**

Every value intended for analysis or modeling should answer three questions:

1. **What exactly is it?** — property, unit, test temperature, substrate, curing time and other semantics are explicit;
2. **Where did it come from?** — `source_id`, `evidence_locator`, source URL and evidence quality are preserved;
3. **Can it be used for modeling?** — measured, claimed, inferred and secondary evidence are separated.

Primary use cases include:

- PUR formulation/process mining
- SQL / FTS / vector RAG retrieval
- property prediction
- formulation screening
- inverse design
- evidence-grounded scientific agents

---

## Data Snapshot

### Legacy HMPUR cloud base

The pre-existing cloud HMPUR SQLite has been verified to contain:

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

The 4,559 temperature–viscosity points correspond to **39 distinct PU prepolymer viscosity curves**, spanning roughly 40–80 °C, multiple polyol/isocyanate codes, and pNCO values from 4–10 wt.%. The legacy inventory is exposed in [`data/legacy/cloud_inventory.csv`](data/legacy/cloud_inventory.csv).

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

> See [`data/cn/BATCH_004.md`](data/cn/BATCH_004.md)

### Corpus growth

<p align="center">
  <img src="assets/corpus_growth.svg" alt="Growth of Chinese PUR structured corpus" width="100%">
</p>

From Batch 001 to Batch 004, the Chinese structured corpus grew from **4 → 36 sources**, **16 → 42 experiments**, and **18 → 131 measurements**.

### Source composition

<p align="center">
  <img src="assets/source_mix.svg" alt="Source composition of Chinese PUR corpus" width="100%">
</p>

The current Chinese-domain source layer consists of **10 CN patents, 10 MSc theses, 8 standards, 7 journal papers and 1 secondary review source**. These source types are not treated equally during modeling: standards, metadata and secondary evidence mainly support semantics, method constraints and RAG rather than primary training targets.

### Batch 005 — raw-material descriptor layer

Batch 005 extends the project from formulation-level observations toward a **raw material → reaction → property** representation. Current additions include:

- **Evonik DYNACOLL 7000**: 21 polyester-polyol grades with OH number, acid number, molecular weight, Tg, Tm, softening point, density and melt viscosity;
- **DYNACOLL + 4,4′-MDI controlled RHM benchmark**: common OH:NCO = 1:2.2 conditions with open time, setting time, tensile strength, elongation and melt viscosity at 130 °C;
- **Covestro Desmophen 2002 / C 1200**: OH, acid, water, viscosity and equivalent-weight descriptors;
- **BASF Lupranate**: monomeric / modified / polymeric MDI and MDI prepolymers with NCO, functionality and viscosity at 25 °C;
- **Stepan polyester polyols**: multiple grades explicitly positioned for reactive hot-melt adhesive use.

See [`data/materials/BATCH_005.md`](data/materials/BATCH_005.md).

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
| `sources` | papers, patents, theses, standards, TDS/SDS and reports |
| `experiments` | sample / example / comparative example within a source |
| `materials` | normalized raw-material master entities |
| `formulations` | formulation-level records |
| `formulation_components` | component-level formulation composition |
| `process_steps` | drying, charging, prepolymerization, chain extension, degassing, etc. |
| `measurements` | viscosity, NCO, open time, peel, lap shear, DSC and other observations |
| `protocols` | test methods and conditions |
| `standard_index` | GB / HG/T and related standards |
| `evidence` | evidence locator, evidence type and quality |
| `viscosity_curves` | temperature–viscosity curve points |
| `thesis_index` | Chinese thesis tracking and full-text status |
| `rag_fts` | SQLite FTS5 retrieval entry point |

---

## Research Focus

### 1. Polyol blend → MDI prepolymer amplification

A central HMPUR hypothesis supported by this database is:

> **Small property differences at the polyol-blend level may be systematically amplified after entering the MDI prepolymer stage, with the amplification itself depending on blend composition.**

<p align="center">
  <img src="assets/research_workflow.svg" alt="PUR research workflow" width="100%">
</p>

Priority variables include:

`blend viscosity` · `prepolymer viscosity` · `NCO/OH` · `free NCO` · `OH value` · `acid value` · `Mn` · `polyol chemistry` · `reaction temperature` · `reaction time` · `DSC/crystallization` · `open time` · `green strength` · `peel` · `lap shear`

### Real composition–property trajectory

<p align="center">
  <img src="assets/pae_property_trends.svg" alt="PAE composition property trends in PUR" width="100%">
</p>

For `CN_JRN_WANG2026_PAE`, increasing PAE from **0 → 10 wt.%** changes melt viscosity from **1292 → 4821 mPa·s**, NCO from **3.372 → 2.411 wt.%**, and open time from **4.5 → 11.3 min**. Continuous trajectories like this are more valuable for composition-aware modeling than isolated optimum formulations.

### 2. Mixing-law failure

The database supports testing whether simple additive mixing laws can close the system:

$$
X_{blend} \rightarrow X_{prepolymer} \rightarrow Y_{adhesive}
$$

and whether amplification is composition dependent:

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

- Chinese and English journal papers, MSc/PhD theses and conference/technical documents;
- CN / WO / US / EP patents with example / comparative example / claimed range separation;
- GB / HG/T adhesive test standards;
- polyester / polyether / polycarbonate polyol TDS;
- MDI grades, tackifiers, acrylic resins, catalysts and silanes;
- legally redistributable open datasets and industrial technical material.

The repository **does not redistribute copyrighted full-text papers or theses by default**. It stores structured factual observations, metadata, source links, short evidence locators and legally shareable data.

---

## Repository Structure

```text
Database-For-PUR/
│
├── README.md                  # English
├── README.zh-CN.md            # 简体中文
├── assets/                    # README research/data visualizations
├── data/
│   ├── cn/                    # Chinese structured corpus
│   ├── legacy/                # legacy cloud inventory and migration indices
│   ├── materials/             # Batch 005 raw-material descriptor layer
│   ├── master/                # terminology / material normalization
│   └── rag/                   # RAG-ready evidence units
├── schema/
│   └── pur_cn_v1.sql
├── scripts/
│   ├── build_database.py
│   └── validate_database.py
└── releases/
    └── cn_seed_batch_*.zip
```

---

## Quick Start

```bash
git clone https://github.com/stloendays/Database-For-PUR.git
cd Database-For-PUR
python scripts/build_database.py --output database/pur_master.db
python scripts/validate_database.py database/pur_master.db
```

Example: find PUR viscosity records around 120 °C.

```sql
SELECT source_id, formulation_id, sample_id,
       property_name_normalized, value, unit,
       temperature_c, evidence_type, quality_level
FROM measurements
WHERE property_name_normalized LIKE '%viscosity%'
  AND temperature_c BETWEEN 115 AND 125
ORDER BY value;
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

Agent outputs should return at minimum: `source_id`, `experiment_id`, `formulation_id`, property/value/unit, measurement condition, `evidence_type`, `quality_level`, `evidence_locator` and `source_url`.

---

## Evidence Policy

| Level | Definition | Default modeling use |
|---|---|---|
| **A** | complete formulation + process + test conditions + quantitative result + traceable primary evidence | ✅ preferred |
| **B** | reliable formulation and quantitative result, but some process/test conditions are missing | ✅ usable with caution |
| **C** | partial formulation, ranges, indirect or secondary reporting | ⚠️ RAG / weak supervision |
| **D** | review, background or promotional information | ❌ not primary training data |

Evidence types include:

`measured` / `example` / `comparative_example` / `reported` / `claimed_range` / `recommended_range` / `digitized_from_figure` / `inferred` / `secondary_reported`

Critical rules:

- Missing / not disclosed **≠ 0**;
- original and normalized values are both retained;
- test temperature, time, substrate and curing time are part of measurement semantics;
- patent claimed ranges must not be treated as measured examples;
- manufacturer specifications must not be treated as independent experimental measurements;
- secondary citations are not promoted to primary experimental evidence;
- unreadable image tables are not guessed merely to increase row count.

---

## Roadmap

- [x] Legacy HMPUR database inventory & migration base
- [x] PUR-CN relational schema
- [x] Chinese patent seed corpus
- [x] Quantitative Chinese journal extraction
- [x] MSc thesis index
- [x] Chinese test-standard layer
- [x] Raw-material Batch 005 seed: polyols / MDI / controlled RHM benchmark
- [ ] Full 4,559-point legacy viscosity migration
- [ ] Full thesis extraction where legally accessible
- [ ] Unified material descriptor layer
- [ ] Automated FTS + vector hybrid retrieval
- [ ] ML-ready export pipeline
- [ ] Blend → prepolymer amplification dataset
- [ ] Evidence-constrained inverse-design benchmark

---

<div align="center">

**English** | [简体中文](README.zh-CN.md)

**Database-For-PUR**  
*From scattered formulation evidence to machine-readable polyurethane design knowledge.*

</div>
