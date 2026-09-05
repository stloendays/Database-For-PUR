# Batch 009 — reaction-aware PUR hot-melt benchmarks: controlled polyester substitution, measured free NCO, green strength and lap shear

## Scope

Batch 009 adds two complementary patent series that strengthen the database along the chain **composition → reaction state → rheology → early bond formation → cured mechanical/adhesive performance**.

1. **US20200216730A1 / Henkel** provides a 16-example reactive-hot-melt formulation series in which Examples 1-15 use the same generic PPG/acrylic/CaCO3/4,4'-MDI recipe and primarily change the polyester identity. The patent reports theoretical NCO, viscosity at 121 C, open time, green strength at 5-30 min, and selected cured storage-modulus/tensile properties.
2. **US20170066950A1 / Resinate Materials Group** provides two controlled semi-crystalline polyester series based on recycled PET or recycled bisphenol-A polycarbonate. Eight polyester polyols are converted to MDI prepolymers under a shared protocol; critically, the source reports both **target and actually titrated free NCO**. The resulting adhesives are tested by ASTM D1002 lap shear on PE, aluminum, polycarbonate and PVC at 1 h, 24 h and 7 days.

These sources are kept analytically distinct. Henkel is a controlled formulation/performance benchmark; Resinate is a composition → measured reaction-state → time-resolved adhesion benchmark.

## Files

- `batch009_sources.csv` — source registry.
- `batch009_methods.csv` — example protocols and claim/general DSC semantics.
- `henkel_us20200216730_materials_batch009.csv` — polyester A-N identities, chemistry and reported Mn/OH descriptors.
- `henkel_us20200216730_formulations_batch009.csv` — Examples 1-16 with explicit formulation basis and reaction conditions.
- `henkel_us20200216730_performance_batch009.csv` — theoretical NCO, 121 C viscosity, open time, 5-30 min green strength and selected cured properties.
- `henkel_us20200216730_controlled_contrasts_batch009.csv` — five predeclared polyester-substitution contrasts.
- `resinate_us20170066950_polyols_batch009.csv` — eight recycled-PET / recycled-PC semi-crystalline polyester preparations and OH values.
- `resinate_us20170066950_prepolymers_batch009.csv` — eight MDI prepolymers with target and measured free NCO plus common reaction conditions.
- `resinate_us20170066950_lapshear_batch009.csv` — 32 substrate-resolved lap-shear rows with 1 h, 24 h and 7 day outcomes.
- `scripts/validate_batch009.py` — cross-file integrity and evidence-semantics checks.

## Henkel controlled formulation series

### Common chemistry for Examples 1-15

The reported generic formulation is:

- PPG2000 / PPG4000 = 1:1 by weight, total 29.0 wt%
- polyester polyol = 14.5 wt%
- acrylic polymer = 20.5 wt%
- CaCO3 = 25 wt%
- 4,4'-MDI = 11 wt%

All ingredients except MDI are heated and dehydrated under vacuum at about 110-130 C for 60 min. MDI is then added and the mixture is reacted at 130 C for 75 min. Example 14 changes the acrylic grade from Elvacite 2016 to Elvacite 4014; Example 16 is a filler-free formulation reported in **parts by weight**, not normalized wt%, and the file preserves that basis explicitly.

Viscosity is reported from a Brookfield DV-I+ viscometer with #27 spindle at 121 C. Open time is measured by dispensing 0.8 g at 121 C and recording the time at which adhesive no longer transfers to a wooden tongue depressor as the adhesive cools toward 23 C. Green strength is measured on hardwood cross-peeler specimens at 5, 10, 15, 20, 25 and 30 min.

### High-value polyester substitutions

Because the generic formulation is held fixed, several pairs isolate polyester identity particularly well.

- **A → B, Examples 1 → 2:** theoretical NCO remains 2.43 wt%; viscosity changes 10,875 → 12,950 cP, open time changes from about 3 min to <30 s, and 30-min green strength changes 158 → 135 psi.
- **C → K, Examples 3 → 11:** theoretical NCO remains 2.43 wt%; viscosity changes 12,650 → 13,500 cP while open time remains about 8 min and 30-min green strength changes 139 → 148 psi.
- **C → M, Examples 3 → 13:** theoretical NCO remains 2.43 wt%; viscosity is similar (12,650 vs 12,250 cP) and open time is about 8 min in both, yet 30-min green strength differs strongly (139 vs 46 psi). This is an especially useful example of rheology/open-time similarity not implying early-strength similarity.
- **C → I, Examples 3 → 9:** the polyester changes from BD/AA to polycaprolactone; open time remains about 8 min and 30-min green strength is similar, while theoretical NCO changes slightly (2.43 → 2.47 wt%). This pair is therefore classified `medium_high`, not fully controlled.

