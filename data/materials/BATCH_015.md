# Batch 015 — family-deduplicated green-strength formulation panels

## Scope

Batch 015 extends the Henkel PUR hot-melt evidence base with **US6136136A, “Moisture-curable polyurethane hotmelt adhesives with high green strength”** (Roland Heider). This source belongs to the same US patent family as **US5599895A**, which was already structured in Batch 008.

The central data-governance decision in this batch is therefore **family-level deduplication** rather than naive source-level counting.

US6136136A repeats 17 formulation records already represented in Batch 008:

- US6136136 Examples 8–18 correspond to Batch 008 / US5599895A Examples 1–11;
- US6136136 Example 21 A–E corresponds to Batch 008 Example 12 A–E;
- US6136136 Example 22 corresponds to Batch 008 Example 13.

Those repeated rows are **not imported again**. They are recorded in `us6136136_family_overlap_batch015.csv` with `action=do_not_duplicate`.

Batch 015 imports only the non-duplicate experimental panels:

- **Examples 1–7:** seven formulations linking PPG/polyester composition and NCO:OH to temperature-resolved viscosity, 5-min peel/green strength, and selected 3-day peel strength;
- **Example 19 A–F:** a six-point PPG-fraction / comparable-viscosity design with 130 C viscosity and green strength;
- **Example 20 A–F:** a six-member polyester-identity screen with fixed PPG mass, near-fixed MDI/NCO:OH, 130 C viscosity, and NBR/NBR green strength.

The resulting new evidence chain is:

`polyester identity / PPG fraction + NCO:OH -> PUR reaction under common protocol -> melt rheology -> early green peel -> selected mature peel`

## Files

- `batch015_sources.csv` — source and patent-family metadata.
- `batch015_methods.csv` — common reaction, Brookfield viscosity, general peel, and NBR/NBR green-strength protocols.
- `us6136136_materials_batch015.csv` — source-defined polyester/PPG/MDI/tackifier descriptors used by the novel panels.
- `us6136136_novel_formulations_batch015.csv` — 19 non-duplicate formulation/property records.
- `us6136136_family_overlap_batch015.csv` — 17 explicit mappings to existing Batch 008 records.
- `us6136136_controlled_series_batch015.csv` — four predeclared controlled or designed-series relationships.
- `scripts/validate_batch015.py` — staging validation, composition closure, family deduplication and series checks.

## High-value series

### Example 19: PPG fraction under a deliberately comparable-viscosity design

The source varies PPG 425 from **9.2 to 57.1 wt%**, while Polyester A falls from **73.8 wt% to 0**. MDI and NCO:OH are deliberately co-adjusted; the patent explicitly says the NCO:OH ratio was calculated to provide a similar viscosity range and make the results comparable, rather than to optimize each formulation.

| member | PPG 425 (wt%) | Polyester A (wt%) | MDI (wt%) | NCO:OH | eta130 (Pa.s) | green strength (pli) |
|---|---:|---:|---:|---:|---:|---:|
| A | 9.2 | 73.8 | 17.0 | 1.7 | 27 | 1.6 |
| B | 16.0 | 63.9 | 20.1 | 1.5 | 42 | 2.5 |
| C | 19.6 | 58.8 | 21.6 | 1.4 | 38 | 6.5 |
| D | 25.4 | 50.8 | 23.8 | 1.3 | 54 | 10 |
| E | 35.5 | 35.5 | 29.0 | 1.25 | 35 | 17 |
| F | 57.1 | 0 | 42.9 | 1.25 | 60 | 15 |

This is a **designed multi-variable trajectory**, not a strict single-variable causal experiment. That distinction is encoded in the series metadata.

### Example 20: polyester identity screen

Example 20 uses **200 g PPG 425 + 200 g of one polyester** and then MDI. This provides substantially cleaner chemistry contrasts than most patent formulation tables.

The strongest pair is Example 20 E vs F:

- PPG 425 = 200 g in both;
- polyester = 200 g in both;
- MDI = 170 g in both;
- NCO:OH = 1.4:1 in both;
- same NBR/NBR green-strength protocol;
- only the reported polyester identity changes from **Polyester G** to **Polyester H**.

