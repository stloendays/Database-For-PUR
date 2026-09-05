# Batch 007 — Matched-temperature rheology + controlled polyester/prepolymer benchmarks

Date: 2026-09-06

## Why this batch exists

Batch 007 focuses on the data gap that matters most for testing the current HMPUR hypothesis:

> Does a modest precursor-level rheology/composition difference become systematically amplified after reaction with MDI, and is the amplification itself chemistry-dependent?

The batch separates three evidence classes that must not be conflated:

1. **same-temperature precursor → prepolymer viscosity pairs**, where a numerical amplification factor can be computed directly;
2. **cross-temperature precursor/prepolymer tables**, useful for chemistry/property mapping but not for direct amplification ratios;
3. **controlled composition → prepolymer/property series**, useful for causal structure-property analysis even when precursor viscosity is not reported.

---

## 1. Same-temperature Evonik benchmark at 130 °C

The strongest directly usable layer in the current database is the DYNACOLL controlled RHM dataset.

For selected polyester polyols, both the raw-polyol viscosity and the corresponding 4,4'-MDI reaction-product viscosity are reported at **130 °C** in the same manufacturer source version. The reaction-product condition is OH:NCO = **1:2.2**.

File:

- `evonik_matched_130c_amplification_batch007.csv`

Ten exact same-temperature pairs are currently retained:

| Grade | Raw polyol η130 (Pa·s) | MDI prepolymer η130 (Pa·s) | ηpre / ηpolyol |
|---|---:|---:|---:|
| DYNACOLL 7110 | 1.0 | 3 | 3.00× |
| DYNACOLL 7111 | 3.0 | 13 | 4.33× |
| DYNACOLL 7130 | 10 | 45 | 4.50× |
| DYNACOLL 7131 | 10 | 50 | 5.00× |
| DYNACOLL 7140 | 50 | 700 | 14.00× |
| DYNACOLL 7150 | 60 | 400 | 6.67× |
| DYNACOLL 7330 | 0.3 | 3 | 10.00× |
| DYNACOLL 7320 | 4 | 48 | 12.00× |
| DYNACOLL 7340 | 1 | 12 | 12.00× |
| DYNACOLL 7390 | 0.7 | 4 | 5.71× |

The median factor across these ten rows is approximately **6.19×**.

### Interpretation

This does **not** by itself prove a general mixing-law failure, because these are single-grade polyester polyols rather than controlled polyol blends. It does, however, provide a direct empirical anchor that reaction with MDI can magnify melt-viscosity differences by a chemistry-dependent factor even at the same measurement temperature.

The factor is not constant: the retained same-temperature values range from **3× to 14×** under a common nominal OH:NCO condition. That non-constant response is exactly the behavior a future blend-level experiment should test more rigorously.

---

## 2. Source-version audit: DYNACOLL 7320

The database now explicitly records a manufacturer-source version discrepancy instead of silently overwriting it.

File:

- `evonik_source_version_audit_batch007.csv`

For DYNACOLL 7320:

- 2024 product-range brochure: reaction-product viscosity @130 °C = **48 Pa·s**;
- 2025 grade TDS: reaction-product viscosity @130 °C = **30 Pa·s**.

The raw polyol viscosity remains 4 Pa·s in the current grade TDS.

This is a **37.5% relative difference** between the two reported reaction-product values. Both records are therefore treated as versioned manufacturer evidence rather than one being silently substituted for the other.

---

## 3. Stepan PURHM typical-property matrix

Batch 006 already added Stepan grade/application claims and a separate 10/15 wt.% target-NCO prepolymer table. Batch 007 adds the richer PURHM property matrix from the same official brochure.

File:

- `stepan_purhm_typical_properties_batch007.csv`

The table preserves, where reported:

- polyol backbone;
- raw-polyol viscosity and measurement temperature;
- average molecular weight;
- OH value;
- Tg or Tm;
- precursor basis;
- 4,4'-MDI target NCO;
- prepolymer viscosity at 120 and 130 °C;
- open time;
- set time;
- tensile strength;
- elongation at break.

