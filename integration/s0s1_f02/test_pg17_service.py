"""F02 durable S0 laboratory fixture: PG17 request, alias and plan review.

No real provider, messages, Meta approval, send, hosted S0, or private data.
"""
import os
import threading
from concurrent.futures import ThreadPoolExecutor
import unittest

try:
    import psycopg
except ImportError:
    psycopg=None

from .pg17_service import prepare_in_admin_transaction as prepare
from .pg17_service import review_in_admin_transaction as review
from integration.s0s1_pre_dispatch import test_pg17_service as pretest


@unittest.skipUnless(os.environ.get('M09_PG17_DISPOSABLE')=='YES' and psycopg,
                     'exclusive disposable PostgreSQL 17 required')
class F02Physical(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pretest.PreDispatchPhysical.setUpClass.__func__(cls)
        try:
            sql=(cls.origin/'integration/s0s1_f02/pg17_schema.sql').read_text()
            with cls.lab.admin() as c:
                c.execute("SET s0_meta.disposable='YES'")
                c.execute("SET s0_f02.install='F02_CANDIDATE_ONLY'")
                c.execute(sql)
        except BaseException:
            pretest.PreDispatchPhysical.tearDownClass.__func__(cls)
            raise

    @classmethod
    def tearDownClass(cls):
        try:
            with cls.lab.admin() as c:
                c.execute('DROP SCHEMA IF EXISTS s0_f02_lab CASCADE')
        finally:
            pretest.PreDispatchPhysical.tearDownClass.__func__(cls)

    def setUp(self):
        pretest.PreDispatchPhysical.setUp(self)
        with self.lab.admin() as c:
            c.execute('TRUNCATE s0_f02_lab.reviews,s0_f02_lab.aliases,'
                      's0_f02_lab.requests CASCADE')
        self.q={
          'request_ref':'request_A','case_ref':'case_A',
          'service_ref':'M09_KEY_A','purpose_ref':'followup_message',
          'consent_purpose_ref':'lead_followup','owner_route':'human',
          'instructions_text':'Plan only authorized template aliases.',
          'instructions_version':'config_v1',
          'start_after_seconds':90,'duration_minutes':45,
          'max_attempts':2
        }
        self.m09_versions=self.versions  # original five-revision Revisions object
        self.versions={k:1 for k in (
            'case','cycle','catalog','assignment','policy','consent','chain')}

    def create(self,edits=None,expected=None):
        with self.lab.admin() as c:
            return prepare(c,{**self.q,**(edits or {})},
                scope=self.scope,principal=self.principal,
                m09_versions=self.m09_versions,
                expected=expected or self.versions7())

    def versions7(self):
        return dict(self.versions)

    def candidate(self):
        out=self.create()
        self.assertEqual(out['decision'],'LAB_REQUEST_RECORDED_NO_MODEL')
        self.assertIsNotNone(out['private'])
        p=out['private']
        t=p['request']['templates'][0]
        return {
          'status':'S0_RECHECK_ONLY',
          'schemaVersion':'prumo.openai.f02-plan-candidate/0.1',
          'requestId':self.q['request_ref'],
          'chainRef':'synthetic_chain',
          'expectedVersions':self.versions7(),
          'attempts':[{
              'templateId':t['id'],'templateVersion':t['version'],
              'purpose':self.q['purpose_ref'],
              'at':p['request']['windowStart']
          }],
          'finalTemplate':None,
          'sendAuthorized':False,'schedulingAuthorized':False,
          'commercialTransitionAuthorized':False,
        }

    def assess(self,proposal,req=None,expected=None):
        with self.lab.admin() as c:
            return review(c,proposal,q=req or self.q,
                          scope=self.scope,principal=self.principal,
                          m09_versions=self.m09_versions,
                          expected=expected or self.versions7())

    def deny(self,x):
        self.assertNotIn(x['decision'],(
            'LAB_REQUEST_RECORDED_NO_MODEL','LAB_PROPOSAL_RECORDED_REVIEW_ONLY'))
        self.assertFalse(x['send_authorized'])
        self.assertFalse(x['schedule_authorized'])
        self.assertFalse(x['production_authorized'])
        self.assertFalse(x['provider_approval_verified'])
        self.assertFalse(x['consent_source_authenticated'])

    def counts(self):
        with self.lab.admin() as c:
            vals=[]
            for table in ('requests','aliases','reviews'):
                vals.append(c.execute('SELECT COUNT(*) AS n FROM s0_f02_lab.'+
                          table).fetchone()['n'])
            return tuple(vals)

    def test_01_private_envelope_and_persistent_alias(self):
        out=self.create()
        self.assertEqual(out['decision'],'LAB_REQUEST_RECORDED_NO_MODEL')
        p=out['private']
        self.assertEqual(p['schemaVersion'],
                         'prumo.openai.f02-plan-private/0.1-candidate')
        self.assertTrue(p['scope']['authenticated'])  # fixture only!
        self.assertEqual(p['request']['templates'][0]['id'],'tpl_A')
        self.assertEqual(self.counts(),(1,1,0))
        with self.lab.admin() as c:
            alias=c.execute('SELECT alias,template_ref FROM s0_f02_lab.aliases').fetchone()
        self.assertEqual(alias['alias'],'tpl_001')
        self.assertEqual(alias['template_ref'],'tpl_A')
        self.assertFalse(out['send_authorized'])

    def test_02_exact_request_replay_recovers_same_provider_tag(self):
        first=self.create()
        second=self.create()
        self.assertEqual(second['decision'],'LAB_REQUEST_REPLAY_REVIEW_ONLY')
        self.assertEqual(first['private']['providerTag'],
                         second['private']['providerTag'])
        self.assertEqual(self.counts(),(1,1,0))

    def test_03_request_ref_collision_denied(self):
        self.create()
        x=self.create({'duration_minutes':50})
        self.deny(x)
        self.assertEqual(x['reason'],'REQUEST_COLLISION')
        self.assertEqual(self.counts(),(1,1,0))

    def test_04_invalid_scope_and_missing_service(self):
        for change in ({'service_ref':'FORGED'}, {'new_field':'true'},
                       {'max_attempts':True},{'instructions_text':'case_A'},
                       {'start_after_seconds':0},{'duration_minutes':2000}):
            x=self.create(change)
            self.deny(x)
            self.assertEqual(x['decision'],'DENIED')
        self.assertEqual(self.counts(),(0,0,0))

    def test_05_stale_versions_all_independent(self):
        for key in self.versions:
            versions=self.versions7();versions[key]=2
            self.deny(self.create(expected=versions))
        self.assertEqual(self.counts(),(0,0,0))

    def test_06_revoked_consent_denies_without_journal(self):
        with self.lab.admin() as c:
            c.execute("UPDATE s0_pre_dispatch_lab.consents SET state='REVOKED'")
        self.deny(self.create())
        self.assertEqual(self.counts(),(0,0,0))

    def test_07_global_and_purpose_suppression_denies(self):
        for purpose in ('*','lead_followup'):
            with self.lab.admin() as c:
                c.execute('UPDATE s0_pre_dispatch_lab.suppressions '
                          'SET active=true WHERE purpose_ref=%s',(purpose,))
            self.deny(self.create())
            with self.lab.admin() as c:
                c.execute('UPDATE s0_pre_dispatch_lab.suppressions '
                          'SET active=false WHERE purpose_ref=%s',(purpose,))
        self.assertEqual(self.counts(),(0,0,0))

    def test_08_nonmatching_template_purpose_is_not_catalog(self):
        self.deny(self.create({'purpose_ref':'sales_offer'}))
        self.assertEqual(self.counts(),(0,0,0))

    def test_09_unapproved_template_and_inactive_grant_no_catalog(self):
        with self.lab.admin() as c:
            c.execute('UPDATE s0_pre_dispatch_lab.templates '
                      'SET provider_approved=false')
        self.deny(self.create())
        with self.lab.admin() as c:
            c.execute('UPDATE s0_pre_dispatch_lab.templates '
                      'SET provider_approved=true')
            c.execute('UPDATE s0_pre_dispatch_lab.grants SET active=false')
        self.deny(self.create())
        self.assertEqual(self.counts(),(0,0,0))

    def test_10_case_cross_store_or_inactive_denies(self):
        with self.lab.admin() as c:
            c.execute("UPDATE s0_pre_dispatch_lab.cases "
                      "SET concessionaria_id='store-B'")
        self.deny(self.create())
        with self.lab.admin() as c:
            c.execute("UPDATE s0_pre_dispatch_lab.cases "
                      "SET concessionaria_id='store-A',active=false")
        self.deny(self.create())
        self.assertEqual(self.counts(),(0,0,0))

    def test_11_pg17_revoke_channel_denies_new_planning(self):
        from integration.s0s1_m09_registry.pg17_registry import (
            revoke_channel_in_admin_transaction
        )
        with self.lab.admin() as c:
            revoke_channel_in_admin_transaction(
                c,'route_A','channel_A',1,1,1,1)
        self.deny(self.create())
        self.assertEqual(self.counts(),(0,0,0))

    def test_12_valid_candidate_is_stored_as_review_only(self):
        proposal=self.candidate()
        x=self.assess(proposal)
        self.assertEqual(x['decision'],'LAB_PROPOSAL_RECORDED_REVIEW_ONLY')
        self.assertFalse(x['send_authorized'])
        self.assertEqual(self.counts(),(1,1,1))

    def test_13_exact_proposal_replay_is_review_only(self):
        proposal=self.candidate()
        self.assess(proposal)
        x=self.assess(proposal)
        self.assertEqual(x['decision'],'LAB_ALREADY_REVIEWED_NO_EFFECT')
        self.assertFalse(x['schedule_authorized'])
        self.assertEqual(self.counts(),(1,1,1))

    def test_14_divergent_plan_replay_conflict(self):
        proposal=self.candidate()
        self.assess(proposal)
        changed={**proposal,'attempts':[]}
        x=self.assess(changed)
        self.deny(x)
        self.assertEqual(x['reason'],'PROPOSAL_CONFLICT')
        self.assertEqual(self.counts(),(1,1,1))

    def test_15_model_cannot_claim_send_grant(self):
        proposal=self.candidate()
        altered={**proposal,'sendAuthorized':True}
        self.deny(self.assess(altered))
        self.assertEqual(self.counts(),(1,1,0))

    def test_16_unknown_template_and_wrong_scope_denied(self):
        proposal=self.candidate()
        wrong={**proposal,'attempts':[{**proposal['attempts'][0],
                   'templateId':'FORGED'}]}
        self.deny(self.assess(wrong))
        self.assertEqual(self.counts(),(1,1,0))

    def test_17_recheck_of_consent_after_plan_creation(self):
        proposal=self.candidate()
        with self.lab.admin() as c:
            c.execute("UPDATE s0_pre_dispatch_lab.consents "
                      "SET state='REVOKED',revision=revision+1")
        self.deny(self.assess(proposal))
        self.assertEqual(self.counts(),(1,1,0))

    def test_18_recheck_of_template_after_plan_creation(self):
        proposal=self.candidate()
        with self.lab.admin() as c:
            c.execute("UPDATE s0_pre_dispatch_lab.templates "
                      "SET revision=revision+1,provider_approved=false")
        self.deny(self.assess(proposal))
        self.assertEqual(self.counts(),(1,1,0))

    def test_19_recheck_of_case_after_plan_creation(self):
        proposal=self.candidate()
        with self.lab.admin() as c:
            c.execute("UPDATE s0_pre_dispatch_lab.cases "
                      "SET policy_revision=policy_revision+1,global_opt_out=true")
        self.deny(self.assess(proposal))
        self.assertEqual(self.counts(),(1,1,0))

    def test_20_transaction_rollback_removes_request_and_alias(self):
        try:
            with self.lab.admin() as c:
                x=prepare(c,self.q,scope=self.scope,
                          principal=self.principal,m09_versions=self.m09_versions,
                          expected=self.versions7())
                self.assertEqual(x['decision'],'LAB_REQUEST_RECORDED_NO_MODEL')
                raise RuntimeError('unknown commit')
        except RuntimeError:
            pass
        self.assertEqual(self.counts(),(0,0,0))
        self.assertEqual(self.create()['decision'],'LAB_REQUEST_RECORDED_NO_MODEL')

    def test_21_runtime_cannot_read_template_alias_or_plan(self):
        for table in ('requests','aliases','reviews'):
            with psycopg.connect(self.lab.runtime_dsn) as c:
                with self.assertRaises(psycopg.Error):
                    c.execute('SELECT * FROM s0_f02_lab.'+table)

    def test_22_concurrent_same_request_no_duplicate(self):
        gate=threading.Barrier(2)
        def job():
            with self.lab.admin() as c:
                gate.wait(timeout=8)
                return prepare(c,self.q,scope=self.scope,principal=self.principal,
                       m09_versions=self.m09_versions,
                       expected=self.versions7())['decision']
        with ThreadPoolExecutor(max_workers=2) as pool:
            xs=[pool.submit(job) for _ in range(2)]
            outcomes=[x.result(timeout=15) for x in xs]
        self.assertCountEqual(outcomes,
            ['LAB_REQUEST_RECORDED_NO_MODEL','LAB_REQUEST_REPLAY_REVIEW_ONLY'])
        self.assertEqual(self.counts(),(1,1,0))

    def test_23_invalid_response_versions_or_late_window_denies(self):
        proposal=self.candidate()
        bad=dict(proposal)
        bad['expectedVersions']={**self.versions,'policy':2}
        self.deny(self.assess(bad))
        other={**proposal,'attempts':[{
           **proposal['attempts'][0],'at':'2026-01-01T00:00:00Z'}]}
        self.deny(self.assess(other))

    def test_24_absent_consent_cannot_be_opt_in(self):
        with self.lab.admin() as c:
            c.execute('DELETE FROM s0_pre_dispatch_lab.consents')
        self.deny(self.create())
        self.assertEqual(self.counts(),(0,0,0))


if __name__=='__main__':
    unittest.main()