Outcomes:

- eta130: **125 -> 185 Pa.s**;
- green strength: **25 -> 45 pli**.

The source describes G as **very weakly crystalline** and H as **weakly crystalline**, with Tg values of about -23 C and -12 C and distinct high-temperature melt-viscosity ranges. This pair therefore provides a useful controlled structure/crystallinity -> rheology -> green-strength link.

Two additional near-controlled pairs are retained:

- Polyester A vs B: 74 vs 42 Pa.s and 24 vs 10 pli, with MDI 171 vs 173 g and NCO:OH fixed at 1.3:1;
- Polyester E vs F: 34 vs 18 Pa.s and 22 vs 4 pli, with MDI 172 vs 173 g and NCO:OH fixed at 1.3:1.

## Examples 1–7: time-resolved early/mature peel panel

Examples 1–7 add a seven-formulation panel under the common source preparation protocol. The tables report formulation wt%, NCO:OH, viscosity at one or more of 90/110/130/150/170 C, and **5-min SBR/man-made peel strength at 0.5 in/min**. Examples 1, 2 and 5–7 also provide explicit 3-day peel ranges.

The extracted table does not unambiguously assign 3-day values to Examples 3–4, so those mature-strength cells are left null rather than inferred.

## Source methods and evidence semantics

The source states that the polyester/PPG mixture, optionally with beta-pinene resin, is dehydrated under vacuum for about 60 min at **110–130 C**, cooled to about **90 C**, then reacted with 4,4'-MDI under vacuum for about 60 min at **110–130 C**.

Viscosity is measured with a **Brookfield Thermocell** after heating the sample tube for 15 min at the stated temperature.

For the general peel method, primed SBR and shoe-upper material are bonded and tested on an Instron. Examples 1–7 explicitly identify SBR/man-made material and 0.5 in/min. Example 19 reports green strength at 0.5 in/min but does not restate substrate or elapsed aging time; those fields therefore remain null.

Example 20 explicitly uses **NBR/NBR strips**, preheated to **80–100 C**, adhesive applied at about **180 C**, pressed at about **100 psi for about 1 min**, and tested at **5 in/min**. The source does not provide a separate post-assembly waiting time for the Example 20 green-strength number, so no elapsed-time value is invented.

## Data-governance decisions

1. **Patent-family duplicates are not new experiments.** The 17 repeated US6136136 rows are mapped to Batch 008 and excluded from the novel-formulation table.
2. **Units are source-faithful.** Batch 015 retains strength in `pli`; it does not overwrite the source with converted kg/cm values.
3. **No precursor-blend viscosity is fabricated.** The source gives the reaction protocol and product viscosities but not viscosity of the complete unreacted blend immediately before MDI addition.
4. **No free-NCO assay is invented.** Example tables report NCO:OH design ratios, not example-specific measured free-NCO values.
5. **Example 19 is non-orthogonal by design.** PPG fraction, polyester fraction, MDI and NCO:OH co-vary; the panel is useful for multi-objective modeling but should not be interpreted as a pure PPG causal sweep.
6. **Missing mature-strength cells remain missing.** Ambiguous table spacing is not resolved by guesswork.
7. **Material descriptors and formulation outcomes remain distinct.** Supplier/source material Tg or melt-viscosity descriptors are not treated as independent formulation experiments.

## Validation

`validate_batch015.py` checks:

- one registered source, four methods, nine material definitions;
- exactly **19 novel formulation rows**;
- exactly **17 family-overlap mappings** to Batch 008 IDs;
- no imported Example 8–18 / 21 / 22 duplicate labels;
- exact 100 wt% closure for the wt%-basis panels;
- Example 19 PPG/NCO:OH/viscosity/green-strength sequences against the source table;
- Example 20 200 g PPG + 200 g polyester mass structure;
- the exact Example 20 E/F controlled-pair conditions;
- explicit 5-min / 0.5 in/min semantics for Examples 1–7.

The validator was run before commit and passed.

## SQLite / README status

Batch 015 remains a staging-layer addition. The cumulative SQLite build is not modified in this batch, so README record-count statistics remain unchanged until a later cumulative rebuild actually ingests and validates these records.
