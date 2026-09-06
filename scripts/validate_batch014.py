from pathlib import Path
import csv

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / 'data' / 'materials'


def read(name):
    with open(D / name, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

sources = read('batch014_sources.csv')
methods = read('batch014_methods.csv')
materials = read('us20060020101_materials_batch014.csv')
rheo = read('us20060020101_reaction_rheology_batch014.csv')
mech = read('us20060020101_sealant_mechanics_batch014.csv')
contrasts = read('us20060020101_controlled_contrasts_batch014.csv')

assert len(sources) == 1
assert sources[0]['publication_number'] == 'US20060020101A1'
assert len(methods) == 5
assert len(materials) == 10
assert len(rheo) == 16
assert len(mech) == 11
assert len(contrasts) == 6

r = {x['sample_id']: x for x in rheo}
for sid in ['E1','E2','E3','E4','E5','E6_STAGE1','E6_STAGE2','C1','C2','C3_PRE','C3_POST','C4','C5','C6','C7','C8']:
    assert sid in r

# Source-table anchors.
assert float(r['E1']['viscosity_mpas']) == 9740
assert float(r['C1']['viscosity_mpas']) == 23600
assert float(r['E4']['viscosity_mpas']) == 4800
assert float(r['C4']['viscosity_mpas']) == 96000
assert r['E5']['free_monomer_operator'] == '<' and float(r['E5']['free_monomer_wt_pct']) == 0.1
assert r['E6_STAGE2']['free_monomer_operator'] == '<'
assert r['C3_PRE']['free_monomer_operator'] == 'not_determined'
assert r['C6']['viscosity_mpas'] == ''

# NCO-state semantics.
assert float(r['E1']['nco_plateau_wt_pct']) == 2.51
assert float(r['E1']['nco_theoretical_wt_pct']) == 2.56
assert float(r['E1']['end_product_nco_wt_pct']) == 2.52
assert float(r['E6_STAGE1']['nco_plateau_wt_pct']) == 7.58
assert float(r['E6_STAGE2']['end_product_nco_wt_pct']) == 1.26

# Every numeric viscosity is explicitly tied to 23 C and the same method.
for row in rheo:
    if row['viscosity_mpas']:
        assert float(row['viscosity_temperature_c']) == 23
        assert row['viscosity_method_id'] == 'US20060020101_VISC23'
    assert row['nco_method_id'] == 'US20060020101_NCO'
    assert row['free_monomer_method_id'] == 'US20060020101_MONOMER'

# Mechanical rows must point to a reaction/rheology binder state.
for row in mech:
    assert row['binder_sample_id'] in r
    assert float(row['cure_time_days']) == 14
    assert row['mechanical_method_id'] == 'US20060020101_MECH'
    assert row['specimen_prep_method_id'] == 'US20060020101_SEALANT_PREP'

m = {x['sample_id']: x for x in mech}
assert float(m['MECH_E3']['breaking_elongation_pct']) == 646
assert float(m['MECH_C7']['breaking_elongation_pct']) == 21
assert m['MECH_C7']['stress_100_n_mm2'] == ''

# Recompute stored contrast ratios.
for c in contrasts:
    a = float(c['metric_a'])
    b = float(c['metric_b'])
    stored = float(c['ratio_b_over_a'])
    assert abs((b / a) - stored) < 5e-5, (c['contrast_id'], b / a, stored)

# Explicitly protect the strongest same-family contrasts.
cs = {x['contrast_id']: x for x in contrasts}
assert abs(float(cs['MDI_ISOMER_E1_C1']['ratio_b_over_a']) - 23600/9740) < 5e-5
assert abs(float(cs['MDI_ISOMER_E2_C2']['ratio_b_over_a']) - 23650/9785) < 5e-5
assert abs(float(cs['MDI_ISOMER_E3_C3PRE']['ratio_b_over_a']) - 38200/14225) < 5e-5
assert float(cs['LOW_INDEX_E4_C4']['ratio_b_over_a']) == 20.0

print('Batch 014 validation passed:', len(materials), 'materials,', len(rheo), 'reaction/rheology states,', len(mech), 'mechanical rows,', len(contrasts), 'contrasts')
