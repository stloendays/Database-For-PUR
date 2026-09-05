# Batch 006 — Polyol → MDI prepolymer pairs + PURHM formulation/property benchmark

Date: 2026-09-06

## Why this batch exists

Batch 006 adds two data layers that are directly useful for HMPUR formulation research but were still sparse in the repository:

1. **paired precursor → MDI-prepolymer data**, where the same polyol family is linked to reported MDI-prepolymer viscosity at controlled target NCO levels;
2. **worked PUR hot-melt formulation → process/property data**, where blend composition, residual NCO, melt viscosity, open time, early green strength and creep resistance are reported together.

This batch is intentionally committed as a staging layer before it is folded into the cumulative SQLite release. It is source-traceable and does not silently infer missing formulation quantities.

## Source A — Stepan CASE Adhesives Brochure

Official manufacturer brochure:

- 11 polyester-polyol grades;
- raw-polyol descriptors including backbone, viscosity, viscosity temperature, molecular weight, OH value and Tg/Tm where reported;
- each grade linked to 4,4'-MDI prepolymer data at **10 wt.%** and **15 wt.% target NCO**;
- prepolymer viscosity reported at **25 °C**;
- 22 precursor/prepolymer pair rows in total;
- 17 PURHM grade-selection records with normalized application/performance tags.

Files:

- `prepolymer_pair_benchmarks_batch006.csv`
- `material_application_claims_batch006.csv`

### Important interpretation rule

The polyol viscosity and the prepolymer viscosity are often reported at **different temperatures**. Therefore these records are valid as paired chemistry/process evidence, but a direct numerical viscosity-amplification ratio must **not** be computed without temperature normalization.

The paired table is useful for studying how polyol backbone, OH value, molecular weight and target NCO jointly affect prepolymer rheology.

## Source B — US20060205909A1

Patent: **Polyester polyols for polyurethane adhesives**.

Batch 006 extracts the worked experimental region around Tables 6–9.

### Polyol property anchors

Three patent-developed PA/DDDA polyester polyols plus a commercial HDA polyester anchor are structured with:

- polyol composition;
- OH value;
- acid value;
- moisture;
- viscosity and measurement temperature where reported.

File:

- `patent_polyol_properties_batch006.csv`

### Five PURHM formulations

The patent reports five PUR reactive-hot-melt formulations with coupled outputs:

- polyol-blend ratio;
- residual NCO;
- melt viscosity at 120 °C;
- appearance;
- viscosity stability at 120 °C;
- open time;
- green strength at 1, 3 and 6 min;
- creep resistance initially and after 3 min.

File:

- `patent_purhm_benchmark_batch006.csv`

Selected values:

| Formulation | Polyol blend | NCO wt.% | Viscosity @120 °C | Open time | Green strength @6 min |
|---|---|---:|---:|---:|---:|
| F1 | Polyol B only | 2.94 | 9,300 cP | >10 min | 5.9 psi |
| F2 | HDA / Polyol B / PD-56 = 50/25/25 | 2.13 | 10,480 cP | 1.5 min | 110.3 psi |
| F3 | HDA / Polyol C = 50/50 | 2.98 | 7,020 cP | 2 min | 93.9 psi |
| F4 | HDA / Polyol D = 50/50 | 2.12 | 5,820 cP | 0.5 min | 24.5 psi |
| F5 | HDA / Polyol B = 50/50 | 2.69 | 6,300 cP | 1.5 min | 20.6 psi |

This is useful because it exposes the engineering trade-off between **melt viscosity / open time / rapid green-strength development**, rather than treating a formulation as a single scalar target.

## Evidence discipline

- Manufacturer claims are tagged as manufacturer-reported product-selection evidence, not independent performance validation.
- Patent values are stored as reported experimental values.
- Exact MDI mass for the Table 7 five-formulation set is not reported and is **not inferred**.
- Polyol-blend ratios are preserved as blend-basis ratios rather than mislabeled as total adhesive wt.%.
- `<4.5 %/h` viscosity stability is preserved as a censored/qualified value, not converted to 4.5 as an exact measurement.
- One Stepan 10% NCO prepolymer is reported as `solid`; it remains categorical rather than being assigned an artificial viscosity.

## Files added

- `batch006_sources.csv`
- `prepolymer_pair_benchmarks_batch006.csv`
- `material_application_claims_batch006.csv`
- `patent_polyol_properties_batch006.csv`
- `patent_purhm_benchmark_batch006.csv`
- `BATCH_006.md`

## Next integration step

The next cumulative database build should normalize these staging tables into the relational schema, with particular attention to:

1. a dedicated precursor/prepolymer pair entity or reproducible view;
2. censored measurements such as `<4.5 %/h`;
3. application-claim provenance distinct from measured properties;
4. paired blend-viscosity / prepolymer-viscosity measurements at matched temperatures when new sources become available.
