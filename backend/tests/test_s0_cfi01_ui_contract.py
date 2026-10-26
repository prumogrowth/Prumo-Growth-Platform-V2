"""Candidate wire compatibility; no endpoint, authentication or execution claim."""
import copy
from dataclasses import replace
import importlib.util
import hashlib
import json
from pathlib import Path
import subprocess
import unittest

from backend.s0_cfi01_ui_contract import (
    COMMAND_SCHEMA,RESULT_SCHEMA,CAPTURE,RECHECK,MAX_COMMAND_BYTES,InvalidCandidate,
    parse_command,load_command,request_fingerprint,compare_retry,prepare_physical_capture,
    candidate_response,stage_response,
)
from backend.s0_human_closure_event_local import ClosureRequest,_valid

ROOT=Path(__file__).resolve().parents[2]
LAB=ROOT/'integration/ui_cfi01'
VECTORS=json.loads((LAB/'golden_vectors.json').read_text())['vectors']
U='00000000-0000-4000-8000-000000000001'
V='00000000-0000-4000-8000-000000000002'
W='00000000-0000-4000-8000-000000000003'


def command():
    return copy.deepcopy(VECTORS[0]['command'])


def probe(cases):
    out=subprocess.run(['node',str(LAB/'probe.mjs')],input=json.dumps(cases),
        capture_output=True,text=True,check=True,timeout=10)
    return json.loads(out.stdout)


def stage(response,c,context=U):
    return stage_response(response,c,sent_context=U,current_context=context)


class WireCandidateTests(unittest.TestCase):
    def test_01_shared_vectors_python_browser_reference_and_golden_digest(self):
        js=probe([dict(operation='command',command=v['command']) for v in VECTORS])
        for v,j in zip(VECTORS,js):
            with self.subTest(vector=v['name']):
                self.assertEqual(j['valid'],v['valid'])
                if not v['valid']:
                    with self.assertRaises(InvalidCandidate):parse_command(v['command'])
                    continue
                c=parse_command(v['command'])
                self.assertEqual(c.to_wire(),j['command'])
                self.assertEqual(request_fingerprint(c),v['fingerprint'])
                self.assertEqual(j['fingerprint'],v['fingerprint'])
                self.assertEqual(prepare_physical_capture(c).state,v['prepare_state'])

    def test_02_raw_json_rejects_duplicate_decoded_keys_and_non_json(self):
        text=json.dumps(command(),separators=(',',':'))
        bad=[text[:-1]+',"command":"capture_human_closure"}',
             text[:-1]+',"comm\\u0061nd":"capture_human_closure"}',
             text.replace('"kind":"cycle"','"kind":"case","kind":"cycle"'),
             text.replace('"value":"7"','"value":NaN'),
             '['+text+']','{}','null','\ufeff'+text]
        for value in bad:
            with self.subTest(value=value[-30:]),self.assertRaises(InvalidCandidate):
                load_command(value.encode('utf-8'))
        for raw in (b'\xff',b' '* (MAX_COMMAND_BYTES+1),b'',text):
            with self.assertRaises(InvalidCandidate):load_command(raw)
        self.assertEqual(load_command(text.encode()).to_wire(),command())

    def test_03_case_never_becomes_cycle_and_recheck_never_mints_binding(self):
        for n,state in ((2,'CASE_VERSION_BINDING_REQUIRED'),(3,'RECHECK_SERVER_BINDING_REQUIRED')):
            prepared=prepare_physical_capture(VECTORS[n]['command'])
            self.assertEqual(prepared.state,state);self.assertIsNone(prepared.request)

    def test_04_explicit_physical_cycle_preserves_full_int64_and_actual_validator(self):
        for n in (0,1):
            wire=VECTORS[n]['command'];p=prepare_physical_capture(wire).request.to_physical_payload()
            self.assertEqual(set(p),{'case_ref','expected_cycle_version','idempotency_key'})
            self.assertEqual(p['expected_cycle_version'],int(wire['expected_version']['value']))
            self.assertTrue(_valid(ClosureRequest(**p)))
        with self.assertRaises(ValueError):prepare_physical_capture(VECTORS[1]['command']).request.to_js_payload()

    def test_05_dto_revalidation_immutable_snapshot_and_fixed_errors(self):
        raw=command();c=parse_command(raw);raw['expected_version']['value']='8'
        self.assertEqual(c.version_value,'7')
        with self.assertRaisesRegex(InvalidCandidate,'^INVALID_CFI01_CANDIDATE$'):
            request_fingerprint(replace(c,idempotency_key='SECRET TOKEN invalid'))

    def test_06_retry_ids_are_distinct_from_idempotency_and_payload_conflicts(self):
        a=command();b={**a,'request_id':W,'correlation_id':U}
        cases=[(a,b,'SAME_INTENT_STRUCTURE_ONLY')]
        self.assertNotEqual(request_fingerprint(a),request_fingerprint(b))
        cases.append((a,{**b,'idempotency_key':'another-001'},'NEW_INTENT_REVIEW_REQUIRED'))
        for delta in ({'case_ref':V},{'expected_version':{'kind':'cycle','value':'8'}},
                      {'expected_version':{'kind':'case','value':'7'}}):
            cases.append((a,{**b,**delta},'IDEMPOTENCY_CONFLICT_REVIEW_REQUIRED'))
        cases.append((a,{**b,'command':RECHECK,'capture_request_id':V},'DIFFERENT_COMMAND_NOT_A_RETRY'))
        js=probe([dict(operation='retry',previous=a,current=b) for a,b,_ in cases])
        for (a,b,expected),j in zip(cases,js):
            self.assertEqual(compare_retry(a,b),expected);self.assertEqual(j['result'],expected)

    def test_07_fingerprint_ignores_object_order_without_normalizing_values(self):
        raw=command();rev=dict(reversed(list(raw.items())))
        rev['expected_version']=dict(reversed(list(raw['expected_version'].items())))
        self.assertEqual(request_fingerprint(raw),request_fingerprint(rev))
        case={**raw,'expected_version':{'kind':'case','value':'v07'}}
        self.assertNotEqual(request_fingerprint(case),request_fingerprint({**case,'expected_version':{'kind':'case','value':'v7'}}))


