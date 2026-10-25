"""S0 E04-only identity ambiguity query for synthetic lead/form CAS.

A phone or its Brazilian mobile variant is a *candidate*, never identity.
No automatic merge or permission; shop transaction advisory lock required.
"""
_DUPLICATE_LEAD_CANDIDATE = """with current_numbers as (
 select l.telefone_cliente_normalizado as numero
 from public.leads_loja l
 where l.concessionaria_id=%s::uuid and l.id=%s::uuid
 union
 select a.numero_sintetico as numero
 from prumo_private.aliases_identidade_s0 a
 where a.concessionaria_id=%s::uuid and a.lead_id=%s::uuid
), other_numbers as (
 select l.id as lead_id,l.telefone_cliente_normalizado as numero
 from public.leads_loja l
 where l.concessionaria_id=%s::uuid and l.id<>%s::uuid
 union all
 select a.lead_id,a.numero_sintetico
 from prumo_private.aliases_identidade_s0 a
 where a.concessionaria_id=%s::uuid and a.lead_id<>%s::uuid
)
select 1 from current_numbers c join other_numbers o on
 c.numero=o.numero or (
 prumo_private.chave_variante_br_s0(c.numero) is not null
 and prumo_private.chave_variante_br_s0(c.numero)
   =prumo_private.chave_variante_br_s0(o.numero))
limit 1"""

def conflicting_lead_candidate(cur,shop,lead)->bool:
    """Caller MUST hold s0_f03_lock_shop_local(shop) in same S0 txn."""
    cur.execute(_DUPLICATE_LEAD_CANDIDATE,(shop,lead,shop,lead,shop,lead,shop,lead))
    return cur.fetchone() is not None
