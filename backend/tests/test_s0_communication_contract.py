"""Real pinned validators + adversarial compatibility cases, no auth claim."""
import ast
from dataclasses import dataclass, fields
from enum import Enum
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import unittest

from backend.s0_communication_contract import (
    CAPTURE_PROFILE, FV_INTENT_PROFILE, MAX_PG_VERSION, MAX_JS_INTEGER,
    CaptureRequest, InvalidCompatibilityInput, prepare_request,
    parse_receipt_metadata, compare_receipt_metadata, parse_f03_review_candidate,
    match_f03_review, completion_review_projection,
)

HERE=Path(__file__).parent
SOURCES=HERE/'compat_sources'
U='00000000-0000-4000-8000-000000000001'
V='00000000-0000-4000-8000-000000000002'

def capture():
    return dict(case_ref=U,expected_cycle_version=7,idempotency_key='capture-001')

def receipt():
    return dict(store_ref=U,case_ref=U,closure_event_ref=U,assignment_ref=U,
                expected_cycle_version=7,snapshot_sha256='a'*64,message_watermark=U,message_count=2)

def original(name):
    spec=importlib.util.spec_from_file_location('compat_'+name,SOURCES/(name+'.py'))
    mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod)
    return mod

def source_nodes(name,names,namespace):
    tree=ast.parse((SOURCES/(name+'.py')).read_text())
    nodes=[n for n in tree.body if getattr(n,'name',None) in names]
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(SOURCES/(name+'.py')),'exec'),namespace)
    return namespace

def probe(operation,payload,expected=None):
    result=subprocess.run(['node',str(HERE/'compat_probe.mjs')],
        input=json.dumps(dict(operation=operation,payload=payload,expected=expected)),
        capture_output=True,text=True,check=True,timeout=10)
    return json.loads(result.stdout)

def s2_fixture():
    versions=dict(case=1,cycle=2,form=3,catalog=4,assignment=5,identity=6)
    return dict(scope=dict(authenticated=True,authorized=True,tenantAllowed=True,
                  storeId='shop',personId='person',caseId='case',closureId='closure',requestId='request'),
        cutoff=dict(storeId='shop',personId='person',closureId='closure',s0ClosureVerified=True,
                    historyComplete=True,snapshotRef='b'*64,watermark=20,expectedVersions=versions.copy(),
                    sources=[dict(id='msg',storeId='shop',personId='person',caseId='case',sequence=19,
                        available=True,s0Verified=True,claims=[dict(code='cor',value='azul',explicit=True)])]),
        proposal=dict(proposalRef='proposal',fields=[dict(code='cor',value='azul',sourceId='msg')],
                      conflicts=[],advisory=None),catalog=[dict(code='cor',essential=True)],
        current=dict(versions=versions.copy(),closureStillAuthorized=True,
                     assignmentAuthorized=True,personScopeVerified=True),prior=None)

class PhysicalRequestTests(unittest.TestCase):
    def test_payload_roundtrips_into_actual_s0_validator(self):
        target=original('s0_closure')
        for version in (1,7,MAX_PG_VERSION):
            raw={**capture(),'expected_cycle_version':version}
            result=prepare_request(CAPTURE_PROFILE,raw)
            self.assertEqual(result.state,'STRUCTURE_ONLY')
            payload=result.request.to_physical_payload()
            self.assertEqual(payload,raw)
            self.assertTrue(target._valid(target.ClosureRequest(**payload)))

    def test_rejects_identity_authority_and_alias_injection(self):
        for key in ('actor_id','store_ref','session_id','authorized','expected_case_version',
                    'assignment_version','form_version','sendNow','fields_proposed'):
            with self.subTest(key=key):
                self.assertEqual(prepare_request(CAPTURE_PROFILE,{**capture(),key:True}).state,'INPUT_REJECTED')

    def test_type_range_and_no_silent_coercion(self):
        for key,values in {'expected_cycle_version':(True,0,-1,MAX_PG_VERSION+1,'7',7.0),
                           'case_ref':(None,'bad',7),
                           'idempotency_key':('short',' contains space ',None,7)}.items():
            for value in values:
                with self.subTest(key=key,value=value):
                    self.assertEqual(prepare_request(CAPTURE_PROFILE,{**capture(),key:value}).state,'INPUT_REJECTED')

    def test_direct_dto_construction_is_revalidated(self):
        with self.assertRaises(InvalidCompatibilityInput): CaptureRequest(U,True,'capture-001').to_physical_payload()

    def test_case_version_is_not_converted_to_cycle_version(self):
        result=prepare_request(FV_INTENT_PROFILE,dict(case_ref=U,expected_case_version='v7',idempotency_key='capture-001'))
        self.assertEqual(result.state,'CASE_VERSION_BINDING_REQUIRED');self.assertIsNone(result.request)
        self.assertEqual(prepare_request('unknown',capture()).state,'UNSUPPORTED_PROFILE')

    def test_json_safe_integer_guard_preserves_native_pg_version(self):
        for version in (MAX_JS_INTEGER+1,MAX_PG_VERSION):
            request=prepare_request(CAPTURE_PROFILE,{**capture(),'expected_cycle_version':version}).request
            self.assertEqual(request.to_physical_payload()['expected_cycle_version'],version)
            with self.assertRaises(InvalidCompatibilityInput): request.to_js_payload()
        self.assertEqual(CaptureRequest(U,MAX_JS_INTEGER,'capture-001').to_js_payload()['expected_cycle_version'],MAX_JS_INTEGER)

