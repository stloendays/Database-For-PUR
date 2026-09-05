# Batch 011 — direct same-temperature polyol-blend → urethane-prepolymer viscosity amplification

## Scope

Batch 011 structures a rare direct precursor/product rheology benchmark from **US8394868B2, “Polyol prepolymers of natural oil based polyols” (Dow)**. Unlike many polyurethane patents that report only the final prepolymer viscosity, this source explicitly reports the viscosity of an unreacted polyol blend and the viscosity of urethane-containing prepolymers made from that blend at the **same 25 °C measurement temperature**.

This is not a PUR hot-melt adhesive example set. It is retained as a **cross-domain mechanistic polyurethane benchmark** for reaction-induced viscosity amplification. It should not be used as an adhesive-performance label source.

## Files

- `batch011_sources.csv` — source registry.
- `batch011_methods.csv` — viscosity and prepolymer-preparation semantics.
- `us8394868_materials_batch011.csv` — source-defined NOPB A, Polyol A, Voranol CP 3008, TDI and polymeric-MDI identities.
- `us8394868_same_temp_amplification_batch011.csv` — five precursor/product viscosity links, with exact-vs-near-match status explicit.
- `us8394868_controlled_index_series_batch011.csv` — exact 50/50 precursor-blend series at TDI indices 30, 33 and 36.
- `scripts/validate_batch011.py` — arithmetic, linkage and evidence-semantics checks.

## Direct same-temperature evidence

### Exact 50/50 blend → TDI prepolymer series

The source reports an unreacted **50/50 wt Voranol CP 3008 / NOPB A blend** viscosity of **710 mPa·s at 25 °C**. The same blend is reacted with Voranate T-80 after 2 min mixing at 2000 rpm and a 70 °C / 6 h oven hold. Reported prepolymer viscosities at 25 °C are:

| Example | TDI index | g TDI / 100 g polyol | η precursor, 25 °C | η prepolymer, 25 °C | amplification |
|---|---:|---:|---:|---:|---:|
| E10 | 30 | 3.38 | 710 mPa·s | 3730 mPa·s | 5.25× |
| E11 | 33 | 3.72 | 710 mPa·s | 4550 mPa·s | 6.41× |
| E12 | 36 | 4.06 | 710 mPa·s | 6500 mPa·s | 9.15× |

This is especially valuable because precursor composition and rheology measurement temperature are held fixed while isocyanate loading/index changes. Within this narrow series, reaction-induced viscosity amplification rises monotonically with index.

### Near-matched TDI vs polymeric-MDI comparison

Table 1 reports an unreacted C1 blend of **80 parts NOPB A / 20 parts Polyol A** with viscosity **2000 mPa·s at 25 °C**. E1 and E2 use **78 parts NOPB A / 20 parts Polyol A / 2 parts isocyanate**, producing 4920 mPa·s with TDI and 4610 mPa·s with polymeric MDI at the same 25 °C.

The database deliberately labels these two links `near_matched_same_temperature`, not exact matches, because the precursor polyol ratio shifts slightly when the source replaces 2 parts NOPB A with 2 parts isocyanate. Their derived ratios (2.46× and 2.305×) are useful supporting evidence but are not pooled with exact-match factors without a match-class control.

## Material-level context

NOPB A is unusually well characterized in the patent: soy-derived, nominal functionality 3, OH number 89 mg KOH/g, hydroxyl equivalent weight 640 g/eq, Mn 2500, Mw 3550, 100% primary hydroxyls, about 70% natural-oil content and viscosity 2700 mPa·s at 21 °C. The patent also notes that NOPB A contains primary hydroxyls whereas Voranol CP 3008 is based on secondary hydroxyls, a mechanistic distinction that may contribute to the index-dependent reaction response.

## Evidence discipline

1. Same-temperature amplification is calculated only where both precursor and product viscosities are explicitly reported at 25 °C.
2. The 50/50 CP 3008/NOPB A series is marked exact because the source explicitly identifies the same precursor blend for the control viscosity and E10-E12.
3. C1→E1/E2 is marked near-matched because 80:20 precursor parts become 78:20 before isocyanate addition; the small composition difference is not ignored.
4. Source-reported `isocyanate index` is preserved as its own field and is not rewritten as NCO/OH without an explicit source conversion.
5. The later statement that index-44 and index-60 prepolymers were “much higher” in viscosity is not entered numerically because no values are reported.
6. Foam performance from later tables is not used here as an adhesive endpoint; Batch 011 is a mechanistic rheology transfer benchmark.

## Database role

Batch 007 established same-temperature **single-polyol → MDI-prepolymer** amplification at 130 °C. Batch 011 adds a different and complementary evidence class: **unreacted polyol blend → urethane-prepolymer** at a matched measurement temperature, including an exact controlled isocyanate-index series. Together they strengthen the evidence that reaction-stage viscosity amplification is not a universal constant and can depend on formulation/reaction variables.

## SQLite / README status

This remains a staging-layer addition. The cumulative SQLite build is not modified in this batch, so README record-count statistics remain unchanged.
