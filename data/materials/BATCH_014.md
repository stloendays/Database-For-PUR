# Batch 014 — MDI-isomer / NCO / residual-monomer / rheology benchmark

## Scope

Batch 014 structures example-level evidence from **US20060020101A1, “Low-viscosity polyurethane prepolymers based on 2,4'-MDI”**. The source is unusually useful because it reports, within one experimental program, explicit MDI isomer identity, polyether chemistry, reaction temperature/time, measured and theoretical NCO, 23 C shear viscosity, residual free monomeric diisocyanate, and standardized downstream sealant mechanics.

The resulting chain is:

`MDI isomer distribution + polyol architecture -> reaction time / measured NCO -> residual monomer + 23 C rheology -> fixed sealant formulation -> cured mechanical response`

This complements the earlier hot-melt batches: Batch 014 is primarily a **reaction-state and rheology control panel**, not a peel/open-time dataset.

## Why this source is high value

The patent defines three high-2,4'-MDI grades (96.93-99.92 wt.% 2,4'-MDI) and a 4,4'-MDI comparator, then prepares several near-matched prepolymer pairs. The source explicitly discusses Examples 1-3 against Comparative Examples 1-3, and Example 4 against Comparative Examples 4-5.

The strongest rheology contrasts retained are:

| contrast | viscosity A @23 C (mPa.s) | viscosity B @23 C (mPa.s) | B/A |
|---|---:|---:|---:|
| E1 high-2,4'-MDI vs C1 4,4'-MDI | 9,740 | 23,600 | 2.423x |
| E2 high-2,4'-MDI vs C2 4,4'-MDI | 9,785 | 23,650 | 2.417x |
| E3 high-2,4'-MDI vs C3 before plasticizer | 14,225 | 38,200 | 2.685x |
| E4 96.93% 2,4'-MDI + DBTL vs C4 4,4'-MDI + DBTL | 4,800 | 96,000 | 20.0x |

These are marked **near-matched**, not perfect single-variable experiments, because reaction times and/or exact batch scale differ.

## Reaction-state fields

The source determines NCO content according to **DIN EN 1242** and residual monomeric diisocyanate by **GPC**. Batch 014 keeps three NCO states distinct where available:

- theoretical NCO,
- constant-NCO reaction plateau,
- final product NCO after any post-reaction addition.

It also preserves censored free-monomer results such as `<0.1 wt.%` using a separate operator field.

Example 6 is especially useful as a staged-reaction case. Its first-stage NCO-functional precursor has viscosity **3,410 mPa.s @23 C**, measured NCO **7.58 wt.%**, and residual monomer **17.6 wt.%**. After a second polyol reaction stage, the final binder reaches **66,500 mPa.s @23 C**, NCO **1.26 wt.%**, and residual monomer **<0.1 wt.%**. The ~19.50x viscosity increase is stored as a **within-example reacted-stage link**, not as an unreacted blend-to-prepolymer amplification pair.

## Standardized downstream mechanics

The same source uses a fixed sealant recipe for downstream testing: Mesamoll, calcium carbonate, the example binder, Desmodur VH20, pyrogenic silica, then additional binder, GLYMO and DBTL catalyst. Membranes are cast at about 2 mm and cured **14 d at room temperature** before Shore A / tensile testing.

This makes Table 2 suitable for linking binder reaction/rheology state to a common downstream formulation. It does **not** make the data directly comparable to peel or lap-shear tests, so no adhesive-strength semantics are assigned.

## Important data-governance decisions

1. **No claim-level ranges are copied into examples.** The claim preference for NCO/OH 1.4-1.9 is not assigned as an example value unless the example itself gives enough explicit information.
2. **Residual monomer is not the same as total NCO.** GPC free-monomer values and DIN EN 1242 NCO values remain separate fields.
3. **Plasticizer state is explicit.** Comparative Example 3 has separate rows before and after Mesamoll addition. The post-Mesamoll value is not used as a clean rheology comparator to unplasticized Example 3.
4. **Censored values remain censored.** `<0.1 wt.%`, `not determined`, `not measurable`, and `>>10^6 mPa.s` are not converted into invented point values.
5. **Manufacturer/source interpretation is not treated as an independent experiment.** The patent authors' discussion is retained only as contextual evidence; numeric rows come from the example tables and example procedures.
6. **Near-matched means near-matched.** Even apparently clean MDI-isomer pairs have different reaction times, so the contrast table records those qualifiers.
7. **Example 6 is not precursor-blend amplification.** Both stage 1 and stage 2 are reacted polyurethane-containing states.

## Files

- `batch014_sources.csv`
- `batch014_methods.csv`
- `us20060020101_materials_batch014.csv`
- `us20060020101_reaction_rheology_batch014.csv`
- `us20060020101_sealant_mechanics_batch014.csv`
- `us20060020101_controlled_contrasts_batch014.csv`
- `scripts/validate_batch014.py`

## Database role

Batch 014 provides a compact benchmark in which **isocyanate positional isomerism, reaction kinetics, free-monomer cleanup, viscosity, and downstream mechanics are simultaneously observable**. This is useful for later multi-objective selection because low viscosity alone is not sufficient: residual monomer and cured mechanical properties impose additional constraints.

## SQLite / README status

Batch 014 remains in the staging layer. The cumulative SQLite build is not modified in this batch, so README record-count statistics must remain unchanged until a later validated cumulative build actually ingests these records.
