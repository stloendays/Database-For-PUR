# Batch 016 — hollow-microsphere rheology / open-time / green-strength kinetics panel

## Scope

Batch 016 structures the controlled example series from **US20070155859A1, “Reactive polyurethane hot melt adhesive”** (Henkel; Zhengzhe Song, Yingjie Li, Jason Smith).

The source starts from one commercial moisture-reactive PUR hot-melt adhesive, **QR-4668**, and modifies it only by adding **0, 1, 3, or 5 wt.% DUALITE E-136-040D hollow polymeric microspheres**. It then reports, for the same four conditions:

- viscosity at **121 C**;
- source-defined open time;
- adhesive density;
- cross-peel strength at **0, 5, 8, 11, 14, 17, and 20 min**.

This yields a compact controlled chain:

`fixed reactive PUR base + microsphere dose -> melt rheology / density -> open time -> early cross-peel strength trajectory`

Batch 016 is therefore primarily a **physical-structure / rheology / green-strength kinetics benchmark**. It is not a polyol-blend-to-prepolymer amplification dataset and it does not contain example-specific NCO/OH or free-NCO measurements.

## Source and family

The structured source is US20070155859A1, published 2007-07-05 from priority 2006-01-04. The same application family includes PCT/US2006/062273 / WO2007081645A2 and EP06849175A.

Only one family member is represented numerically in Batch 016; family publications are not counted as independent experiments.

## Controlled formulation panel

The example intervention is unusually clean for a patent dataset:

| example | microspheres (wt.%) | viscosity @121 C (cps) | open time (min) | density (g/mL) | 5-min cross peel (psi) |
|---|---:|---:|---:|---:|---:|
| EX1 control | 0 | 12,750 | 5.5 | 1.06 | 33.7 |
| EX2 | 1 | 20,000 | 3.5 | 0.96 | 45.0 |
| EX3 | 3 | 32,000 | 2.5 | 0.89 | 79.0 |
| EX4 | 5 | 48,000 | 2.0 | 0.82 | 83.7 |

Relative to the microsphere-free control:

- **1 wt.%**: viscosity 1.569x, open time 0.636x, density 0.906x, 5-min cross peel 1.335x;
- **3 wt.%**: viscosity 2.510x, open time 0.455x, density 0.840x, 5-min cross peel 2.344x;
- **5 wt.%**: viscosity 3.765x, open time 0.364x, density 0.774x, 5-min cross peel 2.484x.

These contrasts are stored as `controlled_additive_dose` with very-high evidence strength because the source explicitly states that the same commercial reactive PUR hot melt was modified by the reported microsphere loadings.

## Time-resolved cross-peel kinetics

Table II is retained as 28 long-format records rather than collapsed into a single green-strength value.

| time (min) | EX1 | EX2 | EX3 | EX4 |
|---:|---:|---:|---:|---:|
| 0 | 0 | 0 | 0 | 0 |
| 5 | 33.7 | 45.0 | 79.0 | 83.7 |
| 8 | 58.0 | 99.7 | 111.0 | 104.0 |
| 11 | 126.0 | 128.7 | 131.7 | 150.0 |
| 14 | 171.0 | 165.0 | 124.3 | 148.0 |
| 17 | 140.0 | 173.0 | 161.7 | 138.0 |
| 20 | 175.0 | 145.0 | 149.0 | 135.0 |

A useful scientific feature is that the intervention strongly changes the **early trajectory**, but the ranking is not monotonic at later times. For example, the 5 wt.% sample is strongest at 5 and 11 min, while the control is strongest at 14 and 20 min. Accordingly, the database stores the full time axis and does not reduce the source to a statement such as “more microspheres always means stronger adhesion.”

## Material semantics

The source identifies the modifier as **DUALITE E-136-040D**, pre-expanded hollow polymeric microspheres with:

- an adherent particulate calcium-carbonate coating;
- composite density **0.136 g/cm3**;
- particle size about **30–50 um**.

These are stored as material descriptors, not as independent experimental outcomes.

The QR-4668 commercial base adhesive is stored as a material identity only. The patent states that it contains an isocyanate-functionalized polyurethane prepolymer, but it does not disclose the detailed internal QR-4668 recipe in the example section. Missing polyol identities, NCO/OH, free-NCO, and precursor viscosity are therefore not reconstructed.

## Method semantics

### Viscosity

Table I reports viscosity at **121 C** in cps. The example passage does not state spindle, speed, or detailed preconditioning, so Batch 016 does not infer a Brookfield configuration.

### Open time

The adhesive was preheated to **149 C**, applied to room-temperature luwan board, and a tongue depressor was hard-pressed against the adhesive and then pulled off. This protocol is stored separately from Kraft-paper/fiber-tear and other open-time methods in earlier batches.

### Cross peel

Table II reports cross-peel strength in psi at seven explicit post-assembly times. The source passage does not explicitly restate the substrate pair, specimen geometry, or crosshead speed. Those fields remain null instead of being borrowed from other patents or related methods.

## Files

- `batch016_sources.csv`
- `batch016_methods.csv`
- `us20070155859_materials_batch016.csv`
- `us20070155859_formulations_batch016.csv`
- `us20070155859_cross_peel_batch016.csv`
- `us20070155859_controlled_contrasts_batch016.csv`
- `scripts/validate_batch016.py`

## Data-governance decisions

1. The commercial QR-4668 base recipe is **not reverse-engineered** from claims or other sources.
2. No NCO/OH or free-NCO value is assigned because the four-example table does not report one.
3. Microsphere descriptors are separated from formulation-level density outcomes.
4. The 0 wt.% control has no microsphere material ID; 1/3/5 wt.% rows resolve to DUALITE E-136-040D.
5. The complete time-resolved strength trajectory is retained; late-time rank reversals are not hidden by a single headline metric.
6. Open-time method identity is preserved because its absolute values are not directly interchangeable with the other open-time protocols already present in the repository.
7. Patent-family publications are not treated as independent experiments.

## Validation

`validate_batch016.py` checks:

- one source, five methods, two materials;
- four ordered 0/1/3/5 wt.% formulation records;
- exact Table I viscosity/open-time/density values;
- 28 Table II cross-peel records with complete seven-time-point coverage for every example;
- controlled-contrast ratio recomputation;
- material-ID semantics for control versus modified samples;
- absence of invented NCO/OH, free-NCO, or precursor-blend-viscosity fields.

## Database role

Batch 016 complements the chemistry-driven PUR panels with a physically modified controlled series. It is especially useful for multi-objective modeling because it exposes a real trade-off:

`microsphere loading up -> melt viscosity up -> density down -> open time down -> very-early green strength up`

while the later strength ordering changes with time.

For an Agent benchmark, this means that “maximize 5-min strength” and “maximize 20-min strength” are genuinely different decision objectives even within the same four-candidate formulation panel.

## SQLite / README status

Batch 016 remains a staging-layer addition. The cumulative SQLite build is not modified here, so README record-count statistics remain unchanged until a later validated cumulative build actually ingests the staging batches.
