import unittest
from uuid import uuid4
from backend.s1_professionals_local import command,receipt


class Contract(unittest.TestCase):
    def setUp(self):
        self.p=dict(action='TRANSFER',target_id=str(uuid4()),cargo='consultor',manager_id=str(uuid4()),
                    expected_relationship_id=3,idempotency_key='i79-test-command')
    def result(self):
        return dict(outcome='APPLIED',request_id=str(uuid4()),action='TRANSFER',target_id=self.p['target_id'],
                    cargo='consultor',manager_id=self.p['manager_id'],previous_relationship_id='3',relationship_id='4')
    def test_identity_and_authority_never_come_from_payload(self):
        for field in ('actor_id','director_id','session_id','is_director','grant'):
            with self.assertRaises(ValueError):command({**self.p,field:True})
    def test_no_director_creation_or_business_command(self):
        for extra in ({'cargo':'diretor'},{'action':'SEND'},{'action':'MOVE_CASE'}):
            with self.assertRaises(ValueError):command({**self.p,**extra})
    def test_exact_cas_types_and_bounds(self):
        for value in (True,0,-1,'3',9223372036854775808):
            with self.assertRaises(ValueError):command({**self.p,'expected_relationship_id':value})
    def test_registration_cannot_activate_or_choose_manager(self):
        with self.assertRaises(ValueError):command({**self.p,'action':'REGISTER','expected_relationship_id':0})
    def test_activation_requires_consultant_manager_but_not_manager_subordinates(self):
        p={**self.p,'action':'ACTIVATE','expected_relationship_id':0}
        command(p)
        with self.assertRaises(ValueError):command({**p,'manager_id':None})
        command({**p,'cargo':'gestor','manager_id':None})
    def test_receipt_scope_and_version_before_commit(self):
        for key,value in (('target_id',str(uuid4())),('manager_id',str(uuid4())),('relationship_id','3'),('previous_relationship_id','2')):
            with self.assertRaises(ValueError):receipt({**self.result(),key:value},command(self.p))
    def test_receipt_no_pii_or_permission_flags(self):
        for field in ('phone','allow_send','service_role'):
            with self.assertRaises(ValueError):receipt({**self.result(),field:True},command(self.p))
    def test_snapshot_of_command(self):
        p=self.p.copy();parsed=command(p);p['manager_id']=str(uuid4())
        self.assertEqual(str(parsed['manager_id']),self.p['manager_id']);receipt(self.result(),parsed)
