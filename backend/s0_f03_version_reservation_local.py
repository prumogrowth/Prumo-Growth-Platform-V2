"""S0 F03 version-vector CAS *reservation*, local PG17 synthetic only.

No form/catalog/case data is changed here. Current vector values are lab-only
S0-owned fixtures; these are not yet real production per-field versions.
S0's authenticated content/HMAC recheck must wrap every operation.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
from uuid import UUID

from backend.s0_cfi01_f03_receipt_bridge_local import S0F03BoundReceiptLocal
from backend.s0_cfi01_atomic_commands_local import S0InternalReceiptLocal
from backend.s0_f03_bound_content_seal_local import (
    S0F03LocalBoundContentBridge, BoundContentState, _valid,
)
from backend.s0_f03_history_manifest_local import _CONTEXT_SQL, _uuid
from backend.s0_f03_identity_uniqueness_local import conflicting_lead_candidate
from backend.s0_human_closure_event_local import S0LocalClosureStore

_CATALOG = """select versao_catalogo
 from prumo_private.cfi01_f03_catalog_versions_local
 where concessionaria_id=%s::uuid for update"""
_LEAD = """select versao_ficha,versao_identidade
 from prumo_private.cfi01_f03_lead_versions_local
 where concessionaria_id=%s::uuid and lead_id=%s::uuid for update"""
_CASE = """select v.versao_caso,v.versao_atribuicao
 from prumo_private.cfi01_f03_case_versions_local v
 join public.casos_humanos h
  on h.concessionaria_id=v.concessionaria_id and h.id=v.caso_id
  and h.lead_id=v.lead_id
 join public.atribuicoes_humanas a
  on a.concessionaria_id=v.concessionaria_id
  and a.caso_id=v.caso_id and a.id=%s::uuid and a.encerrada_em is null
 join public.ciclos_comerciais c
  on c.concessionaria_id=h.concessionaria_id and c.id=h.ciclo_id
  and c.lead_id=h.lead_id
 where v.concessionaria_id=%s::uuid and v.caso_id=%s::uuid
  and v.lead_id=%s::uuid and c.versao_registro=%s::bigint
 for update of v"""
_PENDING_IDENTITY = """select 1
 from prumo_private.pendencias_identidade_s0 p
 join public.leads_loja l
   on l.concessionaria_id=p.concessionaria_id and l.id=%s::uuid
 where p.concessionaria_id=%s::uuid and (
   p.telefone_sintetico=l.telefone_cliente_normalizado
   or (
     prumo_private.chave_variante_br_s0(p.telefone_sintetico) is not null
     and prumo_private.chave_variante_br_s0(p.telefone_sintetico)
       =prumo_private.chave_variante_br_s0(l.telefone_cliente_normalizado)
   )
   or exists (
     select 1 from prumo_private.aliases_identidade_s0 a
     where a.concessionaria_id=l.concessionaria_id and a.lead_id=l.id
       and (
         a.numero_sintetico=p.telefone_sintetico
         or (
           prumo_private.chave_variante_br_s0(p.telefone_sintetico) is not null
           and prumo_private.chave_variante_br_s0(p.telefone_sintetico)
             =prumo_private.chave_variante_br_s0(a.numero_sintetico)
         )
       )
   )
 ) limit 1"""
_PROOF = """select p.chave_versao
 from prumo_private.cfi01_f03_content_proofs_local p
 join prumo_private.cfi01_f03_history_seals_local s
  on s.concessionaria_id=p.concessionaria_id
  and s.evento_fechamento_id=p.evento_fechamento_id
 where p.concessionaria_id=%s::uuid and p.evento_fechamento_id=%s::uuid
  and p.caso_id=%s::uuid and s.caso_id=p.caso_id
  and s.lead_id=%s::uuid and s.versao_ciclo=%s::bigint
  and s.snapshot_caso_sha256=%s::text
  and s.ultima_mensagem_id=%s::uuid for share of p"""
_EXISTING = """select referencia_requisicao,proposta_sha256,chave_versao,
 versao_ficha,versao_catalogo,versao_caso,versao_atribuicao,versao_identidade
 from prumo_private.cfi01_f03_reservations_local
 where concessionaria_id=%s::uuid and evento_fechamento_id=%s::uuid
 for update"""
_INSERT = """insert into prumo_private.cfi01_f03_reservations_local
 (concessionaria_id,evento_fechamento_id,caso_id,lead_id,
  referencia_requisicao,proposta_sha256,chave_versao,versao_ficha,
  versao_catalogo,versao_caso,versao_atribuicao,versao_identidade)
 values (%s::uuid,%s::uuid,%s::uuid,%s::uuid,%s::text,%s::text,
  %s::text,%s::bigint,%s::bigint,%s::bigint,%s::bigint,%s::bigint)
 on conflict (concessionaria_id,evento_fechamento_id) do nothing
 returning id"""

class ReservationState(str, Enum):
    RESERVED_REVIEW_ONLY = 'RESERVED_REVIEW_ONLY'
    ALREADY_HANDLED_REVIEW_ONLY = 'ALREADY_HANDLED_REVIEW_ONLY'
    STALE_REVIEW_REQUIRED = 'STALE_REVIEW_REQUIRED'
    CONFLICT_REVIEW_REQUIRED = 'CONFLICT_REVIEW_REQUIRED'
    MISSING_VERSION_REVIEW_REQUIRED = 'MISSING_VERSION_REVIEW_REQUIRED'
    DENIED = 'DENIED'
    UNAVAILABLE = 'UNAVAILABLE'

@dataclass(frozen=True)
class VersionVector:
    form: int
    catalog: int
    case: int
    assignment: int
    identity: int

@dataclass(frozen=True)
class ReservationResult:
    state: ReservationState
    # No proposed fields, PII, key, token or SQL receipt in response.


def _validated(binding: object, version: object, request: object,
               proposal_sha: object, key_id: object) -> bool:
    if (type(binding) is not S0F03BoundReceiptLocal
        or type(binding.receipt) is not S0InternalReceiptLocal
        or type(version) is not VersionVector
        or not all(type(n) is int and 1 <= n < 9223372036854775807
                   for n in (version.form,version.catalog,version.case,
                             version.assignment,version.identity))
        or type(request) is not str or not re.fullmatch(r'[A-Za-z0-9._:-]{8,128}',request)
        or type(proposal_sha) is not str or not re.fullmatch(r'[0-9a-f]{64}',proposal_sha)
        or type(key_id) is not str or not re.fullmatch(r'[A-Za-z0-9._:-]{8,80}',key_id)):
        return False
    r=binding.receipt
    return (all(_uuid(x) for x in (r.store_ref,r.case_ref,r.closure_event_ref,
                                  r.assignment_ref,r.message_watermark))
            and type(r.expected_cycle_version) is int and r.expected_cycle_version>0
            and type(r.snapshot_sha256) is str and re.fullmatch(r'[0-9a-f]{64}',r.snapshot_sha256) is not None
            and type(r.message_count) is int and r.message_count>0)

class S0F03LocalVersionReservationStore:
    """Transactional advisory CAS. It neither applies nor claims real form state."""
    def __init__(self, dsn: str):
        self._dsn=S0LocalClosureStore(dsn)._dsn

    def reserve(self, binding: S0F03BoundReceiptLocal, version: VersionVector,
                request: str, proposal_sha: str, key_id: str) -> ReservationState:
        if not _validated(binding,version,request,proposal_sha,key_id):
            return ReservationState.DENIED
        r=binding.receipt
        try:
            import psycopg
            with psycopg.connect(self._dsn,connect_timeout=5) as con:
                with con.cursor() as cur:
                    cur.execute("set local lock_timeout = '3s'")
                    # Serialize with all S0 synthetic phone/alias source writers.
                    cur.execute("select prumo_private.s0_f03_lock_shop_local(%s::uuid)",
                                (r.store_ref,))
                    cur.execute(_CONTEXT_SQL,(
                        r.closure_event_ref,r.store_ref,r.case_ref,
                        r.snapshot_sha256,r.expected_cycle_version,
                        r.message_watermark,r.message_count))
                    context=cur.fetchall()
                    if len(context)!=1 or not isinstance(context[0][0],UUID):
                        return ReservationState.STALE_REVIEW_REQUIRED
                    lead,_cutoff=context[0]
                    # Canonical lock ordering: store catalogue -> person -> case.
                    cur.execute(_CATALOG,(r.store_ref,))
                    cat=cur.fetchone()
                    cur.execute(_LEAD,(r.store_ref,lead))
                    person=cur.fetchone()
                    cur.execute(_CASE,(r.assignment_ref,r.store_ref,r.case_ref,
                                       lead,r.expected_cycle_version))
                    case=cur.fetchone()
                    if (cat is None or person is None or case is None
                        or len(cat)!=1 or len(person)!=2 or len(case)!=2):
                        return ReservationState.MISSING_VERSION_REVIEW_REQUIRED
                    current=(person[0],cat[0],case[0],case[1],person[1])
                    expected=(version.form,version.catalog,version.case,
                              version.assignment,version.identity)
                    if current!=expected:
                        return ReservationState.STALE_REVIEW_REQUIRED
                    # Pending S0 identity conflicts cannot be assigned to a
                    # lead by F03. Treat exact or Brazilian mobile variant
                    # candidates as REVIEW_REQUIRED; no automatic merge.
                    cur.execute(_PENDING_IDENTITY,(lead,r.store_ref))
                    if cur.fetchone() is not None:
                        return ReservationState.CONFLICT_REVIEW_REQUIRED
                    if conflicting_lead_candidate(cur,r.store_ref,lead):
                        return ReservationState.CONFLICT_REVIEW_REQUIRED
                    cur.execute(_PROOF,(r.store_ref,r.closure_event_ref,
                                        r.case_ref,lead,r.expected_cycle_version,
                                        r.snapshot_sha256,r.message_watermark))
                    proof=cur.fetchone()
                    if proof is None or proof!=(key_id,):
                        return ReservationState.STALE_REVIEW_REQUIRED
                    cur.execute(_EXISTING,(r.store_ref,r.closure_event_ref))
                    existing=cur.fetchone()
                    signature=(request,proposal_sha,key_id,*expected)
                    if existing is not None:
                        if existing==signature:
                            return ReservationState.ALREADY_HANDLED_REVIEW_ONLY
                        return ReservationState.CONFLICT_REVIEW_REQUIRED
                    cur.execute(_INSERT,(
                        r.store_ref,r.closure_event_ref,r.case_ref,str(lead),
                        request,proposal_sha,key_id,*expected))
                    if cur.fetchone() is None:
                        return ReservationState.CONFLICT_REVIEW_REQUIRED
                    return ReservationState.RESERVED_REVIEW_ONLY
        except Exception:
            return ReservationState.UNAVAILABLE

class S0F03LocalVersionReservationBridge:
    """Requires a real S0 authorized HMAC verification before AND after CAS."""
    def __init__(self, content: S0F03LocalBoundContentBridge,
                 store: S0F03LocalVersionReservationStore):
        if (type(content) is not S0F03LocalBoundContentBridge
            or type(store) is not S0F03LocalVersionReservationStore
            or content._store._dsn != store._dsn):
            raise TypeError('S0 F03 content and version DB mismatch')
        self._content=content
        self._store=store

    def reserve(self, authorization: str, binding: S0F03BoundReceiptLocal,
                key_id: str, secret: bytes, version: VersionVector,
                request: str, proposal_sha: str) -> ReservationResult:
        if (not _validated(binding,version,request,proposal_sha,key_id)
            or not _valid(binding,key_id,secret)):
            return ReservationResult(ReservationState.DENIED)
        try:
            before=self._content.verify(authorization,binding,key_id,secret)
            if before.state is not BoundContentState.MATCHES_REVIEW_ONLY:
                return ReservationResult(ReservationState.STALE_REVIEW_REQUIRED)
            state=self._store.reserve(binding,version,request,proposal_sha,key_id)
            if state not in (ReservationState.RESERVED_REVIEW_ONLY,
                             ReservationState.ALREADY_HANDLED_REVIEW_ONLY):
                return ReservationResult(state)
            after=self._content.verify(authorization,binding,key_id,secret)
            if after.state is not BoundContentState.MATCHES_REVIEW_ONLY:
                return ReservationResult(ReservationState.STALE_REVIEW_REQUIRED)
            return ReservationResult(state)
        except Exception:
            return ReservationResult(ReservationState.UNAVAILABLE)
