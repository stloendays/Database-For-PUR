# Batch 005 — Raw-material layer + legacy cloud provenance

Date: 2026-09-05

## Why this batch exists

Batch 005 starts the raw-material descriptor layer needed for formulation screening and inverse design. It also exposes the inventory of the pre-existing cloud HMPUR database so legacy statistics are no longer shown only in the README.

## Legacy cloud database inventory

The pre-existing HMPUR SQLite contains:

- sources: 21
- formulations: 85
- components: 278
- observations: 547
- protocols: 22
- viscosity_curves: 4,559
- descriptor_values: 1,599
- datasets: 13
- tg_ml_dataset: 226

A compact inventory is committed as `data/legacy/cloud_inventory.csv`.

The legacy viscosity dataset contains 39 distinct PU prepolymer curve samples over roughly 40–80 °C, spanning polyol codes P/D/C, isocyanate codes 44M/MLQ/TD80/I/W/TDS, and pNCO values 4–10 wt.%. The full 4,559-point migration remains a separate follow-up task.

## New official manufacturer sources

### Evonik — DYNACOLL 7000

Official product-range brochure provides 21 linear polyester-polyol grades with common descriptors including:

- hydroxyl number
- acid number
- molecular weight
- Tg
- melting point
- softening point
- density
- melt viscosity at 80 or 130 °C

The same brochure also gives a controlled RHM reference dataset where every grade is reacted with 4,4'-MDI at OH:NCO = 1:2.2 under common preparation conditions:

- polyester drying: 130 °C, <10 mbar, 45 min
- reaction: 130 °C under dry N2 or CO2
- endpoint: theoretical free isocyanate content
- after 45 min: vacuum degassing until bubble-free

Reported outputs include softening point, open time, setting time, tensile strength, elongation, and melt viscosity at 130 °C.

This is particularly valuable because it behaves like a manufacturer-controlled `raw-material descriptors -> RHM properties` benchmark.

### Covestro — Desmophen 2002

Official product page reports specification values including:

- OH number: 52–58 mg KOH/g
- dynamic viscosity: 500–700 mPa.s at 75 °C
- water: <=0.05 wt.%
- acid number: <=0.8 mg KOH/g
- approximate equivalent weight: 1039 g/mol

### Covestro — Desmophen C 1200

Official product page reports:

- approximate OH number: 56.1 mg KOH/g
- viscosity: 16,500 ± 2,500 mPa.s at 23 °C
- approximate density: 1.10 g/mL
- approximate water: 0.05 wt.%
- approximate acid number: 0.1 mg KOH/g
- approximate equivalent weight: 1000 g/mol

### BASF — Lupranate aromatic isocyanates

Selected official product-family anchors are committed for monomeric MDI, modified/polymeric MDI and MDI prepolymers. Stored fields include NCO wt.%, nominal functionality, viscosity at 25 °C and storage temperature range.

Examples:

| Grade | Type | NCO wt.% | Functionality | Viscosity @25 °C |
|---|---|---:|---:|---:|
| Lupranate 227 | monomeric MDI | 32.1 | 2.0 | 15 cP |
| Lupranate MI | monomeric MDI | 33.5 | 2.0 | 15 cP |
| Lupranate 5143 | carbodiimide-modified MDI | 29.2 | 2.2 | 40 cP |
| Lupranate M20 | polymeric MDI | 31.5 | 2.7 | 200 cP |
| Lupranate 5020 | MDI prepolymer | 9.5 | 2.0 | 2500 cP |
| Lupranate 5025 | MDI prepolymer | 12.9 | 2.0 | 2250 cP |
| Lupranate 5030 | MDI prepolymer | 18.9 | 2.0 | 1130 cP |
| Lupranate 5040 | MDI prepolymer | 26.3 | 2.1 | 140 cP |

### Stepan — polyester polyol anchors for reactive hot melts

Five additional official Stepan anchors were added because their product pages/bulletins explicitly identify adhesive or reactive-hot-melt use:

| Grade | OH (mg KOH/g) | Acid (mg KOH/g) | Viscosity | RHM relevance |
|---|---:|---:|---:|---|
| STEPANPOL PC-205P-56 | 54–58 | <=1.0 | 2800 cP @ 80 °C | polyurethane adhesives; shorter open time / higher green strength |
| STEPANPOL PC-5120P-20 | 22 | 3 | 6000 cP @ 25 °C | Reactive Hot Melt Adhesives |
| STEPANPOL PDP-70 | 70 | 1 | 1900 cP @ 25 °C | Reactive Hot Melt Adhesives |
| STEPANPOL PC-5000P-30 | 30 | 1 | 10200 cP @ 25 °C | prepolymer grade; Reactive Hot Melt Adhesives |
| STEPANPOL PC-5090P-56 | 55 | 0.7 | 1500 cP @ 60 °C | polyurethane adhesives |

PC-205P-56 also provides water <=0.05 wt.%, equivalent weight 1000 g/eq OH, functionality 2.0 and melting point 64 °C.

## Files added

- `data/materials/batch005_sources.csv`
- `data/materials/material_property_summary_batch005.csv`
- `data/materials/isocyanate_property_summary_batch005.csv`
- `data/materials/evonik_rhm_reference_batch005.csv`
- `data/materials/stepan_polyols_batch005.csv`
- `data/legacy/cloud_inventory.csv`

## Evidence rules

1. Manufacturer specifications are stored as `reported/specification`, not as independent experimental measurements.
2. Ranges stay as ranges; no midpoint is silently substituted.
3. Manufacturer-controlled RHM tables are kept separate from literature/patent experiments.
4. Legacy cloud records retain their original provenance and will be migrated without rewriting source semantics.
