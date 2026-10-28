"""Trusted internal LAB runtime. Never a Meta HTTP listener or a business dispatcher."""
import uuid
import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from .protocol import (Reject, canonical, digest, decode_envelope, verify_m2m,
                       verify_meta, normalize, RECEIPT_DOMAIN, b64)

class Ingress:
    def __init__(self, dsn, app_secrets, receipt_key, *, instance='LAB_S0_01',
                 receipt_key_id='LAB_RECEIPT_1', receipt_revision=1, hook=None):
        self.dsn, self.app_secrets, self.receipt_key = dsn, app_secrets, receipt_key
        self.instance, self.receipt_key_id, self.receipt_revision = instance, receipt_key_id, receipt_revision
        self.hook = hook or (lambda stage, connection: None)

    def connect(self):
        return psycopg.connect(self.dsn, row_factory=dict_row, connect_timeout=3,
                               options='-c search_path=s0_meta_lab,pg_catalog -c statement_timeout=8000 -c lock_timeout=5000')

    @staticmethod
    def result(state, reason, receipt=None):
        return {'decision': state, 'reason': reason, 'receipt': receipt,
                'production_authorized': False, 'send_authorized': False,
                'commercial_transition_authorized': False, 'external_http_ack': False}

    def _authorize(self, c, e, wire, signature, items):
        # All paths: route SHARE -> principal SHARE -> bindings sorted SHARE.
        route = c.execute('SELECT * FROM routes WHERE id=%s FOR SHARE', (e['route'],)).fetchone()
        key = c.execute('SELECT * FROM principals WHERE key_id=%s FOR SHARE', (e['key_id'],)).fetchone()
        if not route or not key:
            raise Reject('TECHNICAL_IDENTITY')
        if not route['active'] or route['app'] != e['app'] or str(route['revision']) != e['route_revision']:
            raise Reject('ROUTE_STALE_OR_REVOKED')
        if (not key['active'] or key['issuer'] != e['issuer'] or str(key['revision']) != e['key_revision']
            or key['route'] != e['route'] or key['app'] != e['app'] or e['scope'] not in key['scopes']):
            raise Reject('TECHNICAL_AUTHORIZATION')
        verify_m2m(key['public_key'], wire, signature)
        snapshot = []
        for waba, phone in sorted({(i['waba'], i['phone']) for i in items}):
            b = c.execute('SELECT * FROM bindings WHERE route=%s AND waba=%s AND phone=%s FOR SHARE',
                          (e['route'], waba, phone)).fetchone()
            if not b or not b['active'] or b['app'] != e['app'] or b['tenant'] != key['tenant']:
                raise Reject('CHANNEL_BINDING')
            snapshot.append({**b, 'revision': str(b['revision'])})
        # Recheck DB clock after all waits. No client clock decides authorization.
        now = c.execute('SELECT clock_timestamp() AS now').fetchone()['now']
        ms = int(now.timestamp()*1000)
        if not key['not_before'] <= now < key['not_after'] or not e['issued_ms'] <= ms < e['expires_ms']:
            raise Reject('AUTH_EXPIRED')
        return snapshot

    def call(self, wire, signature):
        try:
            e, raw = decode_envelope(wire)
            # Parse is bounded, and grants nothing; authoritative checks occur under locks.
            items = normalize(raw)
            secret = self.app_secrets.get(e['app'])
            if not secret:
                raise Reject('APP_NOT_CONFIGURED')
            verify_meta(raw, e['meta_signature'], secret)
        except Reject as ex:
            return self.result('REJECTED', ex.reason)
        except (ValueError, TypeError, UnicodeError, RecursionError):
            return self.result('REJECTED', 'INVALID_WIRE')
        touched = False
        try:
            with self.connect() as c:
                c.execute('SET LOCAL synchronous_commit=on')
                settings = c.execute("SELECT current_setting('fsync') AS fsync, current_setting('full_page_writes') AS fpw, current_setting('server_version_num')::int AS version").fetchone()
                if settings['fsync'] != 'on' or settings['fpw'] != 'on' or settings['version']//10000 != 17:
                    return self.result('UNAVAILABLE', 'UNPROVEN_WAL_CONFIGURATION')
                self.hook('before_authorize', c)
                snapshot = self._authorize(c, e, wire, signature, items)
                self.hook('authorized', c)
                # Exclusive transaction lock is namespaced and route scoped, never shared S0/S1.
                c.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s, 731001))", ('s0_meta_ingress_lab:'+e['route'],))
                # A queue wait must not extend the signature lifetime.
                self._authorize(c, e, wire, signature, items)
                touched = True
                c.execute('INSERT INTO nonces(key_id,nonce,envelope_sha) VALUES(%s,%s,%s)',
                          (e['key_id'], e['nonce'], digest(wire)))
                self.hook('nonce', c)
                alias = c.execute('SELECT b.* FROM aliases a JOIN batches b ON b.id=a.batch_id WHERE a.route=%s AND a.ref=%s',
                                  (e['route'], e['batch_ref'])).fetchone()
                batch = alias or c.execute('SELECT * FROM batches WHERE route=%s AND raw_sha=%s',
                                           (e['route'], digest(raw))).fetchone()
                audit_id = uuid.uuid4()
                if batch and (batch['raw_sha'] != digest(raw) or batch['route_revision'] != int(e['route_revision'])
                              or batch['binding_sha'] != digest(canonical(snapshot))):
                    c.execute('INSERT INTO audit(id,key_id,nonce,decision,batch_id,incoming_sha,original_sha) VALUES(%s,%s,%s,%s,%s,%s,%s)',
                              (audit_id,e['key_id'],e['nonce'],'CONFLICT',batch['id'],digest(raw),batch['raw_sha']))
                    result = self.result('CONFLICT', 'IMMUTABLE_IDENTITY_OR_BINDING')
                elif not batch and e['scope'] == 'recover':
                    c.execute('INSERT INTO audit(id,key_id,nonce,decision,incoming_sha) VALUES(%s,%s,%s,%s,%s)',
                              (audit_id,e['key_id'],e['nonce'],'PENDING_RECONCILIATION',digest(raw)))
                    result = self.result('PENDING_RECONCILIATION', 'NO_COMMITTED_RECORD')
                else:
                    if not batch:
                        batch_id = uuid.uuid4()
                        c.execute('''INSERT INTO batches(id,route,app,route_revision,raw,raw_sha,item_count,items_sha,
                          binding_snapshot,binding_sha,issuer,m2m_key,m2m_revision,receipt_key,receipt_revision,receipt_public,instance,audit_id)
                          VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
                          (batch_id,e['route'],e['app'],int(e['route_revision']),raw,digest(raw),len(items),digest(canonical(items)),
                           Jsonb(snapshot),digest(canonical(snapshot)),e['issuer'],e['key_id'],int(e['key_revision']),
                           self.receipt_key_id,self.receipt_revision,self.receipt_key.public_key().public_bytes_raw(),self.instance,audit_id))
                        self.hook('batch', c)
                        for i in items:
                            c.execute('INSERT INTO occurrences(id,batch_id,ordinal,normalized) VALUES(%s,%s,%s,%s)',
                                      (uuid.uuid4(),batch_id,i['ordinal'],Jsonb(i)))
                            self.hook('item', c)
                    else:
                        batch_id = batch['id']
                    if not alias and e['scope'] == 'append':
                        c.execute('INSERT INTO aliases(route,ref,batch_id) VALUES(%s,%s,%s)', (e['route'],e['batch_ref'],batch_id))
                    c.execute('INSERT INTO audit(id,key_id,nonce,decision,batch_id,incoming_sha) VALUES(%s,%s,%s,%s,%s,%s)',
                              (audit_id,e['key_id'],e['nonce'],'COMPLETE_TRANSACTION',batch_id,digest(raw)))
                    self._material(c, batch_id)  # Validate entire persisted result before commit too.
                    result = None
                self.hook('before_commit', c)
            self.hook('after_commit', None)
            if result:
                return result
            # New connection/transaction; no success based on memory or commit acknowledgement alone.
            with self.connect() as c:
                live_snapshot = self._authorize(c,e,wire,signature,items)
                body = self._material(c,batch_id)
                if body['raw_sha256'] != digest(raw) or body['binding_sha256'] != digest(canonical(live_snapshot)):
                    raise Reject('READBACK_CONTEXT')
                self.hook('readback', c)
            if (body['instance'] != self.instance or body['receipt_key_id'] != self.receipt_key_id
                or body['receipt_key_revision'] != str(self.receipt_revision)
                or body['receipt_public_key'] != b64(self.receipt_key.public_key().public_bytes_raw())):
                return self.result('PENDING_RECONCILIATION','RECEIPT_KEY_UNAVAILABLE')
            self.hook('before_sign', None)
            receipt = {'body':body,'signature':b64(self.receipt_key.sign(RECEIPT_DOMAIN+canonical(body)))}
            self.hook('after_sign', None)
            return self.result('ACK_ELIGIBLE','COMPLETE_READBACK_PROVED',receipt)
        except Reject as ex:
            return self.result('REJECTED', ex.reason)
        except psycopg.errors.UniqueViolation:
            return self.result('REJECTED','NONCE_REPLAY')
        except Exception:
            # No exception text, SQL parameters, raw bytes or secrets escape this boundary.
            return self.result('PENDING_RECONCILIATION' if touched else 'UNAVAILABLE','RESULT_UNPROVEN')

    @staticmethod
    def _material(c, batch_id):
        b = c.execute('SELECT * FROM batches WHERE id=%s',(batch_id,)).fetchone()
        rows = c.execute('SELECT * FROM occurrences WHERE batch_id=%s ORDER BY ordinal',(batch_id,)).fetchall()
        if not b:
            raise RuntimeError('incomplete')
        items = [r['normalized'] for r in rows]
        if (len(rows) != b['item_count'] or [r['ordinal'] for r in rows] != list(range(b['item_count']))
            or digest(bytes(b['raw'])) != b['raw_sha'] or normalize(bytes(b['raw'])) != items
            or digest(canonical(items)) != b['items_sha'] or digest(canonical(b['binding_snapshot'])) != b['binding_sha']
            or not c.execute('SELECT 1 FROM audit WHERE id=%s AND batch_id=%s AND decision=%s',
                             (b['audit_id'],b['id'],'COMPLETE_TRANSACTION')).fetchone()):
            raise RuntimeError('incomplete')
        return {'version':'prumo.s0-meta-ingress.receipt.lab/1-candidate','instance':b['instance'],
                'app':b['app'],'route':b['route'],'route_revision':str(b['route_revision']),
                'batch_id':str(b['id']),'raw_sha256':b['raw_sha'],'item_count':len(rows),
                'occurrence_ids':[str(r['id']) for r in rows],'items_sha256':b['items_sha'],
                'binding_sha256':b['binding_sha'],'bindings':b['binding_snapshot'],
                'm2m_issuer':b['issuer'],'m2m_key_id':b['m2m_key'],'m2m_key_revision':str(b['m2m_revision']),
                'receipt_key_id':b['receipt_key'],'receipt_key_revision':str(b['receipt_revision']),
                'receipt_public_key':b64(bytes(b['receipt_public'])),
                'audit_id':str(b['audit_id']),'recorded_at':b['committed_at'].isoformat(),
                'state':'DURABLY_COMMITTED','durability_profile':'PG17_LOCAL_WAL_FSYNC_ON_SYNC_COMMIT_ON',
                'production_authorized':False,'commercial_transition_authorized':False}
