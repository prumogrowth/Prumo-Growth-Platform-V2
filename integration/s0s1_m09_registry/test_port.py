import unittest
from dataclasses import replace
from threading import Barrier, Thread

from .port import (App, Channel, HostScope, M2MPrincipal, RegistryLab,
                   RegistryPort, Revisions, SCHEMA, FLAGS)


def fixture():
    p = M2MPrincipal('service-1', 'issuer-1', 'LAB_S0_M09', 1,
                     frozenset({'store-1'}), frozenset({
                         'REGISTRY_READ','GET_VERIFY_TOKEN','POST_APP_SECRET',
                         'GRAPH_ACCESS_TOKEN'}), True)
    apps = (App('app-1','route-1','store-1','tenant-1',1,1,1,0,10000,
                (('GET_VERIFY_TOKEN','GET_SLOT_A'),('POST_APP_SECRET','POST_SLOT_A'),
                 ('GRAPH_ACCESS_TOKEN','GRAPH_SLOT_A')),
                (Channel('channel-1','waba-1','12345678',1,1),
                 Channel('channel-2','waba-2','23456789',1,1))),
            App('app-2','route-2','store-2','tenant-2',1,1,1,0,10000,
                (('GET_VERIFY_TOKEN','GET_SLOT_B'),('POST_APP_SECRET','POST_SLOT_B'),
                 ('GRAPH_ACCESS_TOKEN','GRAPH_SLOT_B')),
                (Channel('channel-3','waba-3','34567890',1,1),)))
    registry = RegistryLab(apps, {'tenant-1':'store-1','tenant-2':'store-2'})
    scopes = {'route': HostScope('route-1','store-1','app-1'),
              'channel': HostScope('route-1','store-1','app-1',
                                   'channel-1','waba-1','12345678'),
              'channel2': HostScope('route-1','store-1','app-1',
                                   'channel-2','waba-2','23456789'),
              'other': HostScope('route-2','store-2','app-2',
                                 'channel-3','waba-3','34567890')}
    verifier = lambda proof: p if proof == 'SYNTHETIC_PROOF_OK' else None
    router = lambda ref: scopes.get(ref)
    service = RegistryPort(registry, verifier, router, lambda: 100)
    return registry, service, scopes, p, apps


