"""I67 regression: neutral command schema equals the retired I19 parser.

Both modules exist only locally. This checks parsing compatibility without
requiring the old SQL facade capability.
"""
import unittest
from backend.s1_command_validation_local import _fields as neutral,LEGACY_COMMANDS
from backend.s1_gateway_local import _fields as retired,_SQL
from backend.identity_boundary import InvalidCommand

UID="00000000-0000-4000-8000-000000000001"

class CommandValidationI67(unittest.TestCase):
 def test_same_field_sets(self):
  self.assertEqual({k:tuple(v[1]) for k,v in _SQL.items()},LEGACY_COMMANDS)
 def test_equivalent_valid(self):
  for cmd,payload in (
   ("mover",{"loja_id":UID,"caso_id":UID,"atribuicao_esperada_id":UID,"destino_id":UID}),
   ("pausar",{"operador_id":UID,"motivo_codigo":"AUSENCIA_TEMPORARIA"}),
   ("pausar",{"operador_id":UID,"motivo_codigo":"INDISPONIBILIDADE_OPERACIONAL"}),
   ("reativar",{"operador_id":UID}),
  ):
   with self.subTest(cmd=cmd,payload=payload):
    self.assertEqual(neutral(cmd,payload),retired(cmd,payload))
 def test_equivalent_invalid(self):
  for cmd,payload in (
   ("mover",{"loja_id":UID}),
   ("reativar",{"operador_id":True}),
   ("pausar",{"operador_id":UID,"motivo_codigo":"LIVRE"}),
   ("pausar",{"operador_id":UID,"motivo_codigo":True}),
   ("reativar",{"operador_id":UID,"ator_id":UID}),
   ("indefinido",{}),
   ("mover",None),
  ):
   with self.subTest(cmd=cmd,payload=payload):
    with self.assertRaises(InvalidCommand) as a:neutral(cmd,payload)
    with self.assertRaises(InvalidCommand) as b:retired(cmd,payload)
    self.assertEqual(str(a.exception),str(b.exception))
