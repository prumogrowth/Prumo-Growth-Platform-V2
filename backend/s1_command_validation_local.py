"""I67: shared syntax-only validation for local S1 commands.

No legacy SQL facade, database credentials, GoTrue caller or HMAC authority
are imported here. Signed gateways and HTTP policy use the same field schema.
"""
from __future__ import annotations
import re
import uuid

from backend.identity_boundary import InvalidCommand

_UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
LEGACY_COMMANDS={
 "mover":("loja_id","caso_id","atribuicao_esperada_id","destino_id"),
 "pausar":("operador_id","motivo_codigo"),
 "reativar":("operador_id",),
}
_REASON=frozenset(("AUSENCIA_TEMPORARIA","INDISPONIBILIDADE_OPERACIONAL"))

def _uuid(value):
 if not isinstance(value,str) or not _UUID.fullmatch(value):
  raise InvalidCommand("ID_INVALIDO")
 return uuid.UUID(value)

def _fields(command,data):
 if command not in LEGACY_COMMANDS or type(data) is not dict:
  raise InvalidCommand("COMANDO_NAO_PERMITIDO")
 fields=LEGACY_COMMANDS[command]
 if set(data)!=set(fields):
  raise InvalidCommand("CAMPOS_NAO_PERMITIDOS")
 output=[]
 for field in fields:
  value=data[field]
  if field=="motivo_codigo":
   if type(value) is not str or value not in _REASON:
    raise InvalidCommand("MOTIVO_INVALIDO")
   output.append(value)
  else:
   output.append(_uuid(value))
 return tuple(output)
