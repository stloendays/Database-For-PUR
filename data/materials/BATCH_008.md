# Batch 008 — Henkel controlled polyester/PPG/MDI formulation series

## Scope

Batch 008 structures the experimental formulation series in **US5599895A, “Moisture-curing polyurethane hot-melt adhesive” (Roland Heider / Henkel)**. The source is unusually useful because it reports, within one patent and one preparation/test framework:

- explicit polyester identities A/B/C/D/I/H with molecular-weight, OH, Tg and selected raw-polyester viscosity data;
- total-formulation weight percentages for PPG 425, several polyester glycols, tackifier / hydrocarbon resin and 4,4'-MDI;
- example-specific NCO:OH ratios;
- measured hot-melt/prepolymer viscosities, especially at 130 C;
- short-time initial strength, selected 7-day mature bond strength and qualitative creep resistance;
- common preparation and test conditions.

The result is a compact **composition → reaction stoichiometry → rheology → adhesion** benchmark.

## Files

- `batch008_sources.csv` — source registry.
- `henkel_us5599895_materials_batch008.csv` — material definitions and raw-material descriptors.
- `henkel_us5599895_formulations_batch008.csv` — 17 structured formulation rows covering Examples 1-13, including the five subformulations in Example 12.
- `henkel_us5599895_process_methods_batch008.csv` — preparation, rheology, peel/strength and claim-level free-NCO semantics.
- `henkel_us5599895_controlled_contrasts_batch008.csv` — three predeclared near-controlled pairwise contrasts derived only from reported examples.
- `scripts/validate_batch008.py` — consistency checks for source links, formulation closure, ranges and contrast arithmetic.

## High-value controlled series

### Examples 6 vs 8: near-controlled C-to-D redistribution

The following blocks are essentially fixed:

- Polyester B = 5.8 wt%
- PPG 425 = 23.3 wt%
- beta-pinene tackifier = 5.8 wt%
- 4,4'-MDI = 24.3 wt%
- NCO:OH = 1.4:1
- Polyester A = 29.2 vs 29.1 wt%

The main change is:

- Polyester C: 5.8 → 1.1 wt%
- Polyester D: 5.8 → 10.5 wt%

Reported outcomes:

- viscosity at 130 C: **43 → 24 Pa.s**
- 5 min initial strength: **3.6 → 3.6 kg/cm**
- 7 day mature leather/SBR bond strength: **2.5 → 7.1 kg/cm**

This pair is especially useful because a small redistribution between two polyester chemistries produces a large rheology change while the reported 5 min initial strength remains unchanged.

### Example 12D vs 12E: near one-for-one A/B substitution

Held essentially fixed:

- Polyester C = 5.83 wt%
- Polyester I = 5.83 wt%
- PPG 425 = 23.34 wt%
- beta-pinene tackifier = 5.83 wt%
- MDI = 24.16 vs 24.15 wt%
- NCO:OH = 1.4:1

Main substitution:

- Polyester A: 23.34 → 29.17 wt%
- Polyester B: 11.67 → 5.83 wt%

Reported outcomes:

- viscosity at 130 C: **27 → 43 Pa.s**
- initial strength: **2.0 → 4.5 kg/cm**

The patent explicitly describes Polyester A as partially crystalline/high-viscosity and Polyester B as low-Tg. The pair therefore provides a clean chemistry-substitution benchmark without changing the polyether, tackifier or NCO:OH design variables.

### Examples 7 vs 9: reciprocal C/D swap

Examples 7 and 9 retain NCO:OH = 1.4:1 and keep A/B/PPG/tackifier nearly constant to within 0.1 wt%, while approximately swapping Polyester C and D:

- C: 1.2 → 10.5 wt%
- D: 10.5 → 1.2 wt%

The 130 C viscosity changes **22 → 27 Pa.s**, while the 5 min initial strength remains **3.6 kg/cm**. MDI changes from 24.3 to 23.9 wt%, so this contrast is classified `medium_high` rather than fully controlled.

## Evidence semantics

### What is measured

The example-table viscosities are reported hot-melt/prepolymer viscosities. For Examples 1-11 the patent describes a common preparation sequence: polyol components are dehydrated under vacuum at about 110-130 C for about 60 min, cooled to about 90 C, 4,4'-MDI is added, and the mixture is reacted at about 110-130 C under vacuum for about 60 min. Viscosity is then measured with a Brookfield Thermocell after 15 min preheating at the specified temperature.

### What is not measured

The patent does **not** report the viscosity of each complete polyol blend immediately before MDI addition. Therefore Batch 008 must **not** be labeled a direct matched-temperature precursor-blend → prepolymer amplification dataset. It is instead a controlled **formulation-composition → prepolymer rheology/adhesion** dataset.

Raw viscosity values for individual Polyester A/B/C/D/I/H are retained separately and must not be mistaken for whole-blend viscosity.

### Free NCO

US5599895A claims a general free-NCO range of 0.5-3 g per 100 g adhesive, preferably 1-2 g/100 g. These are stored only in `process_methods` as **claim-level ranges** and are not copied into individual example rows because the patent does not report measured free-NCO values for those examples.

### Strength-test comparability

- Examples 1-11 use the SBR / shoe-upper test context and report 5 min initial strength.
- Example 12 uses NBR/NBR strips and a 12.5 cm/min strength test; the exact elapsed time associated with the term “initial strength” is not explicitly restated, so the time field is left blank.
- Example 13 reports initial strength and test speed but does not explicitly restate substrate/timing; these fields remain blank.

Accordingly, absolute strength values should not be pooled across these test families without a test-context indicator.

## Validation policy

`validate_batch008.py` enforces:

1. all rows resolve to the registered source;
2. all 17 formulation records have unique IDs;
3. formulation component sums reproduce the patent totals and close to 100 wt% within 0.11 wt% rounding tolerance;
4. viscosity and strength ranges are ordered and positive;
5. example NCO:OH values remain limited to the reported 1.3:1, 1.4:1 and 1.5:1 levels;
6. controlled contrasts point to existing formulation rows and recompute viscosity deltas/ratios correctly;
7. the expected material definitions are present.

## Database role

Batch 008 adds a type of evidence that complements Batch 007:

- Batch 007 contains direct same-temperature raw-polyol → MDI-prepolymer viscosity amplification pairs from manufacturer data.
- Batch 008 adds controlled multi-component formulation series linking polyester identity/distribution to 130 C prepolymer viscosity and adhesive strength under a shared patent protocol.

Together, the two batches support separate questions: **reaction-stage amplification** and **composition sensitivity within reactive formulations**. They should remain analytically distinct.

## SQLite / README status

This batch is a staging-layer addition. The cumulative SQLite build has not been updated in this change, so README database-count statistics are intentionally unchanged.