class ResponseCandidateTests(unittest.TestCase):
    def test_08_technical_results_remain_noncommercial_in_python_and_js(self):
        cases=[];expected=[]
        for state in ('CAPTURED_LOCAL_ONLY','ALREADY_CAPTURED','VERIFIED_CONTRACT_PENDING','STALE','DENIED','UNAVAILABLE'):
            c=command();r=candidate_response(c,state)
            self.assertEqual(r['schema_version'],RESULT_SCHEMA)
            self.assertFalse(r['outcome']['commercial_effect_confirmed'])
            expected.append(stage(r,c));cases.append(dict(operation='response',response=r,command=c,sent_context=U,current_context=U))
        self.assertEqual(probe(cases),expected)
        for value in expected:
            self.assertTrue(value['accepted']);self.assertFalse(value['has_verified_effect']);self.assertFalse(value['may_execute'])

    def test_09_all_response_correlators_and_digest_are_checked(self):
        c=command();r=candidate_response(c,'CAPTURED_LOCAL_ONLY');bad=[]
        for key,value in [('request_id',W),('correlation_id',W),('case_ref',W),('command',RECHECK),
                          ('schema_version','other'),('request_fingerprint','a'*64)]:
            bad.append({**r,key:value})
        bad.extend([{**r,'actor_id':U},{**r,'outcome':{**r['outcome'],'secret':'never echo'}},
                    {**r,'outcome':{'state':'APPLIED','commercial_effect_confirmed':False}},
                    {**r,'outcome':{**r['outcome'],'commercial_effect_confirmed':True}},
                    {**r,'outcome':{**r['outcome'],'commercial_effect_confirmed':0}}])
        js=probe([dict(operation='response',response=x,command=c,sent_context=U,current_context=U) for x in bad])
        for x,j in zip(bad,js):
            self.assertEqual(stage(x,c),j);self.assertFalse(j['accepted']);self.assertNotIn('secret',str(j))

    def test_10_late_response_from_prior_attempt_is_not_current_success(self):
        old=command();new={**old,'request_id':W}
        response=candidate_response(old,'CAPTURED_LOCAL_ONLY')
        self.assertFalse(stage(response,new)['accepted'])
        self.assertFalse(probe([dict(operation='response',response=response,command=new,sent_context=U,current_context=U)])[0]['accepted'])

    def test_11_actor_store_case_epoch_change_rejects_even_matching_response(self):
        c=command();r=candidate_response(c,'CAPTURED_LOCAL_ONLY')
        self.assertFalse(stage(r,c,V)['accepted'])
        js=probe([dict(operation='response',response=r,command=c,sent_context=U,current_context=V),
                  dict(operation='response',response=r,command=c,sent_context=U,current_context=U,
                       change_context_after_await=True,changed_context=V)])
        self.assertTrue(all(not x['accepted'] for x in js))

    def test_12_response_also_binds_version_key_and_capture_reference(self):
        c=VECTORS[3]['command'];r=candidate_response(c,'VERIFIED_REVIEW_ONLY_LOCAL')
        for patch in ({'idempotency_key':'another-001'}, {'expected_version':{'kind':'cycle','value':'8'}},
                      {'capture_request_id':W}):
            self.assertFalse(stage(r,{**c,**patch})['accepted'])
        self.assertTrue(stage(r,c)['accepted'])
        for key in ('actor_id','session_id','store_ref','snapshot_sha256','closure_event_ref','capture_request_id','idempotency_key'):
            self.assertNotIn(key,r)

    def test_13_wrong_operation_and_commercial_states_are_never_projected(self):
        for c,state in ((command(),'VERIFIED_REVIEW_ONLY_LOCAL'),(VECTORS[3]['command'],'CAPTURED_LOCAL_ONLY'),
                        (command(),'APPLIED'),(command(),'ALREADY_APPLIED')):
            with self.assertRaises(InvalidCandidate):candidate_response(c,state)

    def test_14_existing_frontend_and_s1_do_not_gain_an_unapproved_command(self):
        c=command();r=candidate_response(c,'CAPTURED_LOCAL_ONLY')
        expected=dict(contract_id='C11',contract_version='candidate',request_id=U,correlation_id=V,
                      actor_id=U,scope_ref=U,aggregate_ref=U,expected_version='7')
        out=subprocess.run(['node',str(ROOT/'backend/tests/compat_probe.mjs')],
            input=json.dumps(dict(operation='fv',payload=r,expected=expected)),capture_output=True,text=True,check=True)
        self.assertFalse(json.loads(out.stdout)['accepted'])
        source=ROOT/'backend/tests/compat_sources/s1_export.py'
        spec=importlib.util.spec_from_file_location('s1_ui_contract_compat',source)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        with self.assertRaises(Exception):module.export_fields(c)

    def test_15_current_sources_match_recorded_git_blobs_and_hashes(self):
        for item in json.loads((LAB/'source_manifest.json').read_text()):
            data=(ROOT/item['tested_file']).read_bytes()
            with self.subTest(front=item['front']):
                self.assertEqual(hashlib.sha256(data).hexdigest(),item['sha256'])
                self.assertEqual(hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest(),item['git_blob'])


if __name__=='__main__':
    unittest.main()
