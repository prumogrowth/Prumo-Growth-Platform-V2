"""Actual GoTrue + PG17 review-request registry; no operational F02 grant.

Inherits and reruns all 32 unchanged restricted CFI scenarios. The new tests
exercise this wrapper with real CFI capture/recheck, random SQL/HMAC test
credentials and real GoTrue. F02 witness digests are deliberately untrusted.
"""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import timedelta
import json
import os
from pathlib import Path
import time
import unittest
from unittest.mock import patch
from uuid import UUID,uuid4

import psycopg
from psycopg import sql
from integration.cfi01 import test_restricted_backend as checkpoint
from backend.f02_reconciled_human_authorization_handoff import (
    ClaimedS0Evidence,ReviewOnlyProposal,LOCAL_RECONCILED,LOCAL_ORIGIN,LAB_SOURCE,
    UNVERIFIED_EXTERNAL,UNRATIFIED_HUMAN,REQUEST_ONLY,
)
from backend.f02_reconciled_review_lifecycle import ReviewWindow
from backend import s0_f02_review_registry_local as registry


class F02ReviewTests(checkpoint.RestrictedBackendTests):
    @classmethod
    def setUpClass(cls):
        if os.environ.get('PRUMO_F02_DISPOSABLE_TEST')!='YES':raise RuntimeError('F02 opt-in required')
        super().setUpClass()
        with psycopg.connect(cls.db,autocommit=True) as c:
            cls.old_definition=c.execute("select pg_get_functiondef('prumo_private.cfi01_atomic_signed_closure_local(text,uuid,uuid,uuid,bigint,uuid,text,uuid,bigint,uuid,text)'::regprocedure)").fetchone()[0]
            c.execute("set prumo.f02_disposable='YES'")
            c.execute((Path(__file__).resolve().parents[2]/'supabase/tests/s0_f02_review_registry_local_only.sql').read_text())

    def setUp(self):
        super().setUp()
        self.registry=registry.S0F02ReviewRegistryLocal(self.gateway)

    def setup_request(self,*,expires_seconds=600):
        self.binding=self.capture()
        r=self.binding.receipt
        self.evidence=ClaimedS0Evidence(self.shop,self.lead,self.case,UUID(r.closure_event_ref),
            LOCAL_RECONCILED,LOCAL_ORIGIN,LAB_SOURCE,'a'*64,'b'*64,'c'*64,'d'*64,
            UNVERIFIED_EXTERNAL,UNRATIFIED_HUMAN)
        with psycopg.connect(self.db) as c:now=c.execute('select clock_timestamp()').fetchone()[0]
        self.proposal=ReviewOnlyProposal(self.shop,self.lead,self.case,UUID(r.closure_event_ref),
            self.channel,uuid4(),'v1','pending-policy-001',now+timedelta(days=1),'f02-review-request-0001',REQUEST_ONLY)
        self.window=ReviewWindow(now-timedelta(minutes=1),now+timedelta(seconds=expires_seconds))

    def call(self,operation='record',*,revision=None,binding=None,evidence=None,proposal=None,window=None):
        return self.registry.execute(self.auth,operation,binding or self.binding,
            evidence or self.evidence,proposal or self.proposal,window or self.window,expected_revision=revision)

    def facts(self):
        with psycopg.connect(self.db) as c:
            return (self.counters(),self.audit_count(),
                c.execute('select count(*) from prumo_private.f02_review_requests_local where case_id=%s',(self.case,)).fetchone()[0],
                c.execute('select count(*) from prumo_private.f02_review_audit_local a join prumo_private.f02_review_requests_local r on r.id=a.request_id where r.case_id=%s',(self.case,)).fetchone()[0])

    def reject(self,state,**kwargs):
        before=self.facts();result=self.call(**kwargs)
        self.assertEqual(result.state.value,state);self.assertIsNone(result.review_ref)
        self.assertEqual(self.facts(),before)
        return result

    def proof_review(self,operation='record',revision=None):
        principal=self.gateway._identity.verify(self.auth)  # Actual GoTrue.
        body=registry.prepare_document(self.binding,self.evidence,self.proposal,self.window)
        return self.registry._parameters(operation,body,revision,self.binding,principal)

    def test_33_intake_is_durable_but_claimed_witnesses_never_gain_authority(self):
        self.setup_request();result=self.call()
        self.assertEqual(result.state,registry.ReviewState.RECORDED_REVIEW_ONLY)
        self.assertEqual(result.revision,1)
        self.assertFalse(result.projection()['send_authorized'])
        self.assertEqual(result.projection()['evidence_scope'],'CFI_CONTEXT_ONLY_F02_EVIDENCE_PENDING')
        with psycopg.connect(self.db) as c:
            row=c.execute('select actor_id,session_id,claimed_body,state from prumo_private.f02_review_requests_local where id=%s',(result.review_ref,)).fetchone()
            self.assertEqual(row[0],self.actor)
            self.assertEqual(str(row[1]),str(self.gateway._identity.verify(self.auth).session_id))
            self.assertEqual(row[2]['evidence']['c08_local_witness_sha256'],'b'*64)
            self.assertEqual(row[3],'PENDING_EVIDENCE')
            self.assertEqual(c.execute('select count(*) from public.planos_recontato_sinteticos where concessionaria_id=%s',(self.shop,)).fetchone()[0],0)

    def test_34_new_broker_recovers_server_withdrawal_without_client_timeline(self):
        self.setup_request();first=self.call()
        self.assertEqual(self.call('withdraw',revision=1).state,registry.ReviewState.WITHDRAWN_REVIEW_ONLY)
        self.registry=registry.S0F02ReviewRegistryLocal(self.gateway)  # No retained request state.
        current=self.call('read',revision=1)
        self.assertEqual((current.review_ref,current.revision,current.state),(first.review_ref,2,registry.ReviewState.WITHDRAWN_REVIEW_ONLY))
        self.assertEqual(self.call().state,registry.ReviewState.WITHDRAWN_REVIEW_ONLY)

    def test_35_exact_replay_keeps_request_and_immutable_deadline(self):
        self.setup_request();first=self.call();second=self.call()
        self.assertEqual(first.review_ref,second.review_ref)
        self.assertEqual(second.state,registry.ReviewState.REPLAY_REVIEW_ONLY)
        self.assertEqual(first.expires_at,second.expires_at)
        self.assertEqual(self.facts()[2:],(1,2))

    def test_36_payload_or_deadline_change_conflicts_without_any_committed_nonce(self):
        self.setup_request();self.call()
        self.reject('IDEMPOTENCY_CONFLICT',proposal=replace(self.proposal,proposed_at=self.proposal.proposed_at+timedelta(minutes=1)))
        self.reject('IDEMPOTENCY_CONFLICT',window=replace(self.window,expires_at=self.window.expires_at+timedelta(minutes=1)))
        self.reject('IDEMPOTENCY_CONFLICT',evidence=replace(self.evidence,c08_local_witness_sha256='e'*64))

    def test_37_two_actual_connections_one_request_under_same_key(self):
        self.setup_request()
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(lambda _:self.call(),range(2)))
        self.assertEqual({r.state for r in results},{registry.ReviewState.RECORDED_REVIEW_ONLY,registry.ReviewState.REPLAY_REVIEW_ONLY})
        self.assertEqual(len({r.review_ref for r in results}),1);self.assertEqual(self.facts()[2:],(1,2))

    def test_38_real_logout_revokes_request_read_and_replay(self):
        self.setup_request();self.call()
        from scripts.test_s0_cfi01_auth_rest_local import request
        self.assertIn(request(self.api,self.key,'POST','/auth/v1/logout',token=self.token)[0],(200,204))
        self.reject('DENIED',operation='read');self.reject('DENIED')

    def test_39_revoked_store_permission_blocks_intake(self):
        self.setup_request()
        with psycopg.connect(self.db) as c:c.execute('update public.vinculos_papel_escopo set valido_ate=clock_timestamp() where ator_id=%s',(self.actor,))
        self.reject('DENIED')

    def test_40_changed_physical_version_blocks_intake(self):
        self.setup_request()
        with psycopg.connect(self.db) as c:c.execute('update public.ciclos_comerciais set versao_registro=2 where id=%s',(self.cycle,))
        self.reject('STALE')

    def test_41_new_messages_block_intake(self):
        self.setup_request()
        with psycopg.connect(self.db) as c:self.add_message(c,uuid4())
        self.reject('STALE')

    def test_42_sql_password_or_old_cfi_mac_cannot_sign_a_review_document(self):
        self.setup_request();params=list(self.proof_review());before=self.facts()
        params[-1]=params[-2]  # Deliberately wrong HMAC domain.
        self.deny_sql(registry._SQL,params);self.assertEqual(self.facts(),before)
        params=list(self.proof_review());params[1]=params[1].replace('pending-policy-001','forged-policy-001')
        self.deny_sql(registry._SQL,params);self.assertEqual(self.facts(),before)

    def test_43_nonce_replay_denied_without_second_review_audit(self):
        self.setup_request();params=self.proof_review()
        with psycopg.connect(self.dsn) as c:c.execute(registry._SQL,params).fetchall()
        before=self.facts();self.deny_sql(registry._SQL,params);self.assertEqual(self.facts(),before)

    def test_44_review_audit_failure_rolls_back_cfi_nonce_audit_and_request(self):
        self.setup_request();name='fault_'+uuid4().hex
        with psycopg.connect(self.db) as c:
            c.execute(sql.SQL("create function prumo_private.{}() returns trigger language plpgsql as $$ begin raise exception 'F02_TEST_FAULT'; end $$").format(sql.Identifier(name)))
            c.execute(sql.SQL('create trigger {} before insert on prumo_private.f02_review_audit_local for each row execute function prumo_private.{}()').format(sql.Identifier(name),sql.Identifier(name)))
        try:self.reject('UNAVAILABLE')
        finally:
            with psycopg.connect(self.db) as c:
                c.execute(sql.SQL('drop trigger {} on prumo_private.f02_review_audit_local').format(sql.Identifier(name)))
                c.execute(sql.SQL('drop function prumo_private.{}()').format(sql.Identifier(name)))
        self.assertEqual(self.call().state,registry.ReviewState.RECORDED_REVIEW_ONLY)

    def test_45_pr13_full_receipt_comparison_still_precedes_commit(self):
        self.setup_request()
        bad=replace(self.binding,receipt=replace(self.binding.receipt,snapshot_sha256='0'*64))
        self.reject('STALE',binding=bad)
        self.assertEqual(self.call().state,registry.ReviewState.RECORDED_REVIEW_ONLY)

    def test_46_server_clock_rejects_already_expired_request(self):
        self.setup_request(expires_seconds=-1);self.reject('REQUEST_EXPIRED')

    def test_47_expiry_is_terminal_and_replay_cannot_extend_deadline(self):
        self.setup_request(expires_seconds=2);self.call();time.sleep(2.1)
        current=self.call('read')
        self.assertEqual((current.state,current.revision),(registry.ReviewState.EXPIRED_REVIEW_ONLY,2))
        self.assertEqual(self.call().state,registry.ReviewState.EXPIRED_REVIEW_ONLY)
        self.reject('IDEMPOTENCY_CONFLICT',window=replace(self.window,expires_at=self.window.expires_at+timedelta(hours=1)))

    def test_48_future_persisted_clock_fault_cannot_reopen_or_append_history(self):
        self.setup_request();first=self.call()
        # Privileged fixture fault, NOT a user-controlled clock or actual NTP test.
        with psycopg.connect(self.db) as c:
            c.execute("update prumo_private.f02_review_requests_local set last_checked_at=clock_timestamp()+interval '1 hour' where id=%s",(first.review_ref,))
        self.reject('CLOCK_RECHECK_REQUIRED',operation='read')

    def test_49_private_scope_acl_and_original_cfi_definition_preserved(self):
        for table in ('f02_review_requests_local','f02_review_audit_local'):
            self.deny_sql('select * from prumo_private.'+table)
            for role in ('anon','authenticated','service_role'):
                with psycopg.connect(self.db) as c:
                    self.assertFalse(c.execute('select has_table_privilege(%s,%s,\'SELECT\')',(role,'prumo_private.'+table)).fetchone()[0])
        self.deny_sql('set role prumo_s0_f02_review_owner_local')
        with psycopg.connect(self.db) as c:
            self.assertEqual(c.execute("select pg_get_functiondef('prumo_private.cfi01_atomic_signed_closure_local(text,uuid,uuid,uuid,bigint,uuid,text,uuid,bigint,uuid,text)'::regprocedure)").fetchone()[0],self.old_definition)
            self.assertEqual(c.execute("select rolcanlogin,rolsuper,rolbypassrls from pg_roles where rolname='prumo_s0_f02_review_owner_local'").fetchone(),(False,False,False))
            self.assertFalse(c.execute("select has_column_privilege('prumo_cfi01_atomic_owner_local','public.casos_humanos','lead_id','SELECT')").fetchone()[0])

    def test_50_live_session_expiry_waits_for_whole_registry_transaction(self):
        self.setup_request();params=self.proof_review()
        def expire():
            with psycopg.connect(self.db) as c:c.execute("update auth.sessions set not_after=clock_timestamp()-interval '1 second' where id=%s",(params[4],))
        with psycopg.connect(self.dsn) as c,ThreadPoolExecutor(max_workers=1) as pool:
            c.execute(registry._SQL,params).fetchall();pid=c.execute('select pg_backend_pid()').fetchone()[0]
            future=pool.submit(expire)
            try:self.wait_for_any_blocker(pid)
            finally:c.commit()
            future.result(timeout=15)
        self.reject('DENIED',operation='read')

    def test_51_claimed_lead_and_channel_must_match_actual_locked_case(self):
        self.setup_request();lead=uuid4()
        self.reject('DENIED',evidence=replace(self.evidence,lead_id=lead),proposal=replace(self.proposal,lead_id=lead))
        self.reject('DENIED',proposal=replace(self.proposal,channel_id=uuid4()))

    def test_52_withdraw_read_race_has_one_terminal_state_no_reactivation(self):
        self.setup_request();self.call()
        with ThreadPoolExecutor(max_workers=2) as pool:
            pending=pool.submit(self.call,'withdraw',revision=1)
            read=pool.submit(self.call,'read',revision=1)
            self.assertEqual(pending.result(timeout=15).state,registry.ReviewState.WITHDRAWN_REVIEW_ONLY)
            self.assertIn(read.result(timeout=15).state,(registry.ReviewState.CURRENT_REVIEW_ONLY,registry.ReviewState.WITHDRAWN_REVIEW_ONLY))
        self.assertEqual(self.call('read').state,registry.ReviewState.WITHDRAWN_REVIEW_ONLY)

    def test_53_future_cursor_cannot_claim_complete_recovery(self):
        self.setup_request();self.call();self.reject('STALE',operation='read',revision=999)

    def test_54_request_scope_and_audit_cannot_be_deleted_or_rewritten(self):
        self.setup_request();first=self.call()
        self.deny_sql("update prumo_private.f02_review_requests_local set claimed_body='{}' where id=%s",(first.review_ref,),dsn=self.db)
        for table in ('f02_review_requests_local','f02_review_audit_local'):
            self.deny_sql('delete from prumo_private.'+table,dsn=self.db)
            self.deny_sql('truncate prumo_private.'+table+' cascade',dsn=self.db)

    def test_55_invalid_returned_review_revision_rolls_back_all_four_facts(self):
        self.setup_request()
        corrupt='select review_state,review_id,0 as revision,observed_at,request_sha256,expires_at,state,event_ref,store_ref,snapshot_sha256,message_watermark,assignment_ref,cycle_version,message_count from ('+registry._SQL+') r'
        with patch.object(registry,'_SQL',corrupt):self.reject('DENIED')

    def test_56_private_lock_owner_cannot_mutate_key_or_case(self):
        with psycopg.connect(self.db) as c:
            c.execute('grant prumo_s0_f02_review_owner_local to postgres with inherit false,set true')
            c.execute('set local role prumo_s0_f02_review_owner_local')
            for query in ('update prumo_private.cfi01_signing_keys_local set key_id=key_id',
                          'update public.casos_humanos set id=id'):
                with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                    with c.transaction():c.execute(query)
            c.rollback()


if __name__=='__main__':unittest.main(verbosity=2)
