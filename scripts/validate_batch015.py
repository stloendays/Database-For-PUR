from pathlib import Path
import csv
ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'data/materials'

def read(name):
    with open(D/name,newline='',encoding='utf-8') as f:
        return list(csv.DictReader(f))

sources=read('batch015_sources.csv')
methods=read('batch015_methods.csv')
mats=read('us6136136_materials_batch015.csv')
forms=read('us6136136_novel_formulations_batch015.csv')
overlap=read('us6136136_family_overlap_batch015.csv')
series=read('us6136136_controlled_series_batch015.csv')

assert len(sources)==1 and sources[0]['publication_number']=='US6136136A'
assert len(methods)==4
assert len(mats)==9
assert len(forms)==19
assert len(overlap)==17
assert len(series)==4
assert len({r['record_id'] for r in forms})==19
assert all(r['source_id']=='PAT_US6136136A' for r in forms+overlap+series)

# Explicit family deduplication: no repeated Examples 8-18, 21, or 22 are imported.
labels={r['example_label'] for r in forms}
for n in range(8,19):
    assert f'Example {n}' not in labels
assert not any(x.startswith('Example 21') or x.startswith('Example 22') for x in labels)
expected_existing={
'HENKEL_US5599895_EX1','HENKEL_US5599895_EX2','HENKEL_US5599895_EX3','HENKEL_US5599895_EX4','HENKEL_US5599895_EX5',
'HENKEL_US5599895_EX6','HENKEL_US5599895_EX7','HENKEL_US5599895_EX8','HENKEL_US5599895_EX9','HENKEL_US5599895_EX10','HENKEL_US5599895_EX11',
'HENKEL_US5599895_EX12A','HENKEL_US5599895_EX12B','HENKEL_US5599895_EX12C','HENKEL_US5599895_EX12D','HENKEL_US5599895_EX12E','HENKEL_US5599895_EX13'}
assert {r['existing_record_id'] for r in overlap}==expected_existing
assert all(r['action']=='do_not_duplicate' for r in overlap)

# wt% panels must close exactly to 100 as reported.
component_cols=['polyester_a','polyester_b','polyester_e','polyester_f','polyester_g','polyester_h','ppg425','tackifier_beta_pinene','mdi44']
for r in forms:
    if r['basis']=='wt_pct':
        total=sum(float(r[c]) for c in component_cols if r[c] != '')
        assert abs(total-100.0)<1e-8, (r['record_id'], total)
        assert float(r['reported_total'])==100.0

# Example 19 source-designed trajectory.
ex19=[r for r in forms if r['series_role']=='ppg_fraction_comparable_viscosity_series']
assert len(ex19)==6
assert [float(r['ppg425']) for r in ex19]==[9.2,16.0,19.6,25.4,35.5,57.1]
assert [float(r['nco_oh_ratio']) for r in ex19]==[1.7,1.5,1.4,1.3,1.25,1.25]
assert [float(r['viscosity_130c_pa_s']) for r in ex19]==[27,42,38,54,35,60]
assert [float(r['green_strength_min_pli']) for r in ex19]==[1.6,2.5,6.5,10,17,15]

# Example 20 identity screen and clean G/H contrast.
ex20={r['example_label']:r for r in forms if r['series_role']=='polyester_identity_screen'}
assert len(ex20)==6
for r in ex20.values():
    assert r['basis']=='parts_g'
    assert float(r['ppg425'])==200
    polyester_mass=sum(float(r[c]) for c in ['polyester_a','polyester_b','polyester_e','polyester_f','polyester_g','polyester_h'] if r[c] != '')
    assert polyester_mass==200
assert float(ex20['Example 20 E']['mdi44'])==170
assert float(ex20['Example 20 F']['mdi44'])==170
assert float(ex20['Example 20 E']['nco_oh_ratio'])==1.4
assert float(ex20['Example 20 F']['nco_oh_ratio'])==1.4
assert float(ex20['Example 20 E']['viscosity_130c_pa_s'])==125
assert float(ex20['Example 20 F']['viscosity_130c_pa_s'])==185
assert float(ex20['Example 20 E']['green_strength_min_pli'])==25
assert float(ex20['Example 20 F']['green_strength_min_pli'])==45

# Time-resolved early panel semantics.
for r in forms[:7]:
    assert r['green_strength_time_min']=='5'
    assert r['test_speed_in_min']=='0.5'
    assert r['test_substrate']=='SBR/man-made shoe-upper material'
assert forms[2]['mature_strength_min_pli']=='' and forms[3]['mature_strength_min_pli']==''

print('Batch 015 validation passed:',len(mats),'materials,',len(forms),'novel formulations,',len(overlap),'family-overlap mappings,',len(series),'controlled-series records')
