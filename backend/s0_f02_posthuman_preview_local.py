"""E04 S0-owned post-human F02 *preview*, no scheduling or external send.

Standalone extension to the S0/C04 gap review. The S2 JS candidate never
asserts permission. Requires a separately verified manager session, current
S1 roster and S0 template/purpose/category. C04's existing prohibition on
recontact for humanized cycles remains completely intact.

Positive return is PREVIEW_ONLY_LEGACY_C04_BLOCKED, not send, approval of
real marketing consent, authoritative category from Meta or a write operation.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import re
from uuid import UUID

from backend.identity_boundary import Principal,IdentityProvider,Denied
from backend.s0_f02_posthuman_compatibility_local import (
    S0F02LocalPostHumanCompatibilityBridge,F02RecheckState,
    _candidate as _s2_f02_candidate,
)
from backend.s0_f03_version_reservation_local import VersionVector
from backend.s0_f03_operational_contracts_local import ProposedField
from backend.s0_cfi01_f03_receipt_bridge_local import S0F03BoundReceiptLocal
from backend.s0_human_closure_event_local import S0LocalClosureStore

_MANAGER="""select 1
from auth.sessions s
join public.equipe_prumo_s1 t on t.ator_id=s.user_id and t.estado='ativo'
join public.vinculos_papel_escopo v on v.ator_id=s.user_id
 and v.concessionaria_id=%s::uuid and v.papel='gestor'
 and v.valido_desde<=statement_timestamp()
 and (v.valido_ate is null or v.valido_ate>statement_timestamp())
where s.id=%s::uuid and s.user_id=%s::uuid
"""
_TEMPLATE="""select c.codigo,c.versao,c.aprovado_simulacao,
 p.finalidade,p.categoria,p.versao_politica
from public.catalogo_templates_sinteticos c
join prumo_private.cfi01_f02_posthuman_template_policy_local p
 on p.concessionaria_id=c.concessionaria_id and p.template_id=c.id
