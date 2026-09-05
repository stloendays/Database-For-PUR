from pathlib import Path
import csv, math
ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'data'/'materials'

def rows(name):
    with (D/name).open(encoding='utf-8',newline='') as f:
        return list(csv.DictReader(f))

f=rows('us20030022973_formulations_batch010.csv')
p=rows('us20030022973_uncured_properties_batch010.csv')
d=rows('us20030022973_dynamic_peel_batch010.csv')
l=rows('us20030022973_lapshear_batch010.csv')
c=rows('us20030022973_controlled_contrasts_batch010.csv')
assert len(f)==13 and len({r['sample_id'] for r in f})==13
ids={r['sample_id'] for r in f}
assert {r['sample_id'] for r in p}==ids
assert {r['sample_id'] for r in d}==ids
assert {r['sample_id'] for r in l}==ids
assert all(r['formulation_basis']=='parts_by_weight' for r in f)
# verify reported-part totals without forcing 100 wt% closure
for r in f:
    calc=sum(float(r[k]) for k in ['ppg2025_parts','ppg4025_parts','dynacoll7360_parts','elvacite2016_parts','dmdee_parts','mdi_parts','tackifier_parts'])
    assert math.isclose(calc,float(r['total_reported_parts']),abs_tol=1e-9)
expected={'4A':99.2,'5A':99.2,'6A':99.2,'7A':99.2,'4B':118.7,'5B':118.7,'6B':118.7,'7B':118.7,'10A':125.7,'10B':125.7,'10C':95.4,'10D':95.4,'10E':70.1}
for r in f:
    assert math.isclose(float(r['total_reported_parts']),expected[r['sample_id']],abs_tol=1e-9)
# explicit NCO/rheology values must be positive; open time may be missing only for Table 11
for r in p:
    assert float(r['reported_nco_pct'])>0 and float(r['melt_viscosity_cps'])>0
    if r['sample_id'].startswith('10'):
        assert r['open_time_min']==''
    else:
        assert float(r['open_time_min'])>0
# preserve explicit zeros separately from missing dynamic-peel dashes
by={r['sample_id']:r for r in d}
assert by['4A']['mm_min_at_30c']=='0' and by['4B']['mm_min_at_30c']=='0'
assert by['10C']['mm_min_at_55c']=='' and by['10D']['mm_min_at_50c']=='' and by['10E']['mm_min_at_30c']==''
# lap-shear completeness and positivity
for r in l:
    for k in ['lap_shear_30min_psi','lap_shear_2h_psi','lap_shear_4h_psi','lap_shear_24h_psi']:
        assert float(r[k])>0
# ten controlled contrasts, including four Dynacoll addition pairs
assert len(c)==10
props={r['sample_id']:r for r in p}
for r in c:
    a,b=r['sample_a'],r['sample_b']
    ratio=float(props[b]['melt_viscosity_cps'])/float(props[a]['melt_viscosity_cps'])
    assert math.isclose(ratio,float(r['viscosity_b_over_a']),rel_tol=2e-5)
for n in '4567':
    ra=next(r for r in f if r['sample_id']==n+'A')
    rb=next(r for r in f if r['sample_id']==n+'B')
    assert float(ra['dynacoll7360_parts'])==0.0 and float(rb['dynacoll7360_parts'])==19.5
    for k in ['ppg2025_parts','ppg4025_parts','elvacite2016_parts','dmdee_parts','mdi_parts','tackifier_identity','tackifier_parts']:
        assert ra[k]==rb[k]
print('batch010 validation passed: 13 formulations, 13 property rows, 13 peel rows, 13 lap-shear rows, 10 controlled contrasts')
