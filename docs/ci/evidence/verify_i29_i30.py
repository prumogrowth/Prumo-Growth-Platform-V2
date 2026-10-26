import json,re,sys
from datetime import datetime
from pathlib import Path
root=Path(__file__).resolve().parents[3]
inv=json.loads((root/'docs/ci/CI_S1_I29_I30_SCENARIO_MAP_20261025.json').read_text())
runs=json.loads(Path(sys.argv[1]).read_text())
def stamp(s): return datetime.fromisoformat(s.replace('Z','+00:00')).timestamp()
def unit_ids(lines):
 return [m.group(2) if m.group(2).endswith('.'+m.group(1)) else m.group(2)+'.'+m.group(1) for line in lines if (m:=re.match(r'^(test_\S+) \(([^)]+)\) .*ok$',line))]
expected_ids={i for v in inv['units'].values() for i in v['test_ids']}
expected_markers={i for v in inv['e2e'].values() for i in v['scenarios']}
groups={'controls':[r for r in runs if 'CONTROL' in r['name']], 'parallel':[r for r in runs if 'parallel' in r['name']], 'serial':[r for r in runs if 'serial' in r['name']]}
summary={}
for mode,rs in groups.items():
 assert rs and all(r['conclusion']=='success' for r in rs),mode
 jobs=[j for r in rs for j in r['jobs']];assert all(j['conclusion']=='success' for j in jobs),mode
 lines=[l for j in jobs for l in j['test_evidence']]
 ids=unit_ids(lines);assert set(ids)==expected_ids,(mode,'unit IDs',len(ids),len(set(ids)),expected_ids-set(ids))
 if mode in ['parallel','serial']: assert len(ids)==108,(mode,'unit duplicates')
 if mode=='controls': assert len(ids)==201,(mode,'control count')
 markers=[l for l in lines if l.startswith('PASS S1')]
 if mode!='parallel':
  masked_expected={s.replace('Bearer independente','***') if re.match(r'^PASS S1(?:PERSIST|AUTHORITY)-36:',s) else s for s in expected_markers}
  assert set(markers)==masked_expected and len(markers)==225,(mode,'scenarios')
 else:
  for gate,count in [('I29',105),('I30',120)]: assert f'PASS EXP E2E {gate}: {count} exact scenario markers' in lines
 duration=sum(stamp(j['completed_at'])-stamp(j['started_at']) for j in jobs)
 summary[mode]={'run_ids':[r['id'] for r in rs],'jobs':len(jobs),'runner_seconds':int(duration),'job_span_seconds':int(max(stamp(j['completed_at']) for j in jobs)-min(stamp(j['started_at']) for j in jobs)),'feedback_from_created_seconds':int(max(stamp(j['completed_at']) for j in jobs)-min(stamp(r['created_at']) for r in rs)),'unit_executions':len(ids),'unique_unit_ids':len(set(ids)),'e2e_scenarios':225,'scenario_proof':'validated exact markers in each runner; artifact reference available' if mode=='parallel' else '225 scenario IDs; 223 exact descriptions and 2 descriptions normalized for GitHub masking of Bearer independente'}
assert len({r['head_sha'] for r in runs})==1
print(json.dumps({'sha':runs[0]['head_sha'],'summary':summary},indent=2))