where c.concessionaria_id=%s::uuid and c.id=%s::uuid
"""
_TEMPLATE_EXISTS="""select 1 from public.catalogo_templates_sinteticos c
where c.concessionaria_id=%s::uuid and c.id=%s::uuid """

class PreviewState(str,Enum):
    PREVIEW_ONLY_LEGACY_C04_BLOCKED='PREVIEW_ONLY_LEGACY_C04_BLOCKED'
    DENIED='DENIED'
    MANAGER_S1_REQUIRED='MANAGER_S1_REQUIRED'
    TEMPLATE_POLICY_REQUIRED='TEMPLATE_POLICY_REQUIRED'
    TEMPLATE_STALE_REVIEW_REQUIRED='TEMPLATE_STALE_REVIEW_REQUIRED'
    CONTRACT_REVIEW_REQUIRED='CONTRACT_REVIEW_REQUIRED'
    UNAVAILABLE='UNAVAILABLE'

@dataclass(frozen=True)
class PreviewResult:
    state:PreviewState

@dataclass(frozen=True)
class PostHumanPreviewRequest:
    """S0 operator-supplied local intent; no actor id, source approval or send flag."""
    template_ref:str
    policy_version:str

def _uuid(v:object)->UUID|None:
    if type(v) is not str:return None
    try:
        ident=UUID(v)
        return ident if str(ident)==v else None
    except (ValueError,TypeError,AttributeError):
        return None

def _valid_request(req:object)->bool:
    return (type(req) is PostHumanPreviewRequest
        and _uuid(req.template_ref) is not None
        and type(req.policy_version) is str
        and re.fullmatch(r'[A-Za-z0-9_.:-]{4,80}',req.policy_version) is not None)

class S0F02LocalPostHumanPreview:
    """Read-only preflight performed only after actual S0/F03 compatibility gate."""
    def __init__(self,compat:S0F02LocalPostHumanCompatibilityBridge,
                 identity:IdentityProvider,dsn:str):
        if type(compat) is not S0F02LocalPostHumanCompatibilityBridge:
            raise TypeError('physical S0 F02 compatibility gate required')
        if identity is None or not callable(getattr(identity,'verify',None)):
            raise TypeError('trusted S0 identity provider required')
        local=S0LocalClosureStore(dsn)._dsn
        if compat._dsn!=local:
            raise TypeError('physical S0 database mismatch')
        self._compat=compat
        self._identity=identity
        self._dsn=local

    def inspect(self,authorization:str,binding:S0F03BoundReceiptLocal,
                key_version:str,secret:bytes,version:VersionVector,
                request_ref:str,fields:tuple[ProposedField,...],
                f03_output:dict,f03_proposal:dict,
                s2_f02_result:dict,channel_ref:str,
                request:PostHumanPreviewRequest)->PreviewResult:
        if not _valid_request(request) or not _s2_f02_candidate(s2_f02_result):
            return PreviewResult(PreviewState.DENIED)
        try:
            principal=self._identity.verify(authorization)
            if type(principal) is not Principal:
                return PreviewResult(PreviewState.DENIED)
        except Denied:
            return PreviewResult(PreviewState.DENIED)
        except Exception:
            return PreviewResult(PreviewState.UNAVAILABLE)
        before=self._compat.inspect(authorization,binding,key_version,secret,
                                   version,request_ref,fields,f03_output,
                                   f03_proposal,s2_f02_result,channel_ref)
        if before.state is not F02RecheckState.LEGACY_C04_HUMAN_CASE_INCOMPATIBLE:
            if before.state is F02RecheckState.UNAVAILABLE:
                return PreviewResult(PreviewState.UNAVAILABLE)
            if before.state is F02RecheckState.DENIED:
                return PreviewResult(PreviewState.DENIED)
            return PreviewResult(PreviewState.CONTRACT_REVIEW_REQUIRED)
        store=binding.receipt.store_ref
        try:
            import psycopg
            with psycopg.connect(self._dsn,connect_timeout=5) as con:
                with con.cursor() as cur:
                    cur.execute("set transaction isolation level repeatable read read only")
                    cur.execute("set local lock_timeout='3s'")
                    cur.execute(_MANAGER,(store,principal.session_id,principal.actor_id))
                    if cur.fetchone() is None:
                        return PreviewResult(PreviewState.MANAGER_S1_REQUIRED)
                    cur.execute(_TEMPLATE,(store,request.template_ref))
                    details=cur.fetchone()
                    if details is None:
                        cur.execute(_TEMPLATE_EXISTS,(store,request.template_ref))
                        return PreviewResult(PreviewState.TEMPLATE_POLICY_REQUIRED
                            if cur.fetchone() else PreviewState.TEMPLATE_STALE_REVIEW_REQUIRED)
                    code,number,approved,purpose,category,policy=details
                    if approved is not True or purpose!='post_human':
                        return PreviewResult(PreviewState.TEMPLATE_STALE_REVIEW_REQUIRED)
                    if (s2_f02_result['templateId']!=code
                        or s2_f02_result['templateVersion']!=f'v{number}'
                        or s2_f02_result['category']!=category
                        or policy!=request.policy_version):
                        return PreviewResult(PreviewState.TEMPLATE_STALE_REVIEW_REQUIRED)
            # The underlying S0 PG17 contact/case/identity gate is rerun for
            # fail-closed drift, including opt-out and legacy plans.
            again=self._compat.inspect(authorization,binding,key_version,secret,
                                       version,request_ref,fields,f03_output,
                                       f03_proposal,s2_f02_result,channel_ref)
            if again.state is not F02RecheckState.LEGACY_C04_HUMAN_CASE_INCOMPATIBLE:
                return PreviewResult(PreviewState.CONTRACT_REVIEW_REQUIRED)
            return PreviewResult(PreviewState.PREVIEW_ONLY_LEGACY_C04_BLOCKED)
        except Exception:
            return PreviewResult(PreviewState.UNAVAILABLE)
