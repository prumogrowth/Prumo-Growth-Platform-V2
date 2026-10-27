import unittest
from uuid import uuid4
from backend.s0_g1_manual_queue_local import fields,safe_result


class ManualContractTests(unittest.TestCase):
    def setUp(self):
        self.payload=dict(loja_id=str(uuid4()),ciclo_id=str(uuid4()),consultor_id=str(uuid4()),
                          versao_esperada=1,chave_idempotencia='g1-test-request-0001')

    def result(self):
        return dict(outcome='MANUAL_ASSIGNED',request_id=str(uuid4()),store_id=self.payload['loja_id'],
            cycle_id=self.payload['ciclo_id'],consultant_id=self.payload['consultor_id'],
            case_id=str(uuid4()),assignment_id=str(uuid4()),exception_id=None,version=2)

    def test_01_actor_role_session_and_action_cannot_come_from_payload(self):
        for key in ('actor_id','gestor_id','session_id','is_manager','action','case_id'):
            with self.assertRaises(ValueError):fields({**self.payload,key:str(uuid4())})

    def test_02_bool_and_int64_overflow_are_not_queue_versions(self):
        for version in (True,False,0,-1,9223372036854775807,'1'):
            with self.assertRaises(ValueError):fields({**self.payload,'versao_esperada':version})

    def test_03_payload_snapshot_retains_values_and_returns_typed_uuids(self):
        original=self.payload.copy();values=fields(self.payload)
        self.assertEqual(self.payload,original);self.assertEqual(str(values['loja_id']),original['loja_id'])

    def test_04_idempotency_and_uuid_fields_are_strict(self):
        for key in ('bad key',7,'x'*129,'<SEND_NOW>'):
            with self.assertRaises(ValueError):fields({**self.payload,'chave_idempotencia':key})
        with self.assertRaises(ValueError):fields({**self.payload,'loja_id':'not-a-uuid'})

    def test_05_result_cannot_change_store_cycle_destination_or_version(self):
        for key in ('store_id','cycle_id','consultant_id','version'):
            bad=self.result();bad[key]=4 if key=='version' else str(uuid4())
            with self.assertRaises(ValueError):safe_result(bad,fields(self.payload))

    def test_06_result_has_no_extra_pii_or_authority_flags(self):
        for key in ('telefone','conteudo','send_authorized'):
            with self.assertRaises(ValueError):safe_result({**self.result(),key:True},fields(self.payload))

    def test_07_other_operation_outcomes_do_not_mean_manual_handoff(self):
        for state in ('CLAIMED_BY_MANAGER','ASSIGNED_NEW','SENT','APPLIED'):
            with self.assertRaises(ValueError):safe_result({**self.result(),'outcome':state},fields(self.payload))

    def test_08_normal_and_exceptional_results_keep_minimal_scoped_shape(self):
        normal=self.result();self.assertEqual(safe_result(normal,fields(self.payload)),normal)
        exceptional={**normal,'exception_id':str(uuid4()),'outcome':'ALREADY_MANUAL_ASSIGNED'}
        self.assertEqual(safe_result(exceptional,fields(self.payload)),exceptional)
