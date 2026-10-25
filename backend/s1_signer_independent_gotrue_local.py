"""S1-002/I26 - GoTrue revalidado DENTRO do assinador (somente CI).

O gateway faz uma verificacao inicial e envia o Bearer ao processo-filho.
O filho revalida via seu proprio cliente GoTrue ANTES de assinar,
e vincula sub/session_id do retorno confiavel ao material canonico HMAC.
Isso nao substitui I15 auth.sessions nem protege contra roubo do Bearer.
"""
from __future__ import annotations

import time
import uuid

from backend.identity_boundary import Denied, IdentityUnavailable, InvalidCommand
from backend.s1_command_validation_local import _fields
from backend.s1_gateway_signed_local import _COMMAND, _action_args, _proof_material, _SQL_SIGNED
from backend.s1_signer_process_local import LocalSeparatedSignerGateway


class LocalIndependentlyAuthenticatedGateway(LocalSeparatedSignerGateway):
    def proof(self, principal, command, values, *, authorization,
              issued=None, nonce=None):
        op = _COMMAND.get(command)
        if op is None:
            raise InvalidCommand("COMANDO_NAO_PERMITIDO")
        args = _action_args(command, values)
        issued_at = int(time.time()) if issued is None else issued
        unique = uuid.uuid4() if nonce is None else nonce
        material = _proof_material(op, principal.actor_id, principal.session_id,
                                   args, issued_at, unique)
        # Chave/controle nao estao no gateway. O assinador nao pode ignorar
        # esta prova: no modo I26, rejeita requests sem bearer ou sub falso.
        signature = self.signer.sign(self.key_id, material, authorization)
        return (op, principal.actor_id, principal.session_id, *args,
                self.key_id, issued_at, unique, signature)

    def invoke(self, authorization, command, payload):
        import psycopg
        values = _fields(command, payload)
        principal = self.gotrue.verify(authorization)
        signed_args = self.proof(principal, command, values,
                                 authorization=authorization)
        with psycopg.connect(self.dsn, connect_timeout=5) as connection:
            with connection.cursor() as cur:
                try:
                    cur.execute(_SQL_SIGNED, signed_args)
                except psycopg.Error as exc:
                    if exc.sqlstate in ("42501", "22023", "23514", "23505"):
                        raise Denied("OPERACAO_S1_NAO_AUTORIZADA") from None
                    raise IdentityUnavailable("BANCO_INDISPONIVEL") from None
                row = cur.fetchone()
                if row is None or not isinstance(row[0], dict):
                    raise IdentityUnavailable("RETORNO_S1_INVALIDO")
                return row[0]