class ReceiptCompatibilityTests(unittest.TestCase):
    def test_matches_actual_atomic_receipt_field_names(self):
        n=source_nodes('s0_atomic',{'S0InternalReceiptLocal'},{'dataclass':dataclass})
        self.assertEqual(set(receipt()),{f.name for f in fields(n['S0InternalReceiptLocal'])})
        self.assertEqual(parse_receipt_metadata(receipt()).message_watermark,U)

    def test_every_metadata_dimension_invalidates_recheck(self):
        self.assertEqual(compare_receipt_metadata(receipt(),receipt()),'UNCHANGED_STRUCTURE_ONLY')
        for key in receipt():
            changed=receipt();changed[key]= {'expected_cycle_version':8,'message_count':3,'snapshot_sha256':'b'*64}.get(key,V)
            with self.subTest(key=key): self.assertEqual(compare_receipt_metadata(receipt(),changed),'STALE_REVIEW_REQUIRED')

    def test_no_uuid_watermark_to_numeric_sequence_coercion(self):
        with self.assertRaises(InvalidCompatibilityInput): parse_receipt_metadata({**receipt(),'message_watermark':20})
        f=s2_fixture();f['cutoff']['watermark']=U
        self.assertEqual(probe('s2',f)['status'],'HISTORY_REVIEW_REQUIRED')

    def test_receipt_rejects_hidden_authority_extras_and_boolean_counts(self):
        for extra in ({'authorized':True},{'form_version':7},{'message_count':True}):
            with self.subTest(extra=extra),self.assertRaises(InvalidCompatibilityInput): parse_receipt_metadata({**receipt(),**extra})

