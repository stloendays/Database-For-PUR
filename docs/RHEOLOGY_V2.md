# PUR-RHEOLOGY V2

This derived layer turns the normalized PUR database into a source-traceable rheology science layer while keeping raw published values unchanged.

## Evidence hierarchy

1. **Direct source values** — raw Pugar viscosity points and patent point values.
2. **Within-range derived quantities** — per-formulation fits, 45/75 °C interpolations, matched-family slopes and crossover estimates lying within the joint source range.
3. **Extrapolated projections** — e.g. Pugar-derived 120 °C values; retained only as projections and never described as direct measurements.
4. **Synthetic design benchmark** — `PUR_SIM_V1`; used only for deterministic inverse-design logic and prospective target freezing.

## Current quantitative findings

- 39 Pugar prepolymers / 4559 direct points. Simple Arrhenius median R² = 0.9967; a Tg-shifted coordinate raises the median to 0.9997, improves 38/39 samples and cuts median ln-viscosity RMSE by 65.3%.
- In 11 high-quality chemistry families, +1 wt%-point free NCO lowers fitted viscosity at both 45 and 75 °C; median multipliers are 0.709 and 0.736. Median dEa/dNCO = -0.81 kJ mol⁻¹ per wt%-point.
- Matched C/P contrast compresses from median 8.85 at 45 °C to 4.63 at 75 °C; median low-temperature amplification = 1.91×.
- Rankings at 45 and 75 °C remain globally similar (Spearman 0.959; Kendall 0.871), yet 43/666 formulation pairs invert. Six of twelve matched D/P pairs have fitted crossovers inside their joint ~40–80 °C source range.
- US5932680A directly confirms a temperature-induced ranking reversal: Example 1 vs Example 4 is 190 vs 98 Pa·s at 90 °C but 55 vs 60 Pa·s at 110 °C.
- US5932680A Examples 5–8 show a composition-context effect: high-A/low-A ratio = 1.654 in a C/D-balanced background and 1.091 in a D-rich background; ratio-of-ratios = 1.516. This is an effect-size statement only because replicate variance is not reported.

## Design-state upgrade

The old eta80 + eta120 + eta80/eta120 objective triple-counts a two-degree-of-freedom temperature response. The new `PUR-RHEOLOGY-STATE V1` uses two independent normalized coordinates: eta120 and thermal sensitivity (eta80/eta120, equivalently an apparent-Ea coordinate), while eta80 remains a hard processing-window gate.

On the frozen 928-candidate `PUR_SIM_V1` benchmark, the property-state optimum is WO_INV_0419 (PPG700/PPG1000 = 50/50, NCO/OH = 1.7), but its MDI fraction is 34.06%, below the frozen 35% floor. Backward analysis gives a continuous feasibility threshold of NCO/OH = 1.77198, so the first reachable 0.1-grid state is NCO/OH = 1.8, WO_INV_0420. `PUR_SIM_V1` remains synthetic benchmark truth, not experimental evidence.

## Strict robustness reachability audit

The written strict robust gate was re-evaluated on the complete response table using the **actual lower/upper intervals for each response**, including the compounded interval for η80/η120. The result is not a robust winner: it is an **unreachable robust target**.

- Nominal-feasible candidates: **117**.
- Strict robust-feasible candidates: **0**.
- Closest candidate by relaxing preferred-window half-width: `WO_INV_0359`, requiring a **1.486×** half-width, i.e. **+48.56%**.
- Best candidate under a uniform uncertainty-shrink thought experiment: `WO_INV_0374`, still requiring at least a **34.40%** reduction in uncertainty.
- Prospective target `WO_INV_0420` would require about a **41.27%** uncertainty reduction; its limiting coordinate is the **viscosity ratio / thermal-sensitivity interval**.

This audit is algorithmic and belongs to `PUR_SIM_V1`. It is not a statement about physical experimental uncertainty. The key decision rule is: **when the strict robust set is empty, report the reachability gap rather than assigning an artificial L2 winner.**
