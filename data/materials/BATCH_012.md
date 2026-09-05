# Batch 012 — low-temperature PURHM composition → measured NCO → rheology → green/cured peel benchmark

## Scope

Batch 012 structures the example tables of **US12319850B2, “Polyurethane hot melt adhesive for low temperature application” (Henkel)**. The source is unusually valuable for decision-oriented PUR datasets because it joins explicit wt% formulations with **titration-measured %NCO**, **Brookfield viscosity at 80 °C**, and **90° peel after 5 min and 24 h** on two board substrates bonded to vinyl foil.

The batch therefore adds a coherent chain:

`composition → reaction-state label (%NCO) → melt rheology → 5-min green strength → 24-h cured adhesion`

## Files

- `batch012_sources.csv` — source registry.
- `batch012_methods.csv` — preparation, viscosity, NCO titration, peel and open-time method semantics.
- `us12319850_materials_batch012.csv` — source-defined polyester/polyether/isocyanate/TPU/additive descriptors.
- `us12319850_formulations_batch012.csv` — 3 comparative formulations plus 8 main examples.
- `us12319850_peel_batch012.csv` — 44 substrate/time-resolved peel outcomes.
- `us12319850_controlled_contrasts_batch012.csv` — five near-controlled ablation/composition contrasts.
- `scripts/validate_batch012.py` — closure, linkage, outcome-semantics and contrast checks.

## Methods retained from source

- Example viscosity: Brookfield viscometer, spindle 28, 10 rpm, **80 °C**.
- `% NCO`: **conventional titration**. It is stored as source-labeled measured `%NCO`; no NCO/OH ratio is inferred.
- Bond strength: **90° peel at room temperature, 6 in/min**.
- Aging: **5 min = short-term/green strength**; **24 h = long-term/cured strength**.
- Bond construction: adhesive coated at about **95 °C**; vinyl foil receives 2–3 gsf and board 4–5 gsf; specimens are 1 × 5 in.
- Open time: source defines a 5 mil Kraft-paper/fiber-tear method, but the example tables do not report numeric open-time values. Accordingly, the method is registered but no example-specific open-time labels are invented.

The disclosed general preparation protocol mixes and vacuum-dehydrates polyols/polymers/resins, adds f=2 diisocyanate under vacuum at about 120–140 °C, reacts about 1 h or until desired viscosity/NCO, then optionally adds f>2 polyisocyanate/catalyst/additives and mixes under vacuum another 30–60 min.

## Main E1–E8 panel

The eight main examples span measured `%NCO = 3.7–4.0 wt%` and `η80 = 8,000–18,000 cps`. Five-minute numeric peel values, where measured, range from 0.6–2.6 psi on Lauan→vinyl and 0.2–1.2 psi on Azdel→vinyl. Twenty-four-hour outcomes mix numeric peel values with substrate-failure codes; those failure codes are retained as censored categorical outcomes rather than converted into artificial numbers.

### Near-controlled f>2 polyisocyanate / TPU ablation panel

E4–E7 all report a 1:1 amorphous:crystalline polyester ratio and closely related backbones, but differ in whether polymeric MDI (`f>2`) and Pearlbond 521 TPU are present:

| sample | f>2 pMDI | TPU | η80 (cps) | Lauan 5 min (psi) | Azdel 5 min (psi) |
|---|---:|---:|---:|---:|---:|
| E4 | yes | yes | 13,000 | 2.0 | 0.8 |
| E5 | yes | no | 10,000 | 1.1 | 0.5 |
| E6 | no | yes | 13,000 | 1.1 | 0.4 |
| E7 | no | no | 11,000 | 0.6 | 0.2 |

The patent itself interprets E4 as showing improved strength when f=2 diisocyanate, f>2 polyisocyanate and TPU are used together. The database records these as **near-controlled ablations**, not exact single-variable experiments, because the wt% recipes are retuned slightly across E4–E7.

### Acrylic-resin addition contrast

E8 adds 3 wt% Elvacite 2013 to a formulation close to E4 while retaining pMDI and TPU. It reports η80 = 16,000 cps, Lauan 5-min peel = 2.6 psi and Azdel 5-min peel = 1.2 psi. This is stored as a near-controlled acrylic-addition contrast rather than an exact intervention because several component percentages shift slightly.

## Comparative C1–C3 panel

The comparative samples have η80 = 13,000–15,000 cps and measured `%NCO = 2.6–2.9`, but their 5-min outcomes are `poor` or `no adhesion`, while their 24-h outcomes reach substrate-failure categories. This is useful evidence that acceptable melt viscosity and strong ultimate adhesion do not guarantee useful early green strength.

C3 is also a deliberate data-quality case: the listed wt% components sum to **95.05 wt%**, not 100. The database preserves that non-closure and does not invent the missing 4.95 wt%.

## Evidence discipline

1. `measured_nco_wt_pct` means exactly the source-labeled `%NCO` measured by titration. It is not rewritten as free-NCO or NCO/OH unless the source says so.
2. Example rheology uses the source table’s **80 °C** measurement, not broader claim-level 95 °C viscosity limits.
3. `I-SF`, `SF`, and `D-SF` are preserved as failure-mode-censored outcomes and never assigned arbitrary numeric peel strengths.
4. `nm` remains not-measured; it is not zero.
5. `poor` and `no adhesion` remain qualitative labels.
6. The 0.6 wt% additive bundle is kept as a bundle because the source gives only Thermoplast Blue >0.1 wt%, Resiflow LF 0.4 wt%, and A-Link 25 <0.1 wt%, not an exact complete split.
7. Comparative C3 non-closure is retained rather than normalized or backfilled.
8. Open-time methodology is registered, but no example-specific value is created because none is reported in the example tables.

## Database role

Batch 012 adds a particularly useful **multi-objective formulation benchmark** for later blind-selection/Agent work: candidates can have similar viscosity and NCO yet substantially different 5-min green strength and different 24-h failure modes. It complements Batch 011’s direct precursor→prepolymer amplification evidence by adding downstream decision labels on realistic PURHM formulations.

## SQLite / README status

This batch remains a staging-layer addition. The cumulative SQLite build is not modified, so README record-count statistics remain unchanged.