class CrossFrontExecutionTests(unittest.TestCase):
    def test_real_s2_output_is_accepted_by_original_pr1_parser_and_adapter(self):
        output=probe('s2',s2_fixture())
        n=source_nodes('oai_fields',{'FieldKind','ProposedField','proposal_digest'},
                       dict(dataclass=dataclass,Enum=Enum,hashlib=hashlib,json=json,re=re))
        source_nodes('oai_crossfront',{'_candidate'},n)
        proposal=(n['ProposedField']('cor',n['FieldKind'].TEXT_ONLY,'azul'),)
        self.assertEqual(n['_candidate'](output,proposal),'b'*64)
        self.assertEqual(parse_f03_review_candidate(output).field_codes,('cor',))
        self.assertEqual(match_f03_review(output,sealed_metadata_sha256='b'*64,
                         proposed_field_codes=('cor',)),'MATCHED_STRUCTURE_ONLY')

    def test_receipt_hash_is_not_metadata_seal_hash(self):
        output=probe('s2',s2_fixture())
        self.assertEqual(match_f03_review(output,sealed_metadata_sha256=receipt()['snapshot_sha256'],
                         proposed_field_codes=('cor',)),'STALE_REVIEW_REQUIRED')

    def test_field_mismatch_duplicate_unknown_value_and_effect_claim_blocked(self):
        output=probe('s2',s2_fixture())
        self.assertEqual(match_f03_review(output,sealed_metadata_sha256='b'*64,
                         proposed_field_codes=('nome',)),'FIELD_REVIEW_REQUIRED')
        for patch in ({'fieldCodes':['cor','cor']},{'fieldCodes':[]},{'fieldCodes':['CPF']},
                      {'status':'APPLIED'},{'fields_proposed':[]},{'send_authorized':True}):
            with self.subTest(patch=patch),self.assertRaises(InvalidCompatibilityInput): parse_f03_review_candidate({**output,**patch})

    def test_real_s2_revocation_and_stale_are_never_promoted(self):
        for expected,change in [('DENIED',lambda f:f['scope'].update(authorized=False)),
                               ('STALE',lambda f:f['current']['versions'].update(form=8))]:
            f=s2_fixture();change(f);output=probe('s2',f);self.assertEqual(output['status'],expected)
            with self.assertRaises(InvalidCompatibilityInput): parse_f03_review_candidate(output)

    def test_s1_export_parser_does_not_accept_cfi_payload_or_browser_authority(self):
        s1=original('s1_export')
        valid=dict(tipo='lotes',loja_id=U,apos=None,limite=20)
        self.assertEqual(str(s1.export_fields(valid)[1]),U)
        for raw in (capture(),{**valid,'actor_id':U},{**valid,'limite':True}):
            with self.assertRaises(Exception): s1.export_fields(raw)

    def test_real_frontend_has_no_cfi_command_and_rejects_candidate_projection(self):
        expected=dict(contract_id='CFI01',contract_version='candidate',request_id='r',correlation_id='c',
                      actor_id='a',scope_ref='s',aggregate_ref='k',expected_version='v')
        for state in ('CAPTURED_LOCAL_ONLY','ALREADY_CAPTURED','VERIFIED_CONTRACT_PENDING','APPLIED'):
            projection=completion_review_projection(state)
            self.assertFalse(projection['confirmed_persisted'])
            self.assertFalse(probe('fv',projection,expected)['accepted'])
            self.assertNotIn('closure_event_ref',projection)

    def test_real_ui_claimed_applied_still_is_not_verified_effect(self):
        expected=dict(contract_id='C11',contract_version='candidate',request_id='r',correlation_id='c',
                      actor_id='a',scope_ref='s',aggregate_ref='k',expected_version='v')
        response={**expected,'schema_version':'s0-command-result-proposal/0.1',
                  'outcome':dict(status='APPLIED',confirmed_persisted=True,effect_id='e',source_of_truth_version='v2')}
        result=probe('fv',response,expected)
        self.assertTrue(result['accepted']);self.assertFalse(result['hasVerifiedEffect'])

class CompletionProjectionTests(unittest.TestCase):
    def test_only_technical_state_leaves_projection(self):
        for state,expected in [('CAPTURED_LOCAL_ONLY','RECORDED_REVIEW_ONLY'),
                               ('ALREADY_CAPTURED','RECORDED_REVIEW_ONLY'),
                               ('VERIFIED_REVIEW_ONLY_LOCAL','RECHECKED_REVIEW_ONLY'),
                               ('VERIFIED_CONTRACT_PENDING','CONTRACT_PENDING'),
                               ('BLOCKED_S1','DENIED'),('APPLIED','INPUT_REJECTED'),
                               ({'actor_id':'secret','token':'secret'},'INPUT_REJECTED')]:
            with self.subTest(state=state):
                out=completion_review_projection(state)
                self.assertEqual(set(out),{'schema_version','state','confirmed_persisted'})
                self.assertEqual(out['state'],expected)
                self.assertFalse(out['confirmed_persisted'])
                self.assertNotIn('secret',str(out))

    def test_original_capture_field_allowlist_is_unchanged(self):
        source=ast.parse((SOURCES/'s0_authenticated.py').read_text())
        node=next(n for n in source.body if isinstance(n,ast.Assign)
                  and any(isinstance(t,ast.Name) and t.id=='_CAPTURE_FIELDS' for t in n.targets))
        actual=frozenset(ast.literal_eval(node.value.args[0]))
        self.assertEqual(set(prepare_request(CAPTURE_PROFILE,capture()).request.to_physical_payload()),actual)


class PinnedSourceIntegrityTests(unittest.TestCase):
    def test_every_fixture_matches_original_git_blob_and_digest(self):
        for entry in json.loads((SOURCES/'manifest.json').read_text()):
            data=(SOURCES/entry['fixture']).read_bytes()
            with self.subTest(path=entry['path']):
                self.assertEqual(hashlib.sha256(data).hexdigest(),entry['sha256'])
                self.assertEqual(hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest(),entry['git_blob_sha'])
