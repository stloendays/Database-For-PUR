# Batch 017 — experimental viscosity measurability constraints

## Scope

Batch 017 records an experimental feasibility finding from the current PPG2000/PDP-70 common-material validation plan. The laboratory reported that the selected low-viscosity raw materials, and their pre-MDI blend, fall below the lower useful range of the available viscometer. This is not stored as a fabricated viscosity value and is not treated as a failed experiment.

The key workflow change is:

`candidate formulation -> instrument-window feasibility gate -> quantitative measurement if measurable; otherwise censored/out-of-range observation + method adaptation`

## Scientific interpretation

For ordinary polyol liquids, viscosity decreases as temperature increases. Therefore, if the pre-MDI blend is already below the available viscometer range at a lower temperature, moving directly to 80-120 C cannot rescue measurability on the same instrument; it will generally make the sample even less viscous.

The original formulation should not be modified by adding a third raw material solely to make the viscometer return a number. Such an intervention changes the formulation identity and therefore changes the hypothesis being tested.

## Database semantics

The file `batch017_experimental_measurability_constraints.csv` stores three explicit records:

1. A provisional qualitative `below_instrument_lower_range` observation for the current pre-MDI PPG2000/PDP-70 system.
2. A prospective pre-MDI measurability gate requiring temperature points to lie inside the calibrated instrument window.
3. A corresponding post-MDI gate. The planned 80-120 C window remains usable only when the NCO-terminated prepolymer is measurable with the selected geometry/instrument.

No numerical viscosity value is inferred from the operator report.

## Required metadata before quantitative ingestion

The following fields must be captured before the below-range observation can be converted into a quantitative interval or censoring bound:

- exact viscometer/rheometer model;
- geometry or spindle;
- rotational speed / shear condition;
- numerical lower reliable torque or viscosity limit;
- sample temperature at the failed measurement;
- exact blend identity and composition;
- sample volume and conditioning history where relevant.

Until these are known, the observation remains qualitative/provisional.

## Workflow action

For the current validation experiment:

- **pre-MDI:** perform a short measurability screen first. Use a low-viscosity adapter, cone-plate rheometer, capillary method, or another validated geometry if the existing viscometer cannot resolve the sample. A lower-temperature measurement window is acceptable only if it remains liquid and scientifically relevant.
- **post-MDI:** keep the high-temperature rheology plan as the main process-relevant measurement, but confirm the instrument window before fixing the full 80/90/100/110/120 C sequence.
- **data handling:** values below the measurement floor are stored as left-censored/out-of-range observations, not as zero and not as ordinary missing values.

## Agent / inverse-design implication

Instrument measurability becomes part of the experimental feasibility layer. The Agent may optimize chemistry and process targets, but any prospective experimental recommendation must also pass a measurement-feasibility gate before being sent to the laboratory.

This does **not** mean that experimentally unmeasurable formulations are chemically infeasible. It means that the available measurement method is infeasible for that formulation/condition pair. The distinction must remain explicit in the evidence model.

## Current status

This batch adds staging-layer constraints only. It does not alter historical literature observations, frozen PUR_SIM_V1 values, or primary Agent benchmark results.
