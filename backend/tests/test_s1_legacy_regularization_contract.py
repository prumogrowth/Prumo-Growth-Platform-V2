import unittest
from uuid import uuid4
from backend.s1_legacy_regularization_local import command,receipt


class Contract(unittest.TestCase):
    def setUp(self):
        self.p=dict(action='PREVIEW',target_id=str(uuid4()),cargo='consultor',manager_id=str(uuid4()),expected_sha256='a'*64,
                    preview_id=None,cursor=None,limit=0,idempotency_key='i80-unit-command')
    def test_actor_and_permission_flags_rejected(self):
        for field in ('actor_id','session_id','is_director','ratify_sale'):
            with self.assertRaises(ValueError):command({**self.p,field:True})
    def test_no_director_promotion_or_unreviewed_apply(self):
        for delta in ({'cargo':'diretor'},{'action':'APPLY'},{'action':'ACTIVATE'},{'action':'TRANSFER'}):
            with self.assertRaises(ValueError):command({**self.p,**delta})
    def test_only_explicit_canonical_digest_is_accepted(self):
        for value in (None,'A'*64,'claim','a'*63,True):
            with self.assertRaises(ValueError):command({**self.p,'expected_sha256':value})
    def test_inventory_bounds_and_no_role_choice(self):
        p=dict(action='INVENTORY',target_id=None,cargo=None,manager_id=None,expected_sha256=None,preview_id=None,cursor=None,limit=50,idempotency_key='i80-read-command')
        command(p)
        for value in (True,0,51):
            with self.assertRaises(ValueError):command({**p,'limit':value})
    def test_command_is_snapshotted(self):
        original=self.p.copy();p=command(self.p);self.p['cargo']='gestor'
        self.assertEqual(p['cargo'],original['cargo'])
    def test_inventory_never_returns_pii_or_unbounded_cursor(self):
        p=command(dict(action='INVENTORY',target_id=None,cargo=None,manager_id=None,expected_sha256=None,preview_id=None,cursor=None,limit=1,idempotency_key='i80-read-command'))
        good=dict(outcome='INVENTORY',items=[],has_more=False,next_cursor=None)
        receipt(good,p)
        with self.assertRaises(ValueError):receipt({**good,'email':'example'},p)
        with self.assertRaises(ValueError):receipt({**good,'has_more':True},p)
    def test_apply_receipt_scope_is_validated_before_commit(self):
        p=command({**self.p,'action':'APPLY','preview_id':str(uuid4())})
        r=dict(outcome='APPLIED',request_id=str(uuid4()),preview_id=str(p['preview_id']),target_id=str(p['target_id']),cargo=p['cargo'],estado='ativo',
               manager_id=str(p['manager_id']),relationship_id='12',revoked_exception_count=0,before_sha256='a'*64,after_sha256='b'*64)
        receipt(r,p)
        for key,value in (('target_id',str(uuid4())),('before_sha256','c'*64),('relationship_id',None),('revoked_exception_count',True)):
            with self.assertRaises(ValueError):receipt({**r,key:value},p)
    def test_claimed_human_or_commercial_authority_has_no_wire_field(self):
        for key in ('human_intent_sha256','f03_receipt_sha256','send_authorized'):
            with self.assertRaises(ValueError):command({**self.p,key:'a'*64})
