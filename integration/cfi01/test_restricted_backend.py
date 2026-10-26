"""Real GoTrue + PG17 tests of the consolidated CFI backend and audit.

Inherits all 14 checkpoint scenarios without replacing identity or SQL with
stubs. New scenarios use random disposable SQL/HMAC credentials and disable the
published fixture key. No public UI command or commercial permission is added.
"""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import hmac
import secrets
import time
import unittest
from unittest.mock import patch
import uuid
from urllib.parse import urlsplit

import psycopg
from psycopg import sql

from integration.cfi01 import test_transactional_communication as checkpoint
from backend import s0_cfi01_atomic_commands_local as atomic
from backend.s0_cfi01_communication_local import S0CFI01CommunicationLocal


class RestrictedBackendTests(checkpoint.TransactionalCommunicationTests):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.key_id = uuid.uuid4()
        cls.secret = secrets.token_bytes(48)
        password = secrets.token_urlsafe(40)
        with psycopg.connect(cls.db) as c:
            c.execute('update prumo_private.cfi01_signing_keys_local set active=false')
            c.execute('insert into prumo_private.cfi01_signing_keys_local(key_id,secret) values (%s,%s)', (cls.key_id, cls.secret))
            c.execute(sql.SQL('alter role prumo_cfi01_pgtest_login password {}').format(sql.Literal(password)))
        u = urlsplit(cls.db)
        cls.dsn = f'postgresql://prumo_cfi01_pgtest_login:{password}@{u.hostname}:{u.port}/postgres'
        cls.gateway = atomic.S0CFI01AtomicCommandsLocal(cls.api, cls.key, cls.dsn,
                                                      key_id=cls.key_id, signing_key=cls.secret)
        cls.adapter = S0CFI01CommunicationLocal(cls.gateway)

    def audit_count(self):
        with psycopg.connect(self.db) as c:
            return c.execute('select count(*) from prumo_private.cfi01_command_audit_local where case_id=%s', (self.case,)).fetchone()[0]

    def refused(self, call, state):
        before = self.audit_count()
        result = super().refused(call, state)
        self.assertEqual(self.audit_count(), before)
        return result

    def tearDown(self):
        super().tearDown()
        # Every accepted operation has an exact nonce/key and receipt binding;
        # no observation is allowed to become a cross-store audit claim.
        with psycopg.connect(self.db) as c:
            invalid = c.execute('''select count(*) from prumo_private.cfi01_command_audit_local a
                left join prumo_private.cfi01_consumed_nonces_local n on n.nonce=a.nonce and n.key_id=a.key_id
                left join prumo_private.cfi01_human_closure_events_local e on e.id=a.receipt_id
                where a.case_id=%s and (n.nonce is null or a.store_id<>%s or a.actor_id<>%s
                  or a.cycle_version<>1 or (a.receipt_id is not null and
                    (e.id is null or e.caso_id<>a.case_id or e.concessionaria_id<>a.store_id
                     or e.ator_id<>a.actor_id or e.sessao_id<>a.session_id)))''', (self.case, self.shop, self.actor)).fetchone()[0]
            self.assertEqual(invalid, 0)

    def proof(self, *, key_id=None, secret=None):
        principal = self.gateway._identity.verify(self.auth)  # Actual GoTrue.
        key_id = self.key_id if key_id is None else key_id
        issued, nonce = int(time.time()), uuid.uuid4()
        material = self.gateway._material('capture_human_closure', principal, self.case,
                    1, None, self.payload['idempotency_key'], key_id, issued, nonce)
        mac = hmac.new(self.secret if secret is None else secret, material, hashlib.sha256).hexdigest()
        return ('capture_human_closure', principal.actor_id, principal.session_id,
                self.case, 1, None, self.payload['idempotency_key'], key_id, issued, nonce, mac)

    def deny_sql(self, statement, params=None, *, dsn=None):
        with self.assertRaises(psycopg.errors.InsufficientPrivilege):
            with psycopg.connect(self.dsn if dsn is None else dsn) as c:
                c.execute(statement, params)

    def wait_for_any_blocker(self, pid):
        deadline = time.monotonic()+8
        while time.monotonic() < deadline:
            with psycopg.connect(self.db) as c:
                if c.execute("select 1 from pg_stat_activity a where a.wait_event_type='Lock' and %s=any(pg_blocking_pids(a.pid))", (pid,)).fetchone():
                    return
            time.sleep(.05)
        self.fail('expected real PostgreSQL blocking relation absent')

    def test_15_application_has_only_atomic_entry_no_table_or_owner_role(self):
        for relation in ('auth.sessions','public.casos_humanos','public.mensagens',
                         'prumo_private.cfi01_signing_keys_local',
                         'prumo_private.cfi01_human_closure_events_local',
                         'prumo_private.cfi01_command_audit_local'):
            self.deny_sql(sql.SQL('select * from {} limit 1').format(sql.Identifier(*relation.split('.'))))
        self.deny_sql('set role prumo_cfi01_atomic_owner_local')
        with psycopg.connect(self.db) as c:
            old = 'prumo_private.cfi01_signed_prerequisite_local(text,uuid,uuid,uuid,bigint,uuid,uuid,bigint,uuid,text)'
            self.assertFalse(c.execute("select has_function_privilege('prumo_cfi01_pgtest_login',%s,'execute')", (old,)).fetchone()[0])
            for role in ('anon','authenticated','service_role'):
                self.assertFalse(c.execute('select has_function_privilege(%s,%s,\'execute\')', (role, 'prumo_private.cfi01_atomic_signed_closure_local(text,uuid,uuid,uuid,bigint,uuid,text,uuid,bigint,uuid,text)')).fetchone()[0])

    def test_16_lock_owner_cannot_update_domain_or_secrets(self):
        for table, column in [('public.casos_humanos','id'), ('public.ciclos_comerciais','id'),
                              ('public.concessionarias','id'), ('public.atribuicoes_humanas','id'),
                              ('public.conversas','id'), ('public.mensagens','id'),
                              ('public.vinculos_papel_escopo','id'), ('public.equipe_prumo_s1','ator_id'),
                              ('prumo_private.cfi01_signing_keys_local','key_id')]:
            with psycopg.connect(self.db) as c:
                # Setup must succeed outside assertRaises; a failed GRANT is
                # not evidence that UPDATE under the executor was denied.
                c.execute('grant prumo_cfi01_atomic_owner_local to postgres with inherit false,set true')
                c.execute('set local role prumo_cfi01_atomic_owner_local')
                self.assertEqual(c.execute('select current_user').fetchone()[0], 'prumo_cfi01_atomic_owner_local')
                with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                    with c.transaction():
                        c.execute(sql.SQL('update {} set {}={}').format(sql.Identifier(*table.split('.')),sql.Identifier(column),sql.Identifier(column)))
                c.rollback()  # Also restores exact installer membership.
        self.capture()  # All FOR UPDATE/SHARE locks still work after tightening.

    def test_17_capture_and_recheck_are_audited_with_distinct_nonces(self):
        binding=self.capture()
        self.assertEqual(self.adapter.recheck(self.auth,binding).state,'VERIFIED_CONTRACT_PENDING')
        with psycopg.connect(self.db) as c:
            rows=c.execute('select operation,result,nonce,key_id,receipt_id from prumo_private.cfi01_command_audit_local where case_id=%s order by recorded_at',(self.case,)).fetchall()
        self.assertEqual([(r[0],r[1]) for r in rows],[('capture_human_closure','CAPTURED_LOCAL_ONLY'),('recheck_human_closure','VERIFIED_REVIEW_ONLY_LOCAL')])
        self.assertNotEqual(rows[0][2],rows[1][2])
        self.assertTrue(all(r[3]==self.key_id and str(r[4])==binding.receipt.closure_event_ref for r in rows))

    def test_18_audit_failure_rolls_back_receipt_nonce_and_retry(self):
        name='audit_fault_'+uuid.uuid4().hex
        with psycopg.connect(self.db) as c:
            c.execute(sql.SQL("create function prumo_private.{}() returns trigger language plpgsql as $$ begin raise exception 'DISPOSABLE_AUDIT_FAULT'; end $$").format(sql.Identifier(name)))
            c.execute(sql.SQL('create trigger {} before insert on prumo_private.cfi01_command_audit_local for each row execute function prumo_private.{}()').format(sql.Identifier(name),sql.Identifier(name)))
        try:
            self.refused(lambda:self.adapter.capture(self.auth,self.payload),'UNAVAILABLE')
        finally:
            with psycopg.connect(self.db) as c:
                c.execute(sql.SQL('drop trigger {} on prumo_private.cfi01_command_audit_local').format(sql.Identifier(name)))
                c.execute(sql.SQL('drop function prumo_private.{}()').format(sql.Identifier(name)))
        self.capture();self.assertEqual(self.audit_count(),1)

    def test_19_expired_live_session_denies_already_signed_command(self):
        params=self.proof();before=self.counters()
        with psycopg.connect(self.db) as c:
            c.execute("update auth.sessions set not_after=clock_timestamp()-interval '1 second' where id=%s",(params[2],))
        self.deny_sql(atomic._ATOMIC_INTERNAL_SQL,params)
        self.assertEqual(self.counters(),before);self.assertEqual(self.audit_count(),0)

    def test_20_revoked_key_denies_valid_proof_and_published_key_is_disabled(self):
        params=self.proof();before=self.counters()
        with psycopg.connect(self.db) as c:c.execute('update prumo_private.cfi01_signing_keys_local set active=false where key_id=%s',(self.key_id,))
        try:
            self.deny_sql(atomic._ATOMIC_INTERNAL_SQL,params)
        finally:
            with psycopg.connect(self.db) as c:c.execute('update prumo_private.cfi01_signing_keys_local set active=true where key_id=%s',(self.key_id,))
        published=self.proof(key_id=uuid.UUID('cfeed000-0000-4000-8000-000000000001'),secret=bytes.fromhex('1160b59cd3466f55112233445566778899aabbccddeeff001122334455667788'))
        self.deny_sql(atomic._ATOMIC_INTERNAL_SQL,published)
        self.assertEqual(self.counters(),before);self.assertEqual(self.audit_count(),0)

    def test_21_replay_rolls_back_without_second_audit(self):
        params=self.proof()
        with psycopg.connect(self.dsn) as c:c.execute(atomic._ATOMIC_INTERNAL_SQL,params).fetchall()
        before=self.counters()
        self.deny_sql(atomic._ATOMIC_INTERNAL_SQL,params)
        self.assertEqual(self.counters(),before);self.assertEqual(self.audit_count(),1)

    def test_22_logout_waits_for_inflight_transaction_then_revokes(self):
        params=self.proof()
        with psycopg.connect(self.dsn) as c,ThreadPoolExecutor(max_workers=1) as pool:
            c.execute(atomic._ATOMIC_INTERNAL_SQL,params).fetchall()
            pid=c.execute('select pg_backend_pid()').fetchone()[0]
            future=pool.submit(checkpoint.request,self.api,self.key,'POST','/auth/v1/logout',token=self.token)
            try:self.wait_for_any_blocker(pid)
            finally:c.commit()
            self.assertIn(future.result(timeout=15)[0],(200,204))
        self.refused(lambda:self.adapter.capture(self.auth,self.payload),'DENIED')
        self.assertEqual(self.audit_count(),1)

    def test_23_key_revocation_waits_for_command_commit(self):
        def revoke():
            with psycopg.connect(self.db) as c:c.execute('update prumo_private.cfi01_signing_keys_local set active=false where key_id=%s',(self.key_id,))
        with psycopg.connect(self.dsn) as c,ThreadPoolExecutor(max_workers=1) as pool:
            c.execute(atomic._ATOMIC_INTERNAL_SQL,self.proof()).fetchall()
            pid=c.execute('select pg_backend_pid()').fetchone()[0]
            future=pool.submit(revoke)
            try:self.wait_for_any_blocker(pid)
            finally:c.commit()
            future.result(timeout=15)
        try:self.refused(lambda:self.adapter.capture(self.auth,self.payload),'DENIED')
        finally:
            with psycopg.connect(self.db) as c:c.execute('update prumo_private.cfi01_signing_keys_local set active=true where key_id=%s',(self.key_id,))
        self.assertEqual(self.audit_count(),1)

    def test_24_receipt_and_audit_are_immutable_even_for_installer(self):
        self.capture()
        for table in ('cfi01_human_closure_events_local','cfi01_command_audit_local'):
            for statement in ('update prumo_private.{} set {}={}', 'delete from prumo_private.{}', 'truncate prumo_private.{} cascade'):
                query=statement.format(table,*(['id','id'] if table.endswith('events_local') else ['nonce','nonce']))
                self.deny_sql(query,dsn=self.db)
        self.assertEqual(self.audit_count(),1)

    def test_25_malformed_sql_result_rolls_back_before_commit(self):
        # Real SQL function still executes and writes. Corrupt only the returned
        # digest in an adversarial SQL projection, then require Python rollback.
        original=atomic._ATOMIC_INTERNAL_SQL
        corrupt="select state,event_ref,store_ref,repeat('z',64),message_watermark,assignment_ref,cycle_version,message_count from ("+original+") r"
        with patch.object(atomic,'_ATOMIC_INTERNAL_SQL',corrupt):
            self.refused(lambda:self.adapter.capture(self.auth,self.payload),'DENIED')
        self.capture();self.assertEqual(self.audit_count(),1)

    def test_26_same_operator_two_stores_audit_uses_database_scope(self):
        self.capture()
        refs={name:uuid.uuid4() for name in ('shop','lead','cycle','case','assignment','channel','conversation','message')}
        with psycopg.connect(self.db) as c:
            c.execute("insert into public.concessionarias(id,nome_operacional) values (%s,'SECOND DISPOSABLE STORE')",(refs['shop'],))
            c.execute("insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel) values (%s,%s,'operador')",(self.actor,refs['shop']))
            c.execute("insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado) values (%s,%s,'+5581999888877')",(refs['lead'],refs['shop']))
            c.execute("insert into public.ciclos_comerciais(id,concessionaria_id,lead_id,status_comercial,versao_registro) values (%s,%s,%s,'em atendimento pelo operador',1)",(refs['cycle'],refs['shop'],refs['lead']))
            c.execute('insert into public.casos_humanos(id,concessionaria_id,lead_id,ciclo_id) values (%s,%s,%s,%s)',(refs['case'],refs['shop'],refs['lead'],refs['cycle']))
            c.execute('insert into public.atribuicoes_humanas(id,concessionaria_id,caso_id,operador_id) values (%s,%s,%s,%s)',(refs['assignment'],refs['shop'],refs['case'],self.actor))
            c.execute('insert into public.canais_loja(id,concessionaria_id,identificador_emissor) values (%s,%s,%s)',(refs['channel'],refs['shop'],str(refs['channel'])))
            c.execute('insert into public.conversas(id,concessionaria_id,lead_id,canal_id,caso_id) values (%s,%s,%s,%s,%s)',(refs['conversation'],refs['shop'],refs['lead'],refs['channel'],refs['case']))
            c.execute("insert into public.mensagens(id,concessionaria_id,conversa_id,canal_id,caso_id,direcao,origem,conteudo_sintetico,id_externo) values (%s,%s,%s,%s,%s,'entrada','simulado','synthetic other store',%s)",(refs['message'],refs['shop'],refs['conversation'],refs['channel'],refs['case'],str(refs['message'])))
        payload={**self.payload,'case_ref':str(refs['case'])}
        result=self.adapter.capture(self.auth,payload)
        self.assertEqual(result.state,'VERIFIED_CONTRACT_PENDING')
        self.assertEqual(result.binding.receipt.store_ref,str(refs['shop']))
        with psycopg.connect(self.db) as c:
            c.execute('update public.vinculos_papel_escopo set valido_ate=clock_timestamp() where ator_id=%s and concessionaria_id=%s',(self.actor,refs['shop']))
        self.assertEqual(self.adapter.recheck(self.auth,result.binding).state,'DENIED')
        self.capture()  # The original store's grant remains valid.
        with psycopg.connect(self.db) as c:
            rows=c.execute('select case_id,store_id,count(*) from prumo_private.cfi01_command_audit_local where case_id in (%s,%s) group by case_id,store_id',(self.case,refs['case'])).fetchall()
        self.assertEqual({(r[0],r[1]):r[2] for r in rows},{(self.case,self.shop):2,(refs['case'],refs['shop']):1})

    def test_27_session_expiry_update_waits_for_inflight_command(self):
        params=self.proof()
        next_proof=self.proof()  # Signed while GoTrue/session are still valid.
        def expire():
            with psycopg.connect(self.db) as c:
                c.execute("update auth.sessions set not_after=clock_timestamp()-interval '1 second' where id=%s",(params[2],))
        with psycopg.connect(self.dsn) as c,ThreadPoolExecutor(max_workers=1) as pool:
            c.execute(atomic._ATOMIC_INTERNAL_SQL,params).fetchall()
            pid=c.execute('select pg_backend_pid()').fetchone()[0]
            future=pool.submit(expire)
            try:self.wait_for_any_blocker(pid)
            finally:c.commit()
            future.result(timeout=15)
        self.deny_sql(atomic._ATOMIC_INTERNAL_SQL,next_proof)
        self.assertEqual(self.audit_count(),1)

    def test_28_owner_has_only_required_column_grants(self):
        owner='prumo_cfi01_atomic_owner_local'
        with psycopg.connect(self.db) as c:
            for table,column in [('public.casos_humanos','lead_id'),('public.mensagens','id_externo'),
                                 ('prumo_private.cfi01_human_closure_events_local','registrado_em'),
                                 ('prumo_private.cfi01_consumed_nonces_local','used_at')]:
                self.assertEqual(c.execute("select has_table_privilege(%s,%s,'SELECT'),has_column_privilege(%s,%s,%s,'SELECT')",(owner,table,owner,table,column)).fetchone(),(False,False))
            self.assertFalse(c.execute("select has_column_privilege(%s,'prumo_private.cfi01_command_audit_local','recorded_at','INSERT')",(owner,)).fetchone()[0])
        self.capture()


if __name__=='__main__':
    unittest.main(verbosity=2)
