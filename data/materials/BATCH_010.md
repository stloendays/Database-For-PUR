# Batch 010 — reactive-tackifier PUR benchmark: formulation → NCO/rheology/open time → dynamic peel → lap-shear development

## Scope

Batch 010 structures the example tables from **US20030022973A1, “Moisture cured polyurethane hot melt adhesives with reactive tackifiers”**. The source is unusually valuable for PUR decision modeling because the same sample IDs connect explicit formulation parts to reported NCO, melt viscosity, thermal stability, open time, temperature-resolved dynamic peel and 30 min–24 h lap-shear development.

This batch intentionally uses **Tables 5–13 only** for reconstructed formulations. Table 1 spans a PDF page break whose text layer drops row labels, so its formulation rows are not reconstructed here even though some downstream performance values are visible. This is an evidence-quality choice, not a data omission error.

## Files

- `batch010_sources.csv` — source registry.
- `batch010_methods.csv` — viscosity, open-time, dynamic-peel and lap-shear test semantics.
- `us20030022973_formulations_batch010.csv` — 13 explicit formulations from Tables 5, 6 and 11.
- `us20030022973_uncured_properties_batch010.csv` — NCO, melt viscosity, thermal-stability rise and open time.
- `us20030022973_dynamic_peel_batch010.csv` — temperature-resolved peel-displacement rates.
- `us20030022973_lapshear_batch010.csv` — 30 min, 2 h, 4 h and 24 h strength development.
- `us20030022973_controlled_contrasts_batch010.csv` — ten exact formulation contrasts.
- `scripts/validate_batch010.py` — integrity and semantics checks.

## Evidence semantics

1. Formulation amounts are stored as **parts by weight** exactly as reported. They are not normalized to 100 wt%.
2. Tables 9–10 explicitly label `% Free NCO`; Table 11 labels `% NCO`. The database therefore stores a row-level `nco_semantics` field and does not silently reinterpret Table 11 values as titrated free-NCO measurements.
3. The source does not disclose an NCO assay method for these example tables, so no analytical method is invented.
4. Melt viscosity for Tables 9–10 is linked to the patent’s Brookfield No. 27 method at 120 C. Table 11 states 250 F; the row-level temperature is retained as 121.111 C rather than rounded to 120 C.
5. Dynamic-peel dashes remain blank. Explicit reported zero values remain zero.
6. Lap shear is stored as the source’s time-resolved HPL/particle-board test, not mislabeled as an ASTM method.

## High-value controlled contrasts

### Dynacoll 7360 addition at fixed tackifier

Tables 5 and 6 create four matched A/B pairs. In each pair, B adds **19.5 parts Dynacoll 7360 (hexanediol adipate polyester diol)** while keeping PPG 2025, PPG 4025, Elvacite 2016, DMDEE, MDI and tackifier identity/parts unchanged.

- 4A → 4B, XR 4008: viscosity 15,000 → 37,000 cps; open time 9 → 9 min; 30-min lap shear 51 → 31 psi; 24-h lap shear 377 → 387 psi.
- 5A → 5B, RH 97M-NC: viscosity 7,900 → 15,400 cps; open time 17 → 30 min; 30-min lap shear 43 → 9 psi; 24-h lap shear 345 → 487 psi.
- 6A → 6B, RH 200-NC: viscosity 7,900 → 14,500 cps; open time 35 → 30 min; 30-min lap shear 10 → 15 psi; 24-h lap shear 329 → 482 psi.
- 7A → 7B, KE 615-3: viscosity 4,400 → 10,500 cps; open time 40 → 40 min; 30-min lap shear 12 → 25 psi; 24-h lap shear 365 → 516 psi.

The important modeling point is that adding the same polyester diol does **not** induce one fixed response pattern across tackifier chemistries: viscosity consistently rises, while open time and early/final strength responses depend on the tackifier background.

### Tackifier-identity substitutions

Within the A series and separately within the B series, XR 4008, RH 97M-NC, RH 200-NC and KE 615-3 are substituted at the same 19.5 reported parts while the remaining formulation is held fixed. This forms two independent tackifier-chemistry panels, one without and one with Dynacoll 7360.

These panels are useful for multi-objective agent benchmarks because the lowest-viscosity option is not automatically the highest early-strength or highest 24-h-strength option.

## Table 11 plastic / reactive-tackifier matrix

Samples 10A–10E retain PPG 2025, PPG 4025 and Dynacoll 7360 but vary Elvacite 2016, reactive tackifier and MDI amount. The source reports NCO, viscosity at 250 F and stability, plus dynamic peel and lap-shear development. Open time is not reported in Table 11 and is therefore left blank.

This matrix is not treated as a single-variable controlled series because MDI changes together with plastic/tackifier removal in some comparisons.

## Database role

Batch 010 adds a compact but information-dense **formulation → reaction-state proxy → rheology/processability → early/final adhesion** benchmark. It complements Batch 009: Batch 009 contains measured/titrated free-NCO examples and substrate-resolved cure development, while Batch 010 provides controlled polyester/tackifier formulation panels with open-time and green-strength proxies.

## SQLite / README status

This remains a staging-layer addition. The cumulative SQLite build is not modified in this batch, so README record-count statistics remain unchanged.
