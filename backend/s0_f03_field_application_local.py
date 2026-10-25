"""S0-only E04 human-authorized, atomic synthetic form CAS.

Only a trusted S0 IdentityProvider can identify the manager. The F03 proposal
or HOLD receipt NEVER authorizes an edit. A manager explicitly requests an S0
transaction, which checks session, S1 team, manager scope, live HMAC, the
reservation, five versions and every old-field hash BEFORE ANY mutation.
All synthetic field writes and append-only audit rows commit together.
No real customer form, status change, Meta/OpenAI call or model-side entrypoint.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import hmac
import json
import re
import uuid

from backend.identity_boundary import Principal, Denied, IdentityProvider
from backend.s0_human_closure_event_local import (
    S0LocalClosureStore, S1TransactionAuthority, S1Proof, _SESSION,
)
from backend.s0_f03_identity_ratification_local import _MANAGER_SCOPE
from backend.s0_f03_version_reservation_local import (
    VersionVector,_validated,_CATALOG,_LEAD,_CASE,_PENDING_IDENTITY,_PROOF,
)
from backend.s0_f03_operational_contracts_local import (
    ProposedField,FieldKind,proposal_digest,_SHOP_LOCK,
    _FIELD,_PRODUCT,_RESERVATION,
)
from backend.s0_f03_history_manifest_local import _CONTEXT_SQL,MAX_HISTORY_RECORDS
from backend.s0_f03_bound_content_seal_local import _valid as _valid_hmac
from backend.s0_f03_content_integrity_local import _CONTENT_SQL,_derive
from backend.s0_f03_bound_content_seal_local import _LOCK_LEAD,_LOCK_CONVERSATIONS
from backend.s0_cfi01_f03_receipt_bridge_local import S0F03BoundReceiptLocal

class HumanDecision(str,Enum):
    EXPLICIT_APPROVE_SYNTHETIC_FIELDS='EXPLICIT_APPROVE_SYNTHETIC_FIELDS'

@dataclass(frozen=True)
class FieldCAS:
    proposed: ProposedField
    expected_old_sha256: str|None  # None means field MUST not already exist.

@dataclass(frozen=True)
class HumanFieldRequest:
    binding: S0F03BoundReceiptLocal
    version: VersionVector
    request_ref: str
    key_version: str
    fields: tuple[FieldCAS,...]
    decision: HumanDecision
    approval_evidence_sha256: str
    idempotency_key: str

class ApplicationState(str,Enum):
    APPLIED_SYNTHETIC_ONLY='APPLIED_SYNTHETIC_ONLY'
    ALREADY_APPLIED_AUDIT_ONLY='ALREADY_APPLIED_AUDIT_ONLY'
    DENIED='DENIED'
    BLOCKED_S1='BLOCKED_S1'
    STALE_REVIEW_REQUIRED='STALE_REVIEW_REQUIRED'
    CONFLICT_REVIEW_REQUIRED='CONFLICT_REVIEW_REQUIRED'
    FIELD_REVIEW_REQUIRED='FIELD_REVIEW_REQUIRED'
    CATALOG_REVIEW_REQUIRED='CATALOG_REVIEW_REQUIRED'
    UNAVAILABLE='UNAVAILABLE'

@dataclass(frozen=True)
class ApplicationResult:
    state: ApplicationState
    # No field value, lead, actor, HMAC, secret, credentials, or F03 grant.

_EXISTING = """select gestor_id,sessao_id,referencia_requisicao,proposta_sha256,
cas_condicoes_sha256,evidencia_aprovacao_sha256,chave_idempotencia,
versao_ficha_antes,quantidade_campos,decisao
from prumo_private.cfi01_f03_form_application_local
where concessionaria_id=%s::uuid and evento_fechamento_id=%s::uuid for update"""
_OLD = """select valor_sintetico
from prumo_private.cfi01_f03_form_fields_local
where concessionaria_id=%s::uuid and lead_id=%s::uuid and campo_sintetico=%s::text
for update"""
_INSERT_FORM = """insert into prumo_private.cfi01_f03_form_fields_local
(concessionaria_id,lead_id,campo_sintetico,valor_sintetico)
values(%s::uuid,%s::uuid,%s::text,%s::text)"""
_UPDATE_FORM = """update prumo_private.cfi01_f03_form_fields_local
set valor_sintetico=%s::text
where concessionaria_id=%s::uuid and lead_id=%s::uuid and campo_sintetico=%s::text"""
_AUDIT = """insert into prumo_private.cfi01_f03_form_application_local
(concessionaria_id,evento_fechamento_id,caso_id,lead_id,gestor_id,sessao_id,
referencia_requisicao,proposta_sha256,cas_condicoes_sha256,
evidencia_aprovacao_sha256,chave_idempotencia,versao_ficha_antes,
versao_ficha_depois,quantidade_campos,decisao)
values(%s::uuid,%s::uuid,%s::uuid,%s::uuid,%s::uuid,%s::uuid,
%s::text,%s::text,%s::text,%s::text,%s::text,%s::bigint,
%s::bigint,%s::integer,%s::text) returning id"""
_AUDIT_ITEM = """insert into prumo_private.cfi01_f03_form_application_items_local
(aplicacao_id,campo_sintetico,antigo_sha256,novo_sha256)
values(%s::uuid,%s::text,%s::text,%s::text)"""
_SAVED_HMAC = """select p.chave_versao,p.metadados_sha256,p.mac_sha256,
p.quantidade_mensagens,p.quantidade_casos
from prumo_private.cfi01_f03_content_proofs_local p
where p.concessionaria_id=%s::uuid and p.evento_fechamento_id=%s::uuid
and p.caso_id=%s::uuid for share"""
_VERSION_AFTER = """select versao_ficha
from prumo_private.cfi01_f03_lead_versions_local
where concessionaria_id=%s::uuid and lead_id=%s::uuid"""

def _sha(value:str)->str:
    return hashlib.sha256(value.encode('utf-8')).hexdigest()

def _condition_sha(fields:tuple[FieldCAS,...])->str:
    ordered=sorted([[f.proposed.field_key,f.expected_old_sha256] for f in fields])
    return _sha(json.dumps(ordered,ensure_ascii=False,separators=(',',':')))

def _inputs(req:object,key:object)->tuple[tuple[ProposedField,...],str,str]|None:
    if (type(req) is not HumanFieldRequest
        or type(req.decision) is not HumanDecision
        or req.decision is not HumanDecision.EXPLICIT_APPROVE_SYNTHETIC_FIELDS
        or type(req.fields) is not tuple or not 1<=len(req.fields)<=12
        or type(req.approval_evidence_sha256) is not str
        or re.fullmatch(r'[0-9a-f]{64}',req.approval_evidence_sha256) is None
        or type(req.idempotency_key) is not str
        or re.fullmatch(r'[A-Za-z0-9._:-]{8,128}',req.idempotency_key) is None):
        return None
    proposed=tuple(f.proposed for f in req.fields if type(f) is FieldCAS)
    if len(proposed)!=len(req.fields):
        return None
    if any(f.expected_old_sha256 is not None and
           (type(f.expected_old_sha256) is not str or
            re.fullmatch(r'[0-9a-f]{64}',f.expected_old_sha256) is None)
           for f in req.fields):
        return None
    proposal_sha=proposal_digest(proposed)
    if (proposal_sha is None
        or not _validated(req.binding,req.version,req.request_ref,
                          proposal_sha,req.key_version)
        or not _valid_hmac(req.binding,req.key_version,key)):
        return None
    return proposed,proposal_sha,_condition_sha(req.fields)

class S0F03LocalHumanFieldApplicationStore:
    """Strictly local PG17, same transaction for checks, writes and audit."""
    def __init__(self,dsn:str):
        self._dsn=S0LocalClosureStore(dsn)._dsn

    def apply(self,principal:Principal,req:HumanFieldRequest,
              s1:S1TransactionAuthority|None,key:bytes)->ApplicationResult:
        if s1 is None:
            return ApplicationResult(ApplicationState.BLOCKED_S1)
        inputs=_inputs(req,key)
        if inputs is None:
            return ApplicationResult(ApplicationState.DENIED)
        proposals,digest,conditions=inputs
        r=req.binding.receipt
        import psycopg
        try:
            with psycopg.connect(self._dsn,connect_timeout=5) as con:
                with con.cursor() as cur:
                    cur.execute("set local lock_timeout='3s'")
                    cur.execute(_SESSION,(principal.session_id,principal.actor_id))
                    if cur.fetchone() is None:
                        return ApplicationResult(ApplicationState.DENIED)
                    if s1.lock_team(cur,principal) is not S1Proof.ALLOW:
                        return ApplicationResult(ApplicationState.BLOCKED_S1)
                    # Prevent new synthetic S0 identity pendings during CAS.
                    cur.execute(_SHOP_LOCK,(r.store_ref,))
                    cur.execute(_CONTEXT_SQL,(
                        r.closure_event_ref,r.store_ref,r.case_ref,
                        r.snapshot_sha256,r.expected_cycle_version,
                        r.message_watermark,r.message_count))
                    ctx=cur.fetchall()
                    if len(ctx)!=1 or not isinstance(ctx[0][0],uuid.UUID):
                        return ApplicationResult(ApplicationState.STALE_REVIEW_REQUIRED)
                    lead,cutoff=ctx[0]
                    cur.execute(_MANAGER_SCOPE,(principal.actor_id,r.store_ref))
                    if cur.fetchone() is None:
                        return ApplicationResult(ApplicationState.DENIED)
                    # The human's explicit decision never comes from an F03 role.
                    # A valid S0 manager is separately required on every call.
                    cur.execute(_EXISTING,(r.store_ref,r.closure_event_ref))
                    prior=cur.fetchone()
                    signature=(principal.actor_id,principal.session_id,
                               req.request_ref,digest,conditions,
                               req.approval_evidence_sha256,req.idempotency_key,
                               req.version.form,len(proposals),req.decision.value)
                    if prior is not None:
                        return ApplicationResult(
                            ApplicationState.ALREADY_APPLIED_AUDIT_ONLY
                            if prior==signature else
                            ApplicationState.CONFLICT_REVIEW_REQUIRED)
                    # Same lock order as S0 reservation.
                    cur.execute(_CATALOG,(r.store_ref,))
                    cat=cur.fetchone()
                    cur.execute(_LEAD,(r.store_ref,lead))
                    person=cur.fetchone()
                    cur.execute(_CASE,(r.assignment_ref,r.store_ref,r.case_ref,
                                       lead,r.expected_cycle_version))
                    case=cur.fetchone()
                    if cat is None or person is None or case is None:
                        return ApplicationResult(ApplicationState.STALE_REVIEW_REQUIRED)
                    expected=(req.version.form,req.version.catalog,req.version.case,
                              req.version.assignment,req.version.identity)
                    if (person[0],cat[0],case[0],case[1],person[1])!=expected:
                        return ApplicationResult(ApplicationState.STALE_REVIEW_REQUIRED)
                    cur.execute(_PENDING_IDENTITY,(lead,r.store_ref))
                    if cur.fetchone() is not None:
                        return ApplicationResult(ApplicationState.CONFLICT_REVIEW_REQUIRED)
                    cur.execute(_RESERVATION,(r.store_ref,r.closure_event_ref,
                                              r.case_ref,lead))
                    if cur.fetchone()!=(req.request_ref,digest,req.key_version,*expected):
                        return ApplicationResult(ApplicationState.CONFLICT_REVIEW_REQUIRED)
                    cur.execute(_PROOF,(r.store_ref,r.closure_event_ref,r.case_ref,
                                        lead,r.expected_cycle_version,
                                        r.snapshot_sha256,r.message_watermark))
                    if cur.fetchone()!=(req.key_version,):
                        return ApplicationResult(ApplicationState.STALE_REVIEW_REQUIRED)

                    # Lock physical lead/conversations, rederive HMAC INSIDE the
                    # SAME writing transaction before modifying any field.
                    cur.execute(_LOCK_LEAD,(r.store_ref,lead))
                    if len(cur.fetchall())!=1:
                        return ApplicationResult(ApplicationState.STALE_REVIEW_REQUIRED)
                    cur.execute(_LOCK_CONVERSATIONS,(r.store_ref,lead))
                    if not cur.fetchall():
                        return ApplicationResult(ApplicationState.STALE_REVIEW_REQUIRED)
                    cur.execute(_CONTENT_SQL+' for share of m',
                                (r.store_ref,lead,cutoff))
                    rows=cur.fetchmany(MAX_HISTORY_RECORDS+1)
                    proof=_derive(rows,r,str(lead),cutoff,key)
                    cur.execute(_SAVED_HMAC,(r.store_ref,r.closure_event_ref,r.case_ref))
                    saved=cur.fetchone()
                    if (proof is None or saved is None or len(saved)!=5
                        or saved[0]!=req.key_version
                        or saved[1]!=proof.metadata_sha256
                        or saved[3]!=proof.count or saved[4]!=proof.case_count
                        or not hmac.compare_digest(saved[2],proof.content_mac_sha256)):
                        return ApplicationResult(ApplicationState.STALE_REVIEW_REQUIRED)
                    # Precheck the COMPLETE batch and old values before writing.
                    changes=[]
                    for entry in sorted(req.fields,key=lambda x:x.proposed.field_key):
                        f=entry.proposed
                        cur.execute(_FIELD,(r.store_ref,f.field_key))
                        rule=cur.fetchone()
                        if (rule is None or rule[2] is not True
                            or rule[0]!=f.kind.value or len(f.value)>rule[1]):
                            return ApplicationResult(ApplicationState.FIELD_REVIEW_REQUIRED)
                        if f.kind is FieldKind.CATALOG_CODE:
                            if re.fullmatch(r'[A-Z0-9_-]{2,48}',f.value) is None:
                                return ApplicationResult(ApplicationState.CATALOG_REVIEW_REQUIRED)
                            cur.execute(_PRODUCT,(r.store_ref,f.value))
                            product=cur.fetchone()
                            if product is None or product[0] is not True:
                                return ApplicationResult(ApplicationState.CATALOG_REVIEW_REQUIRED)
                        cur.execute(_OLD,(r.store_ref,lead,f.field_key))
                        old=cur.fetchone()
                        old_hash=_sha(old[0]) if old is not None else None
                        if old_hash!=entry.expected_old_sha256:
                            return ApplicationResult(ApplicationState.CONFLICT_REVIEW_REQUIRED)
                        if old is not None and old[0]==f.value:
                            return ApplicationResult(ApplicationState.CONFLICT_REVIEW_REQUIRED)
                        changes.append((f,old_hash))
                    for f,old_hash in changes:
                        if old_hash is None:
                            cur.execute(_INSERT_FORM,(r.store_ref,lead,f.field_key,f.value))
                        else:
                            cur.execute(_UPDATE_FORM,(f.value,r.store_ref,lead,f.field_key))
                            if cur.rowcount!=1:
                                raise RuntimeError('concurrent field CAS changed')
                    cur.execute(_VERSION_AFTER,(r.store_ref,lead))
                    after=cur.fetchone()
                    if after is None or after[0]!=req.version.form+len(changes):
                        raise RuntimeError('form version mutation mismatch')
                    cur.execute(_AUDIT,(
                        r.store_ref,r.closure_event_ref,r.case_ref,lead,
                        principal.actor_id,principal.session_id,req.request_ref,
                        digest,conditions,req.approval_evidence_sha256,
                        req.idempotency_key,req.version.form,after[0],
                        len(changes),req.decision.value))
                    audit=cur.fetchone()
                    if audit is None:
                        raise RuntimeError('missing application audit')
                    for f,old_hash in changes:
                        cur.execute(_AUDIT_ITEM,(audit[0],f.field_key,
                                                 old_hash,_sha(f.value)))
                    # psycopg context commits both fields and audit together.
                    return ApplicationResult(ApplicationState.APPLIED_SYNTHETIC_ONLY)
        except Exception:
            # psycopg transaction manager rolls back on any exception.
            return ApplicationResult(ApplicationState.UNAVAILABLE)

def apply_human_s0_synthetic_fields(
    authorization:str,request:HumanFieldRequest, *,
    identity:IdentityProvider,store:S0F03LocalHumanFieldApplicationStore,
    s1:S1TransactionAuthority|None,key:bytes,
)->ApplicationResult:
    if type(store) is not S0F03LocalHumanFieldApplicationStore or _inputs(request,key) is None:
        return ApplicationResult(ApplicationState.DENIED)
    try:
        principal=identity.verify(authorization)
        if (type(principal) is not Principal
            or type(principal.actor_id) is not uuid.UUID
            or type(principal.session_id) is not uuid.UUID):
            return ApplicationResult(ApplicationState.DENIED)
        return store.apply(principal,request,s1,key)
    except Denied:
        return ApplicationResult(ApplicationState.DENIED)
    except Exception:
        return ApplicationResult(ApplicationState.UNAVAILABLE)
