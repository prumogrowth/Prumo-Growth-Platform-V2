"""Installer/control-plane only. Never available through Ingress or HTTP."""
from .protocol import Reject

def mutate(c, route, expected_revision, *, revoke_key=None, disable_binding=None):
    row = c.execute('SELECT revision FROM s0_meta_lab.routes WHERE id=%s FOR UPDATE',(route,)).fetchone()
    if not row or row['revision'] != expected_revision:
        raise Reject('CONTROL_CAS')
    if bool(revoke_key) == bool(disable_binding):
        raise Reject('ONE_CONTROL_MUTATION_REQUIRED')
    if revoke_key:
        changed = c.execute('UPDATE s0_meta_lab.principals SET active=false,revision=revision+1 WHERE route=%s AND key_id=%s AND active RETURNING key_id',
                            (route,revoke_key)).fetchone()
    else:
        changed = c.execute('UPDATE s0_meta_lab.bindings SET active=false,revision=revision+1 WHERE route=%s AND channel=%s AND active RETURNING channel',
                            (route,disable_binding)).fetchone()
    if not changed:
        raise Reject('CONTROL_STALE')
    if disable_binding:
        c.execute('UPDATE s0_meta_lab.routes SET revision=revision+1 WHERE id=%s',(route,))
