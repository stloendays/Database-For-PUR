from pathlib import Path
import csv

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / 'data' / 'materials'


def read(name):
    with open(D / name, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

sources = read('batch016_sources.csv')
methods = read('batch016_methods.csv')
materials = read('us20070155859_materials_batch016.csv')
forms = read('us20070155859_formulations_batch016.csv')
peel = read('us20070155859_cross_peel_batch016.csv')
contrasts = read('us20070155859_controlled_contrasts_batch016.csv')

assert len(sources) == 1 and sources[0]['publication_number'] == 'US20070155859A1'
assert len(methods) == 5
assert len(materials) == 2
assert len(forms) == 4
assert len(peel) == 28
assert len(contrasts) == 3

expected_ids = [f'US20070155859_EX{i}' for i in range(1, 5)]
assert [r['sample_id'] for r in forms] == expected_ids
assert [float(r['reported_microsphere_wt_pct']) for r in forms] == [0.0, 1.0, 3.0, 5.0]
assert [float(r['viscosity_cps']) for r in forms] == [12750.0, 20000.0, 32000.0, 48000.0]
assert [float(r['open_time_min']) for r in forms] == [5.5, 3.5, 2.5, 2.0]
assert [float(r['density_g_ml']) for r in forms] == [1.06, 0.96, 0.89, 0.82]
assert all(float(r['viscosity_temperature_c']) == 121.0 for r in forms)

# The control has no microsphere material; modified examples all use the reported DUALITE grade.
assert forms[0]['microsphere_material_id'] == ''
assert all(r['microsphere_material_id'] == 'US20070155859_DUALITE_E136040D' for r in forms[1:])

expected_times = [0, 5, 8, 11, 14, 17, 20]
expected_peel = {
    'US20070155859_EX1': [0, 33.7, 58, 126, 171, 140, 175],
    'US20070155859_EX2': [0, 45, 99.7, 128.7, 165, 173, 145],
    'US20070155859_EX3': [0, 79, 111, 131.7, 124.3, 161.7, 149],
    'US20070155859_EX4': [0, 83.7, 104, 150, 148, 138, 135],
}
for sid in expected_ids:
    rows = [r for r in peel if r['sample_id'] == sid]
    assert [int(r['time_after_assembly_min']) for r in rows] == expected_times
    assert [float(r['cross_peel_strength_psi']) for r in rows] == expected_peel[sid]
    assert all(r['method_id'] == 'US20070155859_CROSSPEEL' for r in rows)

f = {r['sample_id']: r for r in forms}
p5 = {
    r['sample_id']: float(r['cross_peel_strength_psi'])
    for r in peel if r['time_after_assembly_min'] == '5'
}
for c in contrasts:
    a = c['control_sample']
    b = c['modified_sample']
    assert a == 'US20070155859_EX1'
    assert abs(float(c['viscosity_ratio_vs_control']) - float(f[b]['viscosity_cps']) / float(f[a]['viscosity_cps'])) < 1e-9
    assert abs(float(c['open_time_ratio_vs_control']) - float(f[b]['open_time_min']) / float(f[a]['open_time_min'])) < 1e-9
    assert abs(float(c['density_ratio_vs_control']) - float(f[b]['density_g_ml']) / float(f[a]['density_g_ml'])) < 1e-9
    assert abs(float(c['cross_peel_5min_ratio_vs_control']) - p5[b] / p5[a]) < 1e-9

# Data-governance guards: no invented NCO/OH, free-NCO, or undisclosed QR-4668 recipe fields exist in this batch.
form_headers = set(forms[0])
assert 'nco_oh_ratio' not in form_headers
assert 'free_nco_wt_pct' not in form_headers
assert 'polyol_blend_viscosity' not in form_headers

print('Batch 016 validation passed:', len(materials), 'materials,', len(forms), 'formulations,', len(peel), 'cross-peel rows,', len(contrasts), 'controlled contrasts')
