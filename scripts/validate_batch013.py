from pathlib import Path
import csv
ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'data/materials'

def read(name):
    with open(D/name,newline='',encoding='utf-8') as f:
        return list(csv.DictReader(f))

sources=read('batch013_sources.csv')
methods=read('batch013_methods.csv')
mats=read('us6365700_materials_batch013.csv')
cryst=read('us6365700_crystallization_batch013.csv')
tens=read('us6365700_tensile_batch013.csv')
stages=read('us6365700_staged_reactions_batch013.csv')
links=read('us6365700_mechanistic_links_batch013.csv')

assert len(sources)==1 and sources[0]['publication_number']=='US6365700B1'
assert len(methods)==5
assert len(mats)==7
assert len(cryst)==2 and {r['sample_id'] for r in cryst}=={'SAMPLE1','CAPA640'}
assert len(tens)==2 and {r['sample_id'] for r in tens}=={'SAMPLE1','CAPA640'}
assert len(stages)==2 and {r['sample_id'] for r in stages}=={'EX2','EX3'}
assert len(links)==4

c={r['sample_id']:r for r in cryst}
assert float(c['SAMPLE1']['table_time_to_crystallize_min'])==1
assert float(c['CAPA640']['table_time_to_crystallize_min'])==6
assert float(c['SAMPLE1']['cooling_crystallization_onset_c'])==41
assert float(c['CAPA640']['cooling_crystallization_onset_c'])==34
assert float(c['SAMPLE1']['viscosity_mpas'])==98000
assert float(c['CAPA640']['viscosity_mpas'])==164000
assert abs(98000/164000-0.5975609756)<1e-9

s={r['sample_id']:r for r in stages}
assert float(s['EX2']['stage1_viscosity_mpas'])==50000 and float(s['EX2']['final_viscosity_mpas'])==50000
assert float(s['EX2']['thermal_stability_viscosity_increase_pct'])==14
assert s['EX2']['water_before_second_reaction_operator']=='<' and float(s['EX2']['water_before_second_reaction_wt_pct'])==0.05
assert float(s['EX3']['stage1_nco_oh_ratio'])==0.7
assert s['EX3']['stage1_reaction_temperature_c']=='130-150'
assert float(s['EX3']['stage1_reaction_time_min'])==60
assert float(s['EX3']['final_viscosity_mpas'])==18000

for r in cryst:
    assert r['viscosity_method_id']=='US6365700_VISC'
    assert r['dsc_method_id']=='US6365700_DSC'
for r in tens:
    assert r['tensile_method_id']=='US6365700_TENSILE'
for r in stages:
    assert r['viscosity_method_id']=='US6365700_VISC'

print('Batch 013 validation passed:',len(mats),'materials,',len(cryst),'crystallization rows,',len(tens),'tensile rows,',len(stages),'staged-reaction rows,',len(links),'mechanistic links')