class TestM09(unittest.TestCase):
    def setUp(self):
        self.registry, self.service, self.scopes, self.p, self.apps = fixture()

    def read(self, ref='channel', purpose='REGISTRY_READ', **kw):
        return self.service.read(proof='SYNTHETIC_PROOF_OK', host_ref=ref,
                                 purpose=purpose, **kw)

    def assertDenied(self, result):
        self.assertNotEqual(result['decision'], 'SNAPSHOT_CANDIDATE_ONLY')
        self.assertIsNone(result['snapshot'])
        self.assertTrue(all(result[k] is False for k in FLAGS))

    def test_positive_snapshot_and_separate_revisions(self):
        x = self.read()
        self.assertEqual(x['schema'], SCHEMA)
        self.assertEqual(x['decision'],'SNAPSHOT_CANDIDATE_ONLY')
        self.assertEqual(x['snapshot']['revisions'],
                         dict(route=1,app=1,binding=1,grant=1,principal=1))
        self.assertNotIn('slot_ref',x['snapshot'])
        self.assertEqual(x['snapshot']['ownership_evidence_state'],'UNVERIFIED')

    def test_two_wabas_same_store(self):
        self.assertEqual(self.read('channel2')['snapshot']['waba_id'], 'waba-2')

    def test_route_purposes_are_not_channel_grants(self):
        a = self.read('route', 'GET_VERIFY_TOKEN')
        self.assertEqual(a['snapshot']['canal_id'], None)
        self.assertEqual(a['snapshot']['slot_ref'], 'GET_SLOT_A')
        b = self.read('route', 'POST_APP_SECRET')
        self.assertEqual(b['snapshot']['slot_ref'], 'POST_SLOT_A')
        self.assertDenied(self.read('route','GRAPH_ACCESS_TOKEN'))

    def test_graph_slot_one_purpose_only(self):
        x = self.read('channel', 'GRAPH_ACCESS_TOKEN')['snapshot']
        self.assertEqual(x['slot_ref'],'GRAPH_SLOT_A')
        self.assertNotIn('slots',x)
        self.assertNotIn('secret',x)

    def test_unprivileged_gets_no_slot(self):
        base = self.p
        self.service._verify_m2m = lambda proof: replace(base, privileged_slot_reader=False)
        self.assertNotIn('slot_ref', self.read('route','POST_APP_SECRET')['snapshot'])

    def test_wrong_proof_and_nonexistent_host_ref(self):
        self.assertDenied(self.service.read(proof='BAD',host_ref='channel',purpose='REGISTRY_READ'))
        self.assertDenied(self.read('attacker-selected-route'))

    def test_cross_store(self):
        self.assertDenied(self.read('other'))

    def test_host_cross_scope(self):
        self.scopes['channel'] = HostScope('route-1','store-2','app-1','channel-1','waba-1','12345678')
        self.assertDenied(self.read())

    def test_forged_channel(self):
        self.scopes['channel'] = HostScope('route-1','store-1','app-1','forged','waba-1','12345678')
        self.assertDenied(self.read())

    def test_host_phone_swap(self):
        self.scopes['channel'] = HostScope('route-1','store-1','app-1','channel-1','waba-1','23456789')
        self.assertDenied(self.read())

    def test_claims_do_not_override_host(self):
        self.assertDenied(self.service.read(proof={'route_ref':'route-1','admin':True},
                                            host_ref='channel',purpose='REGISTRY_READ'))

    def test_stale_expected_versions(self):
        bad = Revisions(1,1,1,2,1)
        self.assertDenied(self.read(expected=bad))
        self.assertEqual(self.read(expected=bad)['decision'],'STALE_OR_REVOKED')

    def test_snapshot_is_stable_without_clock(self):
        a,b = self.read(),self.read()
        self.assertEqual(a['snapshot']['snapshot_ref'], b['snapshot']['snapshot_ref'])
        self.assertEqual(self.read(previous_snapshot_ref=a['snapshot']['snapshot_ref'])['decision'],
                         'SNAPSHOT_CANDIDATE_ONLY')

    def test_snapshot_ref_binds_purpose_and_principal(self):
        x = self.read('channel', 'REGISTRY_READ')['snapshot']['snapshot_ref']
        self.assertEqual(self.read('channel', 'GRAPH_ACCESS_TOKEN',
                                   previous_snapshot_ref=x)['decision'], 'STALE_OR_REVOKED')
        p = self.p
        self.service._verify_m2m = lambda _: replace(p, principal_ref='other-principal')
        self.assertEqual(self.read(previous_snapshot_ref=x)['decision'], 'STALE_OR_REVOKED')

    def test_bad_snapshot_ref_denied(self):
        self.assertDenied(self.read(previous_snapshot_ref='x'))
        self.assertDenied(self.read(previous_snapshot_ref='0'*64))

    def test_revoke_cas_and_stale_snapshot(self):
        x = self.read()['snapshot']
        version = Revisions(**x['revisions'])
        self.assertEqual(self.registry.revoke_channel('route-1','channel-1',version),
                         'REVOKED_LAB_ONLY')
        self.assertDenied(self.read(previous_snapshot_ref=x['snapshot_ref']))
        self.assertEqual(self.registry.revoke_channel('route-1','channel-1',version),'CONFLICT')
        self.assertEqual(self.read('channel2')['snapshot']['revisions']['route'],2)

    def test_revoked_channel_cannot_leak_metadata(self):
        version = Revisions(1,1,1,1,1)
        self.registry.revoke_channel('route-1','channel-1',version)
        x = self.read()
        self.assertEqual(x['reason'],'NOT_AUTHORIZED')
        self.assertIsNone(x['snapshot'])

    def test_grant_revoked_in_fixture(self):
        a = self.apps[0]
        self.registry._apps = (replace(a, channels=(replace(a.channels[0], grant_active=False), a.channels[1])),self.apps[1])
        self.assertDenied(self.read())

    def test_tenant_map_must_be_explicit(self):
        self.registry._tenant_to_store.clear()
        self.assertDenied(self.read())

    def test_global_waba_ownership(self):
        a,b = self.apps
        self.registry._apps = (a, replace(b, channels=(replace(b.channels[0], waba_id='waba-1'),)))
        self.assertDenied(self.read())

    def test_global_phone_duplicate(self):
        a,b = self.apps
        self.registry._apps = (a,replace(b, channels=(replace(b.channels[0],phone_number_id='12345678'),)))
        self.assertDenied(self.read())

    def test_global_channel_duplicate(self):
        a,b = self.apps
        self.registry._apps = (a,replace(b, channels=(replace(b.channels[0],canal_id='channel-1'),)))
        self.assertDenied(self.read())

    def test_slot_alias_same_app_denied(self):
        a,b = self.apps
        self.registry._apps = (replace(a, slots=(('GET_VERIFY_TOKEN','SAME_SLOT'),
                  ('POST_APP_SECRET','SAME_SLOT'),('GRAPH_ACCESS_TOKEN','THIRD_SLOT'))),b)
        self.assertDenied(self.read())

    def test_slot_alias_between_apps_denied(self):
        a,b = self.apps
        self.registry._apps = (a, replace(b,slots=(('GET_VERIFY_TOKEN','GET_SLOT_A'),
                   ('POST_APP_SECRET','POST_SLOT_B'),('GRAPH_ACCESS_TOKEN','GRAPH_SLOT_B'))))
        self.assertDenied(self.read())

    def test_no_supabase_slot(self):
        a,b = self.apps
        self.registry._apps = (replace(a,slots=(('GET_VERIFY_TOKEN','SUPABASE_TOKEN'),
                   ('POST_APP_SECRET','POST_SLOT_A'),('GRAPH_ACCESS_TOKEN','GRAPH_SLOT_A'))),b)
        self.assertDenied(self.read())

    def test_expired_route(self):
        a,b = self.apps
        self.registry._apps = (replace(a,valid_until_ms=50), b)
        self.assertDenied(self.read())

    def test_principal_revision_and_audience(self):
        p=self.p
        self.service._verify_m2m = lambda proof: replace(p,key_revision=2)
        self.assertDenied(self.read())
        self.service._verify_m2m = lambda proof: replace(p,audience='PROD')
        self.assertDenied(self.read())

    def test_purpose_restricted(self):
        p=self.p
        self.service._verify_m2m = lambda proof: replace(p, allowed_purposes=frozenset({'REGISTRY_READ'}))
        self.assertDenied(self.read('route','POST_APP_SECRET'))

    def test_verifier_failure_is_unavailable(self):
        def fail(_): raise RuntimeError('SECRET SHOULD NOT LEAK')
        self.service._verify_m2m = fail
        x=self.read()
        self.assertEqual(x['decision'],'UNAVAILABLE')
        self.assertNotIn('SECRET',str(x))

    def test_invalid_future_typed_purpose(self):
        self.assertDenied(self.read(purpose='FUTURE_PURPOSE'))
        self.assertDenied(self.read(purpose=None))

    def test_concurrent_cas_single_winner(self):
        fence=Barrier(3)
        results=[]
        def job():
            fence.wait()
            results.append(self.registry.revoke_channel('route-1','channel-1',Revisions(1,1,1,1,1)))
        a,b=Thread(target=job),Thread(target=job)
        a.start();b.start();fence.wait();a.join();b.join()
        self.assertCountEqual(results,['REVOKED_LAB_ONLY','CONFLICT'])

    def test_reply_never_authorizes_commercial_or_transport(self):
        for x in [self.read(), self.read('route','POST_APP_SECRET'),
                  self.read('channel','GRAPH_ACCESS_TOKEN'), self.read('other')]:
            self.assertTrue(all(x[key] is False for key in FLAGS))

if __name__=='__main__':
    unittest.main()
