# Database-For-PUR v2

## Purpose

`pur_master_v2.db` keeps the validated Batch 005 relational master intact and adds a second integration layer for Batch 006-016.

The v2 design solves a specific problem: later batches contain scientifically important relationships that do not fit cleanly into a flat formulation/measurement table without losing semantics. Examples include matched precursor-product rheology, near-controlled formulation contrasts, staged reacted-state links, patent-family duplicate mappings, and objective-dependent candidate rankings.

## Integration model

```text
Batch 005 normalized core
        +
Batch 006-016 lossless staging rows
        +
Promoted scientific relationships
        +
Agent decision benchmarks
        =
pur_master_v2.db
```

Every Batch 006+ CSV row is retained verbatim in `staging_records.payload_json`. High-value relationships are additionally promoted into typed tables.

## New v2 tables

### `staging_batches` / `staging_records`
Lossless provenance layer. This is the safeguard against accidental information loss during normalization.

### `paired_measurements`
Typed precursor/product property links. The initial promoted set includes Batch 006 Stepan single-polyol -> MDI-prepolymer pairs, Batch 007 exact same-temperature DYNACOLL pairs, and Batch 011 unreacted polyol-blend -> urethane-prepolymer pairs. A numerical amplification ratio is generated only when precursor and product are measured at the same temperature.

### `controlled_contrasts` / `controlled_contrast_outcomes`
Stores intervention logic separately from response values, including changed factors, held or near-held factors, control class, outcomes and evidence strength.

### `series_definitions`
Represents designed multi-candidate panels, including the Batch 011 TDI-index series, Batch 015 formulation trajectories, and Batch 016 0/1/3/5 wt.% microsphere dose series.

### `scientific_links`
Stores mechanistic links that are useful but should not be mislabeled as precursor-blend amplification.

### `record_equivalence`
Explicit patent-family deduplication map. Batch 015's 17 repeated US6136136A records point to their Batch 008 canonical records with `action=do_not_duplicate`.

### `decision_benchmarks` / `decision_candidates`
Ground-truth candidate-selection tasks for blind Agent evaluation. Batch 016 is the first panel because the best candidate changes with the objective and constraints.

Examples:
- maximize 5-min cross peel -> 5 wt.% microspheres;
- maximize 20-min cross peel -> 0 wt.% control;
- maximize 5-min cross peel subject to viscosity <= 32,000 cP and density <= 0.90 g/mL -> 3 wt.% microspheres.

## Views

`v_exact_viscosity_amplification` contains direct same-temperature viscosity ratios with exact or single-polyol matched chemistry semantics.

`v_decision_ground_truth` exposes benchmark/candidate ground truth in query-friendly form.

## Build

```bash
python scripts/validate_all_staging.py
python scripts/build_database_v2.py --output database/pur_master_v2.db
python scripts/build_rag_fts.py database/pur_master_v2.db
python scripts/build_rag_v2.py database/pur_master_v2.db
python scripts/validate_database_v2.py database/pur_master_v2.db
python scripts/export_ml_agent_v2.py --db database/pur_master_v2.db --out-dir exports/v2
```

## Exports

- `paired_amplification.csv`
- `exact_same_temperature_amplification.csv`
- `controlled_contrasts.csv`
- `staging_manifest.csv`
- `record_equivalence.csv`
- `ml_formulation_matrix.csv`
- `decision_benchmarks.jsonl`
- `rag_documents.jsonl`

`ml_formulation_matrix.csv` deliberately keeps components and condition-bearing measurements in JSON columns rather than incorrectly pivoting unlike test methods or temperatures into one numeric feature.

## Current normalization boundary

- Batch 005 and earlier: normalized into the original relational schema;
- Batch 006-016: every row integrated losslessly, with scientifically important relationships promoted into dedicated typed tables;
- full remapping of every Batch 006-016 staging row into legacy `formulations`, `measurements`, `materials`, and `process_steps` remains a later normalization pass.

This boundary is intentional. It is safer than forcing heterogeneous patent/manufacturer tables into the old schema before their semantics are fully represented.