The Henkel series also contains examples with long open times but low early strength, and a phase-separating high-Mn polyester control. It therefore supports multi-objective benchmarking rather than a single-property ranking.

## Resinate measured-free-NCO series

### Controlled precursor chemistry

The patent prepares two related semi-crystalline polyester series:

- recycled PET series: 0, 5, 10 and 15 wt% PET;
- recycled bisphenol-A polycarbonate series: 0, 5, 10 and 15 wt% PC.

The polyester chemistry is based principally on 1,3-propanediol and azelaic acid. Example OH values range from 18.4 to 58.6 mg KOH/g.

### Shared MDI prepolymer protocol

The polyester polyol is held at 80 C under nitrogen for 0.5 h. After benzoyl peroxide addition and 5 min mixing, MDI is added in one portion and the exotherm is controlled at or below about 90 C. After the mixture falls to about 75 C, it is heated to 115 C for 1 h. Free NCO is then measured by excess di-n-butylamine/back-titration according to ASTM D-1638-74. Only after this measurement are 1.0 wt% 3-aminopropyltriethoxysilane and 500 ppm DBTDL added.

The eight target → measured free-NCO pairs are retained exactly. Examples include:

- PET 5%: 2.50 → 2.09 wt%
- PET 10%: 3.50 → 2.03 wt%
- PET 15%: 3.50 → 1.74 wt%
- PC 5%: 3.00 → 1.20 wt%
- PC 10%: 3.00 → 1.65 wt%
- PC 15%: 3.00 → 1.48 wt%

This is important because the database now contains a directly observed reaction-state variable rather than only nominal stoichiometry.

### Time-resolved adhesion

The MDI prepolymers are evaluated on polyethylene, aluminum, polycarbonate and PVC. Lap shear is measured after 1 h, 24 h and 7 days of conditioning at 25 C / 50% RH using ASTM D1002, 12 in/min, with triplicate specimens. The patent explicitly interprets the 1 h result as an indicator of green strength.

Batch 009 preserves both peak stress and failure mode (`AF`, `CF`, `SF`) for every reported example/substrate/time point. This yields 32 substrate rows, each carrying 1 h, 24 h and 7 day outcomes and allows analysis of not only strength magnitude but also transitions in failure mechanism during moisture cure.

## DSC / crystallization semantics

US20170066950A1 discusses semi-crystalline polyester polyols and discloses DSC crystallization-temperature ranges such as -20 to 35 C measured at 10 C/min. These are **general/claim-level ranges**, not Example 1-8 measured Tc values. Accordingly:

- individual polyol rows leave `dsc_tc_c` blank;
- `dsc_status` is `not_example_specific`;
- the DSC range and method are stored only in `batch009_methods.csv` with `claim_or_example = claim_general`.

This prevents claim ranges from leaking into the example-level ground truth.

## Evidence discipline

Batch 009 follows these rules:

1. no unreported polyol-blend viscosity is inferred;
2. theoretical NCO from the Henkel table is not relabeled as measured free NCO;
3. Resinate target NCO and measured titrated NCO are separate fields;
4. qualifiers such as `~`, `<30 s`, `<1 min` and `phase separation` are preserved rather than coerced into exact values;
5. Example 16 Henkel amounts remain `parts_by_weight` and are not silently normalized to wt%;
6. DSC ranges remain claim/general evidence and are not assigned to individual examples;
7. industrial-control performance is retained without inventing an undisclosed formulation recipe.

## Validation policy

`validate_batch009.py` checks:

- source registration and cross-file links;
- 16 unique Henkel formulation records;
- 100 wt% closure for Examples 1-15 and explicit `parts_by_weight` semantics for Example 16;
- positive measured viscosities and expected performance coverage;
- arithmetic in the five Henkel controlled contrasts;
- all 14 Henkel polyester material codes A-N;
- eight Resinate polyol/prepolymer links and exact recomputation of measured/target NCO ratios;
- exactly 32 lap-shear rows = 8 prepolymers × 4 substrates, with three cure-time columns per row;
- positive lap-shear values and valid prepolymer references;
- separation of general DSC claims from example-level data.

Local validation passes before staging to the repository.

## Database role

Batch 009 advances the database in two directions that are directly useful for later modeling and agent evaluation:

- **multi-objective formulation selection:** polyester identity → theoretical NCO → viscosity/open time → time-resolved green strength → cured modulus/tensile properties;
- **reaction-aware evidence:** precursor composition/OH → target NCO → actually measured free NCO → substrate- and cure-time-dependent lap shear.

The second direction is particularly valuable because it creates explicit labels for the gap between nominal formulation design and achieved reaction state.

## SQLite / README status

This is a staging-layer addition. The cumulative SQLite build is not modified in this batch, so README record-count statistics remain unchanged.