### Critical semantics

For some rows the named grade is used **alone** as the polyol precursor. For other rows, the named grade is used at **25 wt.% in a polyol blend with STEPANPOL PC-205P-30**. Those two cases are explicitly distinguished in `precursor_basis`.

Also, the raw-polyol viscosity and final prepolymer viscosity are generally measured at different temperatures. Therefore `same_temperature_pair = 0` for these rows and no amplification factor is calculated.

---

## 4. Controlled 35/25/40 polyol-blend patent series

US20100105831A1 / EP2167600 provides a particularly useful controlled series because the first two polyester components and their fractions are fixed:

- DYNACOLL 7130: **35 parts**;
- DYNACOLL 7230: **25 parts**;
- variable third hydroxyl polyester: **40 parts**;
- total polyol basis: **100 parts**;
- 4,4'-MDI at OH:NCO = **1:2.2**;
- drying: **130 °C**;
- reaction: **130 °C for 45 min**.

Files:

- `patent_polyester_structure_batch007.csv`
- `patent_rhm_structure_property_batch007.csv`

Nine third-polyester structures are linked to:

- prepolymer viscosity @130 °C;
- softening point;
- bond strength on aluminium;
- bond strength on ABS;
- bond strength on polyamide;
- bond strength on PMMA.

Because the 35/25/40 formulation framework and nominal reaction condition are held constant, this dataset is useful for isolating the effect of the **identity/structure of the third polyester component**.

---

## 5. Crystalline polyester → MDI prepolymer dataset

US20070129523A1 contributes a separate chemistry-to-processing benchmark.

File:

- `patent_crystalline_prepolymer_batch007.csv`

Eleven row-linked examples preserve:

- DDA / AA / TPA acid composition;
- DDL / HD diol composition;
- hydroxyl value;
- number-average molecular weight;
- polyol melting point;
- crystallization temperature and enthalpy;
- 4,4'-MDI stoichiometry;
- reaction temperature/time;
- prepolymer viscosity;
- prepolymer thermal transitions;
- setting time;
- Shore D hardness;
- working-efficiency classification.

Where the patent reports that a prepolymer partially solidified at 120 °C and therefore had to be measured at **140 °C**, that temperature is preserved explicitly. Those rows must not be compared directly with 120 °C viscosity rows without normalization.

---

## Evidence rules added in Batch 007

1. A numerical viscosity amplification factor is permitted only when precursor and prepolymer viscosities are reported at the **same temperature** and are linked to the same chemistry/source version.
2. Cross-temperature pairs remain useful evidence but are explicitly flagged as non-direct-amplification rows.
3. Named-grade viscosity is not treated as polyol-blend viscosity when the grade is only one component of a blend.
4. Manufacturer-source revisions are versioned; conflicting values are retained and audited rather than overwritten.
5. Patent-controlled comparison series preserve the exact fixed/variable formulation logic.
6. Temperature shifts caused by partial solidification are retained as experimental semantics, not normalized away silently.

---

## Files added

- `batch007_sources.csv`
- `evonik_matched_130c_amplification_batch007.csv`
- `evonik_source_version_audit_batch007.csv`
- `stepan_purhm_typical_properties_batch007.csv`
- `patent_polyester_structure_batch007.csv`
- `patent_rhm_structure_property_batch007.csv`
- `patent_crystalline_prepolymer_batch007.csv`
- `BATCH_007.md`

## Scientific consequence

Batch 007 gives the project its first explicit **same-temperature reaction amplification benchmark**. The current directly defensible statement is:

> Within a manufacturer-controlled polyester-polyol → 4,4'-MDI dataset measured at 130 °C, the ratio ηprepolymer / ηpolyol is strongly non-constant across chemistry, spanning roughly 3×–14× in the retained source version.

This supports designing a dedicated blend experiment, but it does not replace one. The next high-value data target remains a true **polyol-blend viscosity @T → prepolymer viscosity @T** paired series in which blend composition is varied systematically and measured before reaction.
