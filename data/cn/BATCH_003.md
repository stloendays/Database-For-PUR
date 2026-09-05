# Batch 003 — Chinese theses + quantitative journal datasets

Date: 2026-09-05

## Purpose

Batch 003 separates two evidence classes:

1. **Quantitative journal datasets**: public tables/abstracts are structured into experiments/formulations/measurements.
2. **Chinese MSc thesis index**: bibliographic metadata is stored now, but no experimental values are promoted into training tables until the full thesis is available and checked.

## New high-value quantitative sources

### Wang et al. 2026 — PAE-modified moisture-curing PUR
Source: https://gxhxgcxb.xml-journal.net/article/doi/10.3969/j.issn.1003-9015.2025-0256

Public HTML exposes Tables 1-4. The database now includes the PAE 0/2/4/6/8/10 wt.% series (R=2): viscosity, NCO content, open time, tensile strength, elongation and hydrogen-bond index, plus the Blank/BDO/PAE chain-extender comparison.

**Integrity note:** the abstract says PAE-6 viscosity = **3325 mPa.s**, while Table 2 says **3329 mPa.s**. The structured measurement uses the table value and preserves the discrepancy in `notes`.

### Liu et al. 2025 — Al/PVC PUR
Source: https://pmse.scu.edu.cn/gfzclkxygc/article/abstract/20250501

Optimum reported condition: `R=2`, `n(PHA):n(PTMG)=4:6`, `80 C`, `2 h`; initial peel `18.6 N/25mm`, final peel `49.7 N/25mm`, initial decomposition `297 C`; rheology stable over `600 s` at `120 C`.

### Xiao et al. 2025 — high-temperature electronic PUR
Evidence URL: https://www.catia-china.com/post.html?id=68e8629679ec76608c11100f

Complete reported optimum 100 wt.% formulation: 15% polyphenylene-ether polyol, 29.5% polyether polyol, 15% acrylic resin, 20% 7360 crystalline polyester polyol, 0.5% DMDEE and 20% MDI. Reported viscosity `7400 mPa.s @ 110 C`, shear strength `11.51 MPa`, high-temperature shear `2.42 MPa`, and `85%` shear retention after 120 C aging.

### Additional journal anchors
- Zhan 2008: NCO≈3.5%, catalyst 0.1%, tackifier 20%, open time 7 min, cure 24 h, tensile 9.3 MPa, initial bond 0.44 MPa, shear 7.9 MPa.
- Cong et al. 2022: R=1.8-2.2, polyester/polyether=1:1, 120 C viscosity 1700-6000 mPa.s, open time 1-9 min.
- Qiu et al. 2026: 5880 mPa.s @130 C, surface drying 23 s, peel 48 N/25mm, Shore A 71.
- Ye 2019: directional factor map and anchors (optimal NCO 1.6 wt.%, catalyst threshold 0.10 wt.%).

## Thesis index added

10 Chinese MSc theses are indexed, including SCUT, ECUST, BUCT, Hunan University, Guangdong University of Technology, Dalian Polytechnic University and CCNU records. `thesis_index.csv` explicitly marks them `awaiting_fulltext`.

High-priority thesis targets include:
- 翁鋆 (SCUT, 2023), 高初粘强度与结晶行为
- 陈旭欣 (SCUT, 2024), 耐热 PUR
- 曹盛 (ECUST, 2016), 湿固化 PUR 制备与改性
- 马宇彤 (CCNU, 2025), 海绵/涤纶贴合 PUR

## Cumulative Chinese structured corpus after Batch 003

| table | rows |
|---|---:|
| sources.csv | 26 |
| experiments.csv | 41 |
| formulations.csv | 41 |
| formulation_components.csv | 252 |
| process_steps.csv | 133 |
| measurements.csv | 125 |
| protocols.csv | 19 |
| evidence.csv | 54 |
| patents.csv | 9 |
| thesis_index.csv | 10 |

## Training rule

`metadata_only_awaiting_fulltext` thesis sources are discoverable by RAG/Agent but **must not be treated as numerical training observations** until full-text extraction is completed.
