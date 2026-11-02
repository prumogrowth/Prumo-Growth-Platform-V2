"""S0 G2: coherent, strictly historical PG17 readback classification.

This is a laboratory proof of a consistent PostgreSQL MVCC snapshot, NOT
a lease, attestation, current-time permission, send decision or a hosted API.
All live-source writes may occur AFTER the snapshot; these results may then
already be superseded. Meta M18 never consumes this as dispatch authority.
"""
from __future__ import annotations
import os
from collections.abc import Callable
from psycopg.pq import TransactionStatus
from integration.s0s1_pre_dispatch_v02.pg17_service import (
    readback as legacy_readback, out, validate
)

G2_VERSION='prumo.s0.pre-dispatch.g2.snapshot/0.1-lab'
def _result(status,reason,*,classification=None,**extra):
    return {'contract_version':G2_VERSION,'status':status,'reason':reason,
            'classification':classification,
            'transaction_isolation':'REPEATABLE_READ_READ_ONLY',
            'snapshot_consistent_during_read':status=='LAB_HISTORICAL_SNAPSHOT_NO_DISPATCH',
            'snapshot_current_authority':False,
            'authenticated_actor':False,
            'authenticated_receipt':False,
            'attested_attempt_binding':False,
            'outbox_authorized':False,
            'lease_issued':False,'graph_dispatch_authorized':False,
            'send_authorized':False,'automatic_retry_authorized':False,
            'production_authorized':False,**extra}

def classify_historical_snapshot(connection,request,*,scope,principal,
                                 m09_versions,_lab_interleave=None):
    """Caller supplies a FRESH, idle PG17 lab admin connection.

    A single repeatable-read, read-only transaction snapshots all policy,
    registry, consent, quota, and reservation SELECTs performed by legacy
    readback(). It establishes snapshot before optional lab-only interleaving.

    Returned proof is historical and cannot be redeemed: simultaneous policy
    changes can COMMIT after the snapshot begins. REPEATABLE READ alone is
    NOT linearizable and does not replace point-of-use CAS or real actor auth.
    """
    if not validate(request,scope,principal,m09_versions):
        return _result('DENIED','INVALID_REQUEST')
    if os.getenv('M09_PG17_DISPOSABLE')!='YES':
        return _result('DENIED','DISPOSABLE_PG17_REQUIRED')
    if _lab_interleave is not None and not callable(_lab_interleave):
        return _result('DENIED','INVALID_INTERLEAVE')
    try:
        # Must not run inside a caller transaction with weaker isolation;
        # silently creating a savepoint would NOT upgrade its snapshot.
        if connection.info.transaction_status != TransactionStatus.IDLE:
            return _result('DENIED','CALLER_TRANSACTION_ALREADY_ACTIVE')
        if connection.info.server_version // 10000 != 17:
            return _result('DENIED','POSTGRESQL_17_REQUIRED')
        connection.execute('BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY')
        # First SELECT actually establishes the MVCC snapshot.
        gate=connection.execute(
          "SELECT current_database() AS db, "
          "current_setting('s0_meta.disposable',true) AS disposable, "
          "current_setting('transaction_isolation') AS iso, "
          "current_setting('transaction_read_only') AS readonly, "
          "pg_current_snapshot()::text AS snapshot").fetchone()
        if (gate['db']!='s0_meta_ingress_lab' or gate['disposable']!='YES'
            or gate['iso']!='repeatable read' or gate['readonly']!='on'
            or not gate['snapshot']):
            connection.execute('ROLLBACK')
            return _result('DENIED','NOT_DISPOSABLE_COHERENT_SOURCE')
        if _lab_interleave is not None:
            _lab_interleave()
        result=legacy_readback(connection,request,scope=scope,
                               principal=principal,m09_versions=m09_versions)
        # Only lab status fields are exposed. No IDs, nonce or private data.
        if result.get('status')=='UNAVAILABLE':
            connection.execute('ROLLBACK')
            return _result('UNAVAILABLE','SOURCE_UNAVAILABLE')
        if result.get('send_authorized') is not False or (
            result.get('graph_dispatch_authorized') is not False):
            connection.execute('ROLLBACK')
            return _result('DENIED','SOURCE_AUTHORITY_FLAG_INVALID')
        connection.execute('ROLLBACK')
        return _result('LAB_HISTORICAL_SNAPSHOT_NO_DISPATCH',
            'HISTORICAL_OBSERVATION_MAY_BE_SUPERSEDED',
            classification=result)
    except Exception:
        try:
            if connection.info.transaction_status!=TransactionStatus.IDLE:
                connection.rollback()
        except Exception:
            pass
        return _result('UNAVAILABLE','SNAPSHOT_UNAVAILABLE')
