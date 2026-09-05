#!/usr/bin/env python3
from __future__ import annotations
import csv
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data' / 'materials'

def load(name):
    with (DATA/name).open(newline='', encoding='utf-8') as f: return list(csv.DictReader(f))

def num(x): return None if x in ('',None) else float(x)
sources=load('batch009_sources.csv')
forms=load('henkel_us20200216730_formulations_batch009.csv')
perf=load('henkel_us20200216730_performance_batch009.csv')
mats=load('henkel_us20200216730_materials_batch009.csv')
contrasts=load('henkel_us20200216730_controlled_contrasts_batch009.csv')
poly=load('resinate_us20170066950_polyols_batch009.csv')
pre=load('resinate_us20170066950_prepolymers_batch009.csv')
lap=load('resinate_us20170066950_lapshear_batch009.csv')
methods=load('batch009_methods.csv')
source_ids={r['source_id'] for r in sources}
assert source_ids=={'PAT_US20200216730A1','PAT_US20170066950A1'}
for rows in [forms,perf,mats,contrasts,poly,pre,lap,methods]:
    assert all(r['source_id'] in source_ids for r in rows)
assert len(forms)==16 and len({r['record_id'] for r in forms})==16
for r in forms[:15]:
    total=sum(float(r[k]) for k in ['ppg2000_amount','ppg4000_amount','polyester_amount','acrylic_amount','caco3_amount','mdi44_amount'])
    assert abs(total-100)<1e-9 and r['formulation_basis']=='wt_pct'
assert forms[15]['formulation_basis']=='parts_by_weight' and abs(float(forms[15]['reported_total'])-73.2)<1e-9
assert len(perf)==17
for r in perf:
    if r['viscosity_status']=='measured': assert num(r['viscosity_121c_cps']) and num(r['viscosity_121c_cps'])>0
    if r['example_id'] not in ('15','Industrial Control'):
        assert num(r['green_strength_30min_psi']) is not None
form_ids={r['record_id'] for r in forms}
for r in contrasts:
    assert r['baseline_record_id'] in form_ids and r['variant_record_id'] in form_ids
    assert abs((float(r['variant_viscosity_121c_cps'])-float(r['baseline_viscosity_121c_cps']))-float(r['delta_viscosity_cps']))<1e-9
assert len(mats)==14 and {r['material_code'] for r in mats}==set('ABCDEFGHIJKLMN')
assert len(poly)==8 and len(pre)==8
poly_ids={r['record_id'] for r in poly}
for r in pre:
    assert r['polyol_record_id'] in poly_ids
    assert abs(float(r['actual_free_nco_wt_pct'])/float(r['target_free_nco_wt_pct'])-float(r['actual_over_target_ratio']))<1e-5
assert len(lap)==32
assert {r['substrate'] for r in lap}=={'PE','Al','PC','PVC'}
pre_ids={r['record_id'] for r in pre}
for r in lap:
    assert r['prepolymer_record_id'] in pre_ids
    for c in ['stress_1h_psi','stress_24h_psi','stress_168h_psi']:
        assert float(r[c])>0
from collections import Counter
c=Counter(r['prepolymer_record_id'] for r in lap)
assert set(c.values())=={4}
assert all(r['dsc_status']=='not_example_specific' and r['dsc_tc_c']=='' for r in poly)
assert any(r['method_type']=='DSC_crystallization_range' and r['claim_or_example']=='claim_general' for r in methods)
print(f'Batch 009 validation passed: {len(forms)} Henkel formulations, {len(perf)} performance rows, {len(contrasts)} controlled contrasts, {len(poly)} Resinate polyols, {len(pre)} measured-NCO prepolymers, {len(lap)} substrate-resolved lap-shear rows.')
