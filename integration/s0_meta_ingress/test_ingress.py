"""Physical PG17 tests: independent connections, process death, WAL recovery, loopback HTTP."""
import base64
from concurrent.futures import ThreadPoolExecutor
import copy
import hashlib
import hmac
import http.client
import json
import multiprocessing
import os
from pathlib import Path
import signal
import threading
import time
import unittest
import uuid
import psycopg
from psycopg.types.json import Jsonb
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from .ingress import Ingress
from .control import mutate
from .http_lab import serve
from .lab import Laboratory
from .protocol import (VERSION,M2M_DOMAIN,canonical,b64,digest,verify_receipt,normalize,Reject)

LAB=None

def killed_call(dsn,secrets,key_raw,wire,sig,stage,pipe):
    key=Ed25519PrivateKey.from_private_bytes(key_raw)
    def hook(at,c):
        if at==stage:
            pipe.send(at)
            os.kill(os.getpid(),signal.SIGKILL)
    Ingress(dsn,secrets,key,hook=hook).call(wire,sig)

class PhysicalTests(unittest.TestCase):
    def setUp(self):
        self.app='LAB_APP_A'
        self.meta=os.urandom(32)
        self.m2m=Ed25519PrivateKey.generate()
        self.receipt_key=Ed25519PrivateKey.generate()
        with LAB.admin() as c:
            c.execute('TRUNCATE audit,nonces,aliases,occurrences,batches,bindings,principals,routes CASCADE')
            for route,app in [('route_A',self.app),('route_B','LAB_APP_B')]:
                c.execute('INSERT INTO routes VALUES(%s,%s,1,true)',(route,app))
            c.execute("INSERT INTO principals VALUES('key_A','LAB_META_INFRA',1,%s,'route_A',%s,'tenant_A',ARRAY['append','recover'],ARRAY['channel_A','channel_A2'],true,clock_timestamp()-interval '1 hour',clock_timestamp()+interval '1 hour')",(self.m2m.public_key().public_bytes_raw(),self.app))
            for route,waba,phone,app,tenant,channel in [
                ('route_A','100001','200001',self.app,'tenant_A','channel_A'),
                ('route_A','100002','200002',self.app,'tenant_A','channel_A2'),
                ('route_A','100003','200003',self.app,'tenant_B','channel_B'),
                ('route_A','100004','200004','LAB_APP_B','tenant_A','channel_other_app'),
                ('route_B','100005','200005','LAB_APP_B','tenant_B','channel_B2')]:
                c.execute('INSERT INTO bindings VALUES(%s,%s,%s,%s,%s,%s,1,true)',(route,waba,phone,app,tenant,channel))
        self.s0=Ingress(LAB.runtime_dsn,{self.app:self.meta},self.receipt_key)

    def raw(self,channels=(('100001','200001'),),*,duplicate=False,status_first=False):
        entries=[]
        for waba,phone in channels:
            message={'id':'wamid.SYNTHETIC','from':'5500000000000','type':'text','timestamp':'1700000000','text':{'body':'SYNTHETIC ONLY'}}
            status={'id':'wamid.SYNTHETIC','recipient_id':'5500000000000','status':'delivered','timestamp':'1700000001'}
            v={'metadata':{'phone_number_id':phone},'contacts':[{'wa_id':'5500000000000'}]}
            arrays={'statuses':[status],'messages':[message,message] if duplicate else [message]} if status_first else {'messages':[message,message] if duplicate else [message],'statuses':[status]}
            v.update(arrays)
            entries.append({'id':waba,'changes':[{'field':'messages','value':v}]})
        return json.dumps({'object':'whatsapp_business_account','entry':entries},separators=(',',':')).encode()

    def packet(self,raw=None,*,ref='batch_A',scope='append',changes=None):
        raw=raw or self.raw()
        now=int(time.time()*1000)
        e={'version':VERSION,'issuer':'LAB_META_INFRA','key_id':'key_A','key_revision':'1',
           'audience':'LAB_S0_META_INGRESS','scope':scope,'app':self.app,'route':'route_A','route_revision':'1',
           'batch_ref':ref,'nonce':uuid.uuid4().hex,'issued_ms':now-100,'expires_ms':now+29000,
           'raw_base64':b64(raw),'meta_signature':'sha256='+hmac.new(self.meta,raw,hashlib.sha256).hexdigest()}
        e.update(changes or {})
        wire=canonical(e)
        return wire,b64(self.m2m.sign(M2M_DOMAIN+wire))

    def call(self,**kwargs):return self.s0.call(*self.packet(**kwargs))
    def counts(self):
        with LAB.admin() as c:
            return {t:c.execute('SELECT count(*) AS n FROM '+t).fetchone()['n'] for t in ('batches','occurrences','aliases','nonces','audit')}
    def ack(self,result,count=2):
        self.assertEqual(result['decision'],'ACK_ELIGIBLE',result)
        receipt=result['receipt']
        self.assertEqual(receipt['body']['item_count'],count)
        self.assertTrue(verify_receipt(receipt,self.receipt_key.public_key().public_bytes_raw(),{'app':self.app,'route':'route_A','route_revision':'1','raw_sha256':receipt['body']['raw_sha256']}))
        self.assertFalse(result['production_authorized'])
        self.assertFalse(result['external_http_ack'])
        return receipt
    def rejected(self,r):
        self.assertEqual(r['decision'],'REJECTED',r)
        self.assertIsNone(r['receipt'])
        self.assertEqual(self.counts()['batches'],0)

    def test_01_commit_readback_exact_bytes_and_signature(self):
        raw=self.raw()+b'\n '
        receipt=self.ack(self.call(raw=raw))
        with LAB.admin() as c:
            b=c.execute('SELECT * FROM batches').fetchone()
            self.assertEqual(bytes(b['raw']),raw)
            self.assertEqual(b['raw_sha'],digest(raw))
            self.assertEqual(c.execute('SELECT count(*) AS n FROM occurrences').fetchone()['n'],2)
        self.assertEqual(receipt['body']['raw_sha256'],digest(raw))

    def test_02_same_signed_proof_is_not_recovery(self):
        p=self.packet();self.ack(self.s0.call(*p))
        r=self.s0.call(*p)
        self.assertEqual((r['decision'],r['reason']),('REJECTED','NONCE_REPLAY'))
        self.assertEqual(self.counts()['batches'],1)

    def test_03_new_auth_recovers_same_receipt(self):
        first=self.ack(self.call())
        self.s0=Ingress(LAB.runtime_dsn,{self.app:self.meta},self.receipt_key)
        second=self.ack(self.call(scope='recover'))
        self.assertEqual(first,second)
        self.assertEqual(self.counts()['occurrences'],2)

    def test_04_same_raw_new_identifier_alias(self):
        a=self.ack(self.call());b=self.ack(self.call(ref='alias_A'))
        self.assertEqual(a,b)
        self.assertEqual(self.counts(),{'batches':1,'occurrences':2,'aliases':2,'nonces':2,'audit':2})

    def test_05_identity_conflict_durable_and_original_immutable(self):
        a=self.ack(self.call())
        r=self.call(raw=self.raw()+b' ')
        self.assertEqual(r['decision'],'CONFLICT')
        self.assertEqual(self.counts()['audit'],2)
        self.assertEqual(a,self.ack(self.call(scope='recover')))
        with LAB.admin() as c:
            self.assertEqual(c.execute("SELECT count(*) AS n FROM audit WHERE decision='CONFLICT' AND original_sha<>incoming_sha").fetchone()['n'],1)

    def test_06_physical_variant_new_identifier_preserved(self):
        a=self.ack(self.call());b=self.ack(self.call(ref='variant',raw=self.raw()+b' '))
        self.assertNotEqual(a['body']['batch_id'],b['body']['batch_id'])
        self.assertEqual(self.counts()['occurrences'],4)

    def test_07_equivalent_concurrent_connections(self):
        packets=[self.packet() for _ in range(12)]
        with ThreadPoolExecutor(max_workers=12) as pool:
            results=list(pool.map(lambda p:self.s0.call(*p),packets))
        receipts=[self.ack(r) for r in results]
        self.assertTrue(all(r==receipts[0] for r in receipts))
        self.assertEqual(self.counts()['batches'],1)
        self.assertEqual(self.counts()['nonces'],12)

    def test_08_conflicting_concurrent_connections(self):
        packets=[self.packet(raw=self.raw()+b' '*i) for i in range(1,9)]
        with ThreadPoolExecutor(max_workers=8) as pool:
            results=list(pool.map(lambda p:self.s0.call(*p),packets))
        self.assertEqual(sum(r['decision']=='ACK_ELIGIBLE' for r in results),1)
        self.assertEqual(sum(r['decision']=='CONFLICT' for r in results),7)
        self.assertEqual(self.counts()['batches'],1)
        self.assertEqual(self.counts()['audit'],8)

    def test_09_multichannel_same_app_tenant(self):
        r=self.call(raw=self.raw((('100001','200001'),('100002','200002'))))
        receipt=self.ack(r,4)
        self.assertEqual(len(receipt['body']['bindings']),2)

    def test_10_duplicate_occurrences_keep_provenance(self):
        receipt=self.ack(self.call(raw=self.raw(duplicate=True)),3)
        self.assertEqual(len(set(receipt['body']['occurrence_ids'])),3)
        with LAB.admin() as c:
            rows=c.execute('SELECT normalized FROM occurrences ORDER BY ordinal').fetchall()
            self.assertEqual(rows[0]['normalized']['item'],rows[1]['normalized']['item'])
            self.assertNotEqual(rows[0]['normalized']['item_index'],rows[1]['normalized']['item_index'])
            self.assertEqual(rows[2]['normalized']['kind'],'status_callback')
            self.assertEqual(rows[2]['normalized']['resolution'],'ARCHIVED_UNRESOLVED')

    def test_11_physical_member_array_order(self):
        self.ack(self.call(raw=self.raw(status_first=True)))
        with LAB.admin() as c:
            self.assertEqual(c.execute('SELECT normalized FROM occurrences ORDER BY ordinal').fetchone()['normalized']['kind'],'status_callback')

    def test_12_other_tenant_rejects_entire_batch(self):
        self.rejected(self.call(raw=self.raw((('100001','200001'),('100003','200003')))))
        self.assertEqual(self.counts()['nonces'],0)

    def test_13_other_app_channel_rejected(self):
        self.rejected(self.call(raw=self.raw((('100004','200004'),))))

    def test_14_unknown_channel_rejects_whole_batch(self):
        self.rejected(self.call(raw=self.raw((('100001','200001'),('999999','999999')))))

    def test_15_invalid_late_item_no_partial_commit(self):
        p=json.loads(self.raw());p['entry'][0]['changes'][0]['value']['statuses'][0].pop('id')
        self.rejected(self.call(raw=canonical(p)))
        self.assertEqual(self.counts(),dict.fromkeys(self.counts(),0))

    def test_16_unknown_subscribed_event_not_discarded(self):
        p=json.loads(self.raw());p['entry'].append({'id':'100001','changes':[{'field':'unknown','value':{}}]})
        self.rejected(self.call(raw=canonical(p)))

    def test_17_external_signature_tamper(self):
        self.rejected(self.call(changes={'meta_signature':'sha256='+'0'*64}))

    def test_18_m2m_tamper_no_boolean_bypass(self):
        wire,sig=self.packet();e=json.loads(wire);e['batch_ref']='tampered'
        self.rejected(self.s0.call(canonical(e),sig))
        self.rejected(self.call(changes={'meta_verified':True}))

    def test_19_human_jwt_and_wrong_domain(self):
        wire,_=self.packet()
        self.rejected(self.s0.call(wire,'Bearer eyJ.synthetic.human'))
        self.rejected(self.s0.call(wire,b64(self.m2m.sign(b'OTHER_DOMAIN'+wire))))

    def test_20_auth_claims_negative_matrix(self):
        for change in [{'issuer':'HUMAN'},{'key_revision':'2'},{'route_revision':'2'},
                       {'app':'LAB_APP_B'},{'route':'route_B'},{'scope':'dispatch'},
                       {'audience':'GOTRUE'},{'key_id':'unknown'},{'issued_ms':1,'expires_ms':2}]:
            with self.subTest(change=change):self.rejected(self.call(changes=change))

    def test_21_route_cas_and_revoked_key(self):
        with LAB.admin() as c:mutate(c,'route_A',1,revoke_key='key_A')
        self.rejected(self.call())
        self.rejected(self.call(changes={'route_revision':'2','key_revision':'2'}))
        with LAB.admin() as c:
            with self.assertRaises(Reject):mutate(c,'route_A',1,revoke_key='key_A')

    def test_22_revoked_credentials_cannot_replay_committed(self):
        self.ack(self.call())
        with LAB.admin() as c:mutate(c,'route_A',1,revoke_key='key_A')
        r=self.call(scope='recover',changes={'route_revision':'2','key_revision':'2'})
        self.assertEqual(r['decision'],'REJECTED')
        self.assertIsNone(r['receipt'])
        self.assertEqual(self.counts()['batches'],1)

    def test_23_route_revision_changed_binding_conflict(self):
        self.ack(self.call())
        with LAB.admin() as c:
            c.execute("UPDATE routes SET revision=2 WHERE id='route_A'")
        self.assertEqual(self.call()['decision'],'REJECTED')
        self.assertEqual(self.call(changes={'route_revision':'2'})['decision'],'CONFLICT')

    def test_24_revoke_wins_before_authorize(self):
        with LAB.admin() as c:mutate(c,'route_A',1,revoke_key='key_A')
        self.rejected(self.call())

    def test_25_ingress_wins_revocation_waits_for_commit(self):
        authorized=threading.Event();release=threading.Event();done=threading.Event()
        def hook(stage,c):
            if stage=='authorized':authorized.set();self.assertTrue(release.wait(5))
        self.s0.hook=hook
        with ThreadPoolExecutor(max_workers=2) as pool:
            future=pool.submit(self.call)
            self.assertTrue(authorized.wait(5))
            def revoke():
                with LAB.admin() as c:mutate(c,'route_A',1,revoke_key='key_A')
                done.set()
            rev=pool.submit(revoke)
            # Observe a real waiter instead of assuming elapsed time proves a lock.
            deadline=time.monotonic()+4;blocked=False
            while time.monotonic()<deadline:
                with LAB.admin() as c:
                    blocked=c.execute("SELECT EXISTS(SELECT 1 FROM pg_stat_activity WHERE datname=current_database() AND wait_event_type='Lock' AND query LIKE 'SELECT revision FROM s0_meta_lab.routes%') AS yes").fetchone()['yes']
                if blocked:break
                time.sleep(.02)
            self.assertTrue(blocked);self.assertFalse(done.is_set());release.set()
            r=future.result();rev.result()
        self.assertIn(r['decision'],('ACK_ELIGIBLE','REJECTED')) # fresh readback may observe revocation
        self.assertEqual(self.counts()['batches'],1)
        self.assertEqual(self.call(scope='recover')['decision'],'REJECTED')

    def test_26_disabled_binding_and_expired_key(self):
        with LAB.admin() as c:mutate(c,'route_A',1,disable_binding='channel_A')
        self.rejected(self.call(changes={'route_revision':'2'}))
        with LAB.admin() as c:c.execute("UPDATE principals SET not_after=clock_timestamp()-interval '1 second' WHERE key_id='key_A'")
        self.rejected(self.call(changes={'route_revision':'2'}))

    def test_27_failure_each_write_stage_rolls_back(self):
        for stage in ('nonce','batch','item','before_commit'):
            with self.subTest(stage=stage):
                def hook(at,c):
                    if at==stage:raise RuntimeError('synthetic late failure')
                self.s0.hook=hook
                r=self.call()
                self.assertEqual(r['decision'],'PENDING_RECONCILIATION')
                self.assertEqual(self.counts(),dict.fromkeys(self.counts(),0))
        self.s0.hook=lambda *_:None;self.ack(self.call())

    def test_28_process_sigkill_transaction_and_receipt_windows(self):
        ctx=multiprocessing.get_context('spawn')
        for stage in ('nonce','batch','item','before_commit','after_commit','readback','before_sign','after_sign'):
            with self.subTest(stage=stage):
                self.setUp()
                wire,sig=self.packet();parent,child=ctx.Pipe()
                p=ctx.Process(target=killed_call,args=(LAB.runtime_dsn,{self.app:self.meta},self.receipt_key.private_bytes_raw(),wire,sig,stage,child))
                p.start();self.assertTrue(parent.poll(12));self.assertEqual(parent.recv(),stage)
                p.join(5);self.assertEqual(p.exitcode,-signal.SIGKILL)
                committed=stage in ('after_commit','readback','before_sign','after_sign')
                self.assertEqual(self.counts()['batches'],int(committed))
                r=self.call(scope='recover')
                if committed:self.ack(r)
                else:
                    self.assertEqual(r['decision'],'PENDING_RECONCILIATION')
                    self.ack(self.call())
                self.assertEqual(self.counts()['batches'],1)
                parent.close();child.close()

    def test_29_commit_response_lost_recovery(self):
        def fail(at,c):
            if at=='after_commit':raise OSError('lost response')
        self.s0.hook=fail
        self.assertEqual(self.call()['decision'],'PENDING_RECONCILIATION')
        self.assertEqual(self.counts()['batches'],1)
        self.s0.hook=lambda *_:None
        self.ack(self.call(scope='recover'))

    def test_30_database_sigkill_wal_restart(self):
        first=self.ack(self.call())
        # An uncommitted real transaction writes a second nonce and must disappear after crash.
        c=psycopg.connect(LAB.runtime_dsn,options='-c search_path=s0_meta_lab,pg_catalog')
        c.execute("INSERT INTO nonces(key_id,nonce,envelope_sha) VALUES('key_A','UNCOMMITTED',%s)",('a'*64,))
        LAB.crash_restart()
        c.close()
        self.assertEqual(self.counts()['nonces'],1)
        self.assertEqual(first,self.ack(self.call(scope='recover')))
        self.assertEqual(self.counts()['batches'],1)

    def test_31_corrupt_partial_storage_never_ack(self):
        self.ack(self.call())
        with LAB.admin() as c:c.execute('DELETE FROM occurrences WHERE ordinal=1')
        self.assertEqual(self.call(scope='recover')['decision'],'PENDING_RECONCILIATION')

    def test_32_receipt_tampering_wrong_key_wrong_context(self):
        r=self.ack(self.call());pub=self.receipt_key.public_key().public_bytes_raw()
        self.assertFalse(verify_receipt(r,pub,{'app':'LAB_APP_B'}))
        self.assertFalse(verify_receipt(r,Ed25519PrivateKey.generate().public_key().public_bytes_raw(),{}))
        for field,value in [('item_count',999),('state','UNKNOWN'),('raw_sha256','0'*64),('audit_id','fake')]:
            forged=copy.deepcopy(r);forged['body'][field]=value
            self.assertFalse(verify_receipt(forged,pub,{}))

    def test_33_missing_receipt_key_state_uncertain(self):
        self.ack(self.call())
        self.s0.receipt_key_id='LAB_RECEIPT_2'
        self.assertEqual(self.call(scope='recover')['decision'],'PENDING_RECONCILIATION')

    def test_34_runtime_acl_and_registry_locks_no_mutation(self):
        self.ack(self.call())
        bad=["UPDATE routes SET id=id","UPDATE principals SET key_id=key_id",'UPDATE bindings SET route=route',
             'DELETE FROM batches','UPDATE occurrences SET ordinal=ordinal',
             'CREATE TABLE public.forbidden(id int)','CREATE TABLE s0_meta_lab.forbidden(id int)',
             'SET ROLE s0_meta_owner',"UPDATE principals SET active=false",'ALTER ROLE s0_meta_runtime SUPERUSER']
        for query in bad:
            with self.subTest(query=query):
                with self.assertRaises(psycopg.Error):
                    with self.s0.connect() as c:c.execute(query)
        with self.s0.connect() as c:
            self.assertEqual(c.execute("SELECT rolbypassrls,rolsuper FROM pg_roles WHERE rolname=current_user").fetchone(),{'rolbypassrls':False,'rolsuper':False})

    def test_35_body_limits_duplicate_keys_and_utf8(self):
        for raw in [b'\xff',b'{"object":"x","object":"whatsapp_business_account"}',b'x'*262145]:
            with self.subTest(kind=len(raw)):self.rejected(self.call(raw=raw))
        p=json.loads(self.raw());p['entry'][0]['changes'][0]['value']['statuses']*=101
        self.rejected(self.call(raw=canonical(p)))

    def test_36_unavailable_dependency_never_ack(self):
        self.s0.dsn='host=127.0.0.1 port=1 dbname=s0_meta_ingress_lab user=s0_meta_runtime connect_timeout=1'
        r=self.call();self.assertEqual(r['decision'],'UNAVAILABLE');self.assertIsNone(r['receipt'])

    def test_37_http_local_technical_decision_and_lost_response(self):
        for drop in (False,True):
            server=serve(self.s0,drop_response=drop)
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            wire,sig=self.packet(ref='http_A')
            client=http.client.HTTPConnection(*server.server_address,timeout=5)
            try:
                client.request('POST','/lab/ingress',canonical({'envelope':b64(wire),'signature':sig}),{'Content-Type':'application/json'})
                if drop:
                    with self.assertRaises(http.client.RemoteDisconnected):client.getresponse()
                else:
                    response=client.getresponse();self.assertEqual(response.status,207)
                    self.assertEqual(response.getheader('X-Prumo-Laboratory-Only'),'true')
                    self.ack(json.loads(response.read()))
            finally:
                client.close();server.shutdown();server.server_close();thread.join(5)
        self.ack(self.call(ref='http_A',scope='recover'))
        self.assertEqual(self.counts()['batches'],1)

    def test_38_recovery_absent_does_not_create_batch(self):
        self.assertEqual(self.call(scope='recover')['decision'],'PENDING_RECONCILIATION')
        self.assertEqual(self.counts()['batches'],0)

    def test_39_concurrent_same_nonce_one_winner(self):
        p=self.packet()
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(lambda _:self.s0.call(*p),range(2)))
        self.assertEqual(sorted(r['decision'] for r in results),['ACK_ELIGIBLE','REJECTED'])
        self.assertEqual(self.counts()['nonces'],1)

    def test_40_signature_expiration_after_wait(self):
        wire,sig=self.packet(changes={'issued_ms':int(time.time()*1000)-100,'expires_ms':int(time.time()*1000)+500})
        with LAB.admin() as c:
            c.execute("SELECT * FROM routes WHERE id='route_A' FOR UPDATE")
            with ThreadPoolExecutor(max_workers=1) as pool:
                f=pool.submit(self.s0.call,wire,sig)
                time.sleep(.7);c.commit()
                self.rejected(f.result())

    def test_41_no_success_without_wal_guarantees(self):
        original=self.s0.connect
        def connect():
            c=original();c.execute('SET synchronous_commit=off');c.commit();return c
        self.s0.connect=connect
        # Runtime explicitly overrides session preference with LOCAL synchronous_commit=on.
        self.ack(self.call())

    def test_42_binding_revision_changed_conflicts_without_duplicate(self):
        self.ack(self.call())
        with LAB.admin() as c:c.execute("UPDATE bindings SET revision=2 WHERE channel='channel_A'")
        self.assertEqual(self.call()['decision'],'CONFLICT')
        self.assertEqual(self.counts()['batches'],1)


    def test_43_m2m_rotation_new_key_recovers_original_receipt(self):
        first=self.ack(self.call())
        successor=Ed25519PrivateKey.generate()
        with LAB.admin() as c:
            mutate(c,'route_A',1,revoke_key='key_A')
            c.execute("INSERT INTO principals SELECT 'key_A2',issuer,1,%s,route,app,tenant,scopes,channels,true,not_before,not_after FROM principals WHERE key_id='key_A'",(successor.public_key().public_bytes_raw(),))
        self.m2m=successor
        second=self.ack(self.call(scope='recover',changes={'key_id':'key_A2'}))
        self.assertEqual(first,second)
        self.assertEqual(self.counts()['batches'],1)

    def test_44_receipt_same_id_wrong_private_key_uncertain(self):
        self.ack(self.call())
        self.s0.receipt_key=Ed25519PrivateKey.generate()
        self.assertEqual(self.call(scope='recover')['decision'],'PENDING_RECONCILIATION')

    def test_45_unknown_event_array_not_silently_discarded(self):
        p=json.loads(self.raw());p['entry'][0]['changes'][0]['value']['new_events']=[{'id':'unknown'}]
        self.rejected(self.call(raw=canonical(p)))

    def test_46_binding_change_waits_on_ingress_fence(self):
        ready=threading.Event();release=threading.Event();changed=threading.Event()
        def hook(stage,c):
            if stage=='authorized':ready.set();self.assertTrue(release.wait(5))
        self.s0.hook=hook
        with ThreadPoolExecutor(max_workers=2) as pool:
            f=pool.submit(self.call)
            self.assertTrue(ready.wait(5))
            def change():
                with LAB.admin() as c:mutate(c,'route_A',1,disable_binding='channel_A')
                changed.set()
            future=pool.submit(change)
            deadline=time.monotonic()+4;blocked=False
            while time.monotonic()<deadline:
                with LAB.admin() as c:
                    blocked=c.execute("SELECT EXISTS(SELECT 1 FROM pg_stat_activity WHERE datname=current_database() AND wait_event_type='Lock' AND query LIKE 'SELECT revision FROM s0_meta_lab.routes%') AS yes").fetchone()['yes']
                if blocked:break
                time.sleep(.02)
            self.assertTrue(blocked);self.assertFalse(changed.is_set());release.set()
            self.assertIn(f.result()['decision'],('ACK_ELIGIBLE','REJECTED'));future.result()
        self.assertEqual(self.counts()['batches'],1)
        self.assertEqual(self.call(scope='recover',changes={'route_revision':'2'})['decision'],'REJECTED')

    def test_47_reversed_multichannel_order_no_lock_inversion(self):
        a=self.packet(raw=self.raw((('100001','200001'),('100002','200002'))),ref='forward')
        b=self.packet(raw=self.raw((('100002','200002'),('100001','200001'))),ref='reverse')
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(lambda p:self.s0.call(*p),(a,b)))
        for r in results:self.ack(r,4)
        self.assertEqual(self.counts()['batches'],2)

    def test_48_installer_guards_and_atomic_reinstall(self):
        with self.assertRaises(psycopg.Error):
            with LAB.admin() as c:c.execute(Path('integration/s0_meta_ingress/schema.sql').read_text())
        with self.assertRaises(psycopg.Error):
            with LAB.admin() as c:
                c.execute("SET s0_meta.disposable='YES'")
                c.execute(Path('integration/s0_meta_ingress/schema.sql').read_text())
        self.ack(self.call())
        with LAB.admin() as c:self.assertEqual(LAB.catalog_before,LAB.catalog(c))

    def test_49_same_app_tenant_channel_without_explicit_grant(self):
        with LAB.admin() as c:
            c.execute("INSERT INTO bindings VALUES('route_A','100006','200006',%s,'tenant_A','channel_A3',1,true)",(self.app,))
        self.rejected(self.call(raw=self.raw((('100001','200001'),('100006','200006')))))
        self.assertEqual(self.counts()['nonces'],0)

def main():
    global LAB
    LAB=Laboratory()
    report={'classification':'S0_META_INGRESS_01_LAB_BLOCKED'}
    result=None
    try:
        LAB.start()
        report['postgres']=LAB.pg
        suite=unittest.defaultTestLoader.loadTestsFromTestCase(PhysicalTests)
        result=unittest.TextTestRunner(verbosity=2).run(suite)
        report.update(tests_run=result.testsRun,failures=len(result.failures),errors=len(result.errors),skips=len(result.skipped))
    finally:
        report['cleanup']=LAB.cleanup()
        if result and result.wasSuccessful() and not result.skipped and all(report['cleanup'].values()):
            report['classification']='S0_META_INGRESS_01_LAB_CLOSED'
        destination=Path(os.environ.get('S0_META_REPORT','/tmp/s0-meta-ingress-report.json'))
        destination.write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report,indent=2))
    raise SystemExit(0 if report['classification']=='S0_META_INGRESS_01_LAB_CLOSED' else 1)

if __name__=='__main__':main()
