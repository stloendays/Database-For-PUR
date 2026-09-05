# Batch 004 — Standards layer + thesis provenance audit + patent process envelope

Date: 2026-09-05

## Main additions

- 8 official Chinese adhesive/hot-melt standards are now first-class `standard_index` records.
- Added CN116265556B as a text-grounded process/property-envelope source. Image-only formulation/performance tables were deliberately not transcribed.
- Audited the four high-priority theses from Batch 003. No legally open full text was found for Weng 2023, Chen 2024, Cao 2016, or Ma 2025; all remain `awaiting_fulltext`.
- Ma 2025 is independently verified from the CCNU Chemistry institutional defense page.
- Cao 2016 receives a separate **secondary evidence** record from the 2017 PUR review reprint; secondary reported conditions remain excluded from primary numerical training.

## Standards included

- HG/T 3660-1999 — melt viscosity
- HG/T 3716-2003 — open time
- GB/T 16998-1997 — thermal stability
- GB/T 15332-1994 — softening point (ball-and-ring)
- HG/T 5052-2016 — heat-fail temperature in shear
- HG/T 3697-2016 — textile hot-melt adhesives
- GB/T 2790-1995 — 180 degree peel, flexible-to-rigid
- GB/T 7124-2008 — tensile lap-shear, rigid-to-rigid

As of 2026-09-05, GB/T 7124-2008 remains current, while revision project 20263575-T-606 (issued 2026-06-27) is in drafting.

## CN116265556B high-value text-explicit anchors

- pre-chain-extension prepolymer NCO preferred: **2.9–3.7 wt.%**
- final NCO preferred: **1.8–2.6 wt.%**
- final melt viscosity preferred: **20,000–30,000 mPa.s @ 120 C**
- temperature-sensitive polyester polyol: **400–1,000 mPa.s @ 120 C** and **10,000–30,000 mPa.s @ 60 C**
- clean-free time: **>=72 h @ 23 C / 50% RH**
- common process: 120 C dehydration/defoaming 2 h -> cool to 80 C -> isocyanate/prepolymer reaction 1 h -> chain extension to theoretical NCO endpoint

These are stored as `claimed_range`/process evidence, not as measured example values.

## Current cumulative rows

- `evidence.csv`: 58
- `experiments.csv`: 42
- `formulation_components.csv`: 252
- `formulations.csv`: 41
- `measurements.csv`: 131
- `patents.csv`: 10
- `process_steps.csv`: 137
- `protocols.csv`: 29
- `sources.csv`: 36
- `standard_index.csv`: 8
- `thesis_index.csv`: 10

## Training discipline

1. Official standards define test semantics but are not formulation observations.
2. `claimed_range` patent values must be distinguishable from measured example values.
3. `secondary_reported` thesis summaries remain RAG evidence only until the original thesis is checked.
4. Missing image tables are never guessed/OCR-filled merely to increase row count.
