# Batch 013 — crystallization-aware staged PUR prepolymer benchmark

## Scope

Batch 013 structures the example data in **US6365700B1, “High green strength reactive hot melt by a prepolymerization in the main reactor”**. This source is valuable because it connects a deliberately staged polyurethane-prepolymer synthesis to **DSC/crystallization kinetics, melt viscosity, uncured mechanical properties, cooling rheology, and thermal melt stability**.

The batch adds a mechanistic chain that was previously sparse in the repository:

`polyester molecular architecture → near-stoichiometric stage-1 urethane formation → crystallization kinetics / DSC → second-stage PURHM formulation → melt rheology / thermal stability → rapid strength-development rationale`

This is complementary to the later multi-objective adhesion batches: Batch 013 does not fabricate peel/open-time values that are not present. Its role is to add the missing **crystallization-aware reaction layer**.

## Files

- `batch013_sources.csv` — source registry.
- `batch013_methods.csv` — stage-1 preparation, DSC, Brookfield, tensile and CARIMED semantics.
- `us6365700_materials_batch013.csv` — seven source-defined materials.
- `us6365700_crystallization_batch013.csv` — Example 1 urethane-prepolymer vs CAPA 640 crystallization/DSC/viscosity comparison.
- `us6365700_tensile_batch013.csv` — uncured-film tensile properties for the same comparator pair.
- `us6365700_staged_reactions_batch013.csv` — Example 2 and Example 3 staged synthesis, water limit, rheology and thermal-stability fields.
- `us6365700_mechanistic_links_batch013.csv` — explicit comparator and stage-to-stage links without mislabeling them as precursor-blend amplification.
- `scripts/validate_batch013.py` — row-count, linkage, qualifier and arithmetic checks.

## Example 1: crystallization-aware comparator

The patent reacts hydroxy-terminated hexanediol adipate **DYNACOLL 7361 (MW 7200)** with 4,4'-MDI at **NCO:OH = 0.9:1** and compares the resulting urethane prepolymer with **CAPA 640 (MW 37,000)**.

Table 1B reports:

| system | time to crystallize at 40 C (min) | cooling crystallization onset (C) | Delta H (mJ/g) | melt peak (C) | viscosity (mPa.s) |
|---|---:|---:|---:|---:|---:|
| DYNACOLL 7361/MDI prepolymer | 1 | 41 | 66.6 | 56.6 | 98,000 |
| CAPA 640 | 6 | 34 | 64.0 | 55 | 164,000 |

The narrative/Fig. 1 separately says approximately **1.5 min** vs **4.5 min** to fully crystallize after cooling to 40 C. Because those values are not identical to the table endpoint, both are retained in separate columns rather than reconciled by assumption.

The same comparison reports uncured-film elastic modulus **273 vs 195 MPa**, yield stress **9.6 vs 14.5 MPa**, and elongation **>800% vs >1000%**. The `>` qualifiers are preserved.

## Example 2: staged high-viscosity PURHM

The first-stage material uses **55 parts DYNACOLL 7361 + 2.0 parts 4,4'-MDI**. The example labels the stage-1 viscosity as **50,000 mPa.s at 120 C**. It then adds **23.8 parts DYNACOLL 7360 + 10.0 parts VORANOL P1010**, vacuum-dries to **water <0.05%**, and reacts with **9.2 parts 4,4'-MDI for 30 min at 140 C**.

The final adhesive is again reported as **50,000 mPa.s at 120 C**, and a 120 C thermal-stability hold produces a **14% viscosity increase after 4 h**. Cooling CARIMED rheology is described qualitatively; no numeric G'/G'' trace is fabricated.

## Example 3: lower-viscosity staged formulation

Example 3 explicitly prepares the first stage from **40 parts DYNACOLL 7361 + 1.0 part 4,4'-MDI**, with **NCO:OH = 0.7:1**, reacted **1 h at 130–150 C**. Its source-labeled stage-1 viscosity is **18,000 mPa.s at 120 C**.

The patent then lists **5 parts DYNACOLL 7360, 10 parts DYNACOLL 7380, 22 parts PPG 1000, and 16.7 parts ISONATE M143** after the first stage and reports a final viscosity of **18,000 mPa.s at 120 C**. Because the example does not explicitly restate a second-stage reaction time or temperature, those fields remain null.

## Evidence discipline

1. **No free-NCO value is invented.** The source gives NCO:OH ratios for the staged chemistry but not example-specific free-NCO assays.
2. **Example-specific temperature labels override normalization.** The method paragraph says Brookfield Thermosel “at 140 C with 1 rpm,” while Examples 2–3 explicitly call their numerical results “at 120 C.” Batch 013 preserves the explicit 120 C labels and records the internal wording inconsistency in method metadata.
3. **Table and figure/narrative crystallization times are separate endpoints.** `1 vs 6 min` and `1.5 vs 4.5 min` are not silently averaged.
4. **CARIMED curves are qualitative only.** G', G'' and tan-delta are not digitized from prose.
5. **Stage-1-to-final viscosity equality is not called blend→prepolymer amplification.** Both states are already reacted polyurethane-containing systems; they are stored as `stage1_to_final` links.
6. **Claim/general-method ranges stay distinct from example data.** The general second-stage NCO:OH range of 1.2:1–3:1 is not assigned to individual examples unless explicitly stated.
7. **Supplier/material identity is source-faithful.** DYNACOLL 7361, 7360, 7380, VORANOL P1010, ISONATE M143 and CAPA 640 are retained as named materials rather than replaced with guessed modern equivalents.

## Database role

Batch 013 fills a mechanistic gap between precursor descriptors and downstream adhesion outcomes. It gives later models/Agents explicit evidence that **crystallization kinetics and melt viscosity can move independently**: the Example 1 urethane prepolymer crystallizes substantially faster than the polycaprolactone comparator while also showing lower melt viscosity. This supports a reaction/crystallization-aware representation rather than treating viscosity alone as a proxy for green-strength development.

## SQLite / README status

This batch remains a staging-layer addition. The cumulative SQLite build is not modified, so README record-count statistics remain unchanged.
