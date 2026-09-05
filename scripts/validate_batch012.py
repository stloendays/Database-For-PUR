from pathlib import Path
import csv
ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'data/materials'

def read(name):
    with open(D/name,newline='',encoding='utf-8') as f: return list(csv.DictReader(f))

sources=read('batch012_sources.csv'); methods=read('batch012_methods.csv'); mats=read('us12319850_materials_batch012.csv'); forms=read('us12319850_formulations_batch012.csv'); peel=read('us12319850_peel_batch012.csv'); cons=read('us12319850_controlled_contrasts_batch012.csv')
assert len(sources)==1 and sources[0]['publication_number']=='US12319850B2'
assert len(methods)==5
assert len(mats)==16
assert len(forms)==11
assert len(peel)==44
assert len(cons)==5
ids={r['sample_id'] for r in forms}
assert ids=={'C1','C2','C3','E1','E2','E3','E4','E5','E6','E7','E8'}
comp=[c for c in forms[0] if c.endswith('_wt_pct') and c not in ('measured_nco_wt_pct','total_reported_wt_pct')]
for r in forms:
    calc=sum(float(r[c]) for c in comp)
    assert abs(calc-float(r['total_reported_wt_pct']))<0.011, (r['sample_id'],calc,r['total_reported_wt_pct'])
    assert r['nco_method_id']=='US12319850_NCO_TITRATION'
    assert r['viscosity_method_id']=='US12319850_VISC_80C' and float(r['viscosity_temperature_c'])==80
c3=next(r for r in forms if r['sample_id']=='C3')
assert abs(float(c3['total_reported_wt_pct'])-95.05)<1e-6
for r in forms:
    if r['sample_id'].startswith('E'):
        assert 3.7 <= float(r['measured_nco_wt_pct']) <= 4.0
        assert 8000 <= float(r['viscosity_cps']) <= 18000
assert len({(r['sample_id'],r['board_substrate'],r['age_value'],r['age_unit']) for r in peel})==44
for r in peel:
    assert r['sample_id'] in ids
    typ=r['outcome_type']
    if typ=='numeric':
        assert r['peel_strength_psi']!='' and float(r['peel_strength_psi'])>=0 and r['failure_mode']==''
    elif typ=='failure_mode_censored':
        assert r['failure_mode'] in {'I-SF','SF','D-SF'} and r['peel_strength_psi']==''
    elif typ=='not_measured':
        assert r['outcome_text']=='nm' and r['peel_strength_psi']==''
    elif typ=='qualitative':
        assert r['outcome_text'] in {'poor','no adhesion'} and r['peel_strength_psi']==''
    else: raise AssertionError(typ)
lookup={(r['sample_id'],r['board_substrate'].split()[0],r['age_value'],r['age_unit']):r for r in peel}
expect={'E4':(2.0,0.8),'E5':(1.1,0.5),'E6':(1.1,0.4),'E7':(0.6,0.2),'E8':(2.6,1.2)}
for s,(la,az) in expect.items():
    assert abs(float(lookup[(s,'Lauan','5','min')]['peel_strength_psi'])-la)<1e-9
    assert abs(float(lookup[(s,'Azdel','5','min')]['peel_strength_psi'])-az)<1e-9
fmap={r['sample_id']:r for r in forms}
for c in cons:
    assert c['sample_a'] in fmap and c['sample_b'] in fmap
    ratio=float(fmap[c['sample_b']]['viscosity_cps'])/float(fmap[c['sample_a']]['viscosity_cps'])
    assert abs(ratio-float(c['viscosity_ratio_b_over_a']))<1e-5
print('Batch 012 validation passed:',len(mats),'materials,',len(forms),'formulations,',len(peel),'peel outcomes,',len(cons),'contrasts')
