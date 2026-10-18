-- S0/028: DEC-WA-01/02. SYNTHETIC identities only. Not a Meta endpoint.
-- No production phone, external credentials or new commercial authority.
-- Existing C01/C02 signatures and tables remain intact; this is a private
-- opt-in compatibility path pending explicit physical integration review.
create table prumo_private.aliases_identidade_s0(
 id uuid primary key default gen_random_uuid(),
 concessionaria_id uuid not null,
 lead_id uuid not null,
 numero_sintetico text not null check (numero_sintetico ~ '^\+[1-9][0-9]{9,14}$'),
 chave_variante_sintetica text,
 origem text not null check (origem in ('CANAL_SINTETICO','IMPORTACAO_SINTETICA')),
 mobile_confirmado_sintetico boolean not null,
 registrado_em timestamptz not null default statement_timestamp(),
 unique(concessionaria_id,numero_sintetico),
 foreign key(concessionaria_id,lead_id) references public.leads_loja(concessionaria_id,id)
);
create index aliases_identidade_s0_variantes
 on prumo_private.aliases_identidade_s0(concessionaria_id,chave_variante_sintetica)
 where mobile_confirmado_sintetico;
create table prumo_private.eventos_identidade_s0(
 id bigint generated always as identity primary key,
 concessionaria_id uuid not null,
 lead_id uuid not null,
 alias_id uuid not null references prumo_private.aliases_identidade_s0(id),
 decisao text not null check(decisao in ('NEW_SCOPED_CONTACT','MATCH_EXACT','MATCH_CANONICAL_VARIANT')),
 registrado_em timestamptz not null default statement_timestamp(),
 foreign key(concessionaria_id,lead_id) references public.leads_loja(concessionaria_id,id)
);
-- An ambiguous input must survive without choosing an arbitrary lead.
create table prumo_private.pendencias_identidade_s0(
 id uuid primary key default gen_random_uuid(),
 concessionaria_id uuid not null,
 canal_id uuid not null,
 id_externo text not null,
 telefone_sintetico text not null,
 texto_sintetico text not null,
 motivo text not null check(motivo in ('IDENTITY_CONFLICT','NEEDS_REVIEW')),
 registrado_em timestamptz not null default statement_timestamp(),
 unique(concessionaria_id,canal_id,id_externo),
 foreign key(concessionaria_id,canal_id) references public.canais_loja(concessionaria_id,id)
);
alter table prumo_private.aliases_identidade_s0 enable row level security;
alter table prumo_private.eventos_identidade_s0 enable row level security;
alter table prumo_private.pendencias_identidade_s0 enable row level security;
revoke all on prumo_private.aliases_identidade_s0,
 prumo_private.eventos_identidade_s0,prumo_private.pendencias_identidade_s0
 from public,anon,authenticated,service_role,prumo_s0_gateway,prumo_s0_signer;

-- Comparison key is NOT a civil identity and must never become a send address.
-- The 8-digit form participates ONLY with explicit synthetic mobile evidence.
create function prumo_private.chave_variante_br_s0(p_numero text)
returns text language sql immutable set search_path='' as $sql$
 select case
  when p_numero ~ '^\+55[1-9][0-9]9[0-9]{8}$'
    then pg_catalog.left(p_numero,5)||pg_catalog.right(p_numero,8)
  when p_numero ~ '^\+55[1-9][0-9][0-9]{8}$'
    then pg_catalog.left(p_numero,5)||pg_catalog.right(p_numero,8)
  else null end
$sql$;

create function prumo_private.resolver_contato_s0(
 p_loja uuid,p_numero text,p_origem text,p_mobile_confirmado boolean
) returns jsonb language plpgsql security invoker set search_path='' as $fn$
declare v_chave text; v_lead uuid; v_numero_principal text;v_alias uuid;
 v_total integer;v_criado boolean:=false;v_decisao text;v_bloqueados integer;
begin
 if current_user<>'postgres' then raise exception 'INTERNAL_ONLY' using errcode='42501';end if;
 if p_loja is null or p_numero is null
    or p_numero !~ '^\+[1-9][0-9]{9,14}$'
    or p_origem not in ('CANAL_SINTETICO','IMPORTACAO_SINTETICA')
    or p_origem is null or p_mobile_confirmado is null
 then raise exception 'IDENTITY_ARGUMENT_INVALID' using errcode='22023';end if;
 if not exists(select 1 from public.concessionarias where id=p_loja and ativo)
 then raise exception 'INVALID_SCOPE' using errcode='42501';end if;
 v_chave:=case when p_mobile_confirmado
   then prumo_private.chave_variante_br_s0(p_numero) else null end;
 if p_mobile_confirmado and v_chave is null
 then raise exception 'MOBILE_EVIDENCE_INELIGIBLE' using errcode='22023';end if;
 -- Serialize all compatible variants inside the SAME shop, never globally.
 perform pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(
   's0-id:'||p_loja::text||':'||coalesce(v_chave,p_numero),0));
 -- An exact legacy lead or confirmed alias can pre-exist migration 028.
 select l.id,l.telefone_cliente_normalizado into v_lead,v_numero_principal
 from public.leads_loja l where l.concessionaria_id=p_loja
 and l.telefone_cliente_normalizado=p_numero;
 if v_lead is null then
  select a.lead_id,l.telefone_cliente_normalizado into v_lead,v_numero_principal
  from prumo_private.aliases_identidade_s0 a
  join public.leads_loja l on l.id=a.lead_id and l.concessionaria_id=a.concessionaria_id
  where a.concessionaria_id=p_loja and a.numero_sintetico=p_numero;
 end if;
 -- Never silently join two existing leads: even legacy unverified numbers
 -- may signify shared/recycled/fixed contacts.
 if v_chave is not null then
  select count(distinct candidate.lead_id) into v_total from (
    select l.id as lead_id from public.leads_loja l
     where l.concessionaria_id=p_loja
       and prumo_private.chave_variante_br_s0(l.telefone_cliente_normalizado)=v_chave
    union all
    select a.lead_id from prumo_private.aliases_identidade_s0 a
     where a.concessionaria_id=p_loja and a.chave_variante_sintetica=v_chave
       and a.mobile_confirmado_sintetico
  ) candidate;
  if v_total>1 then return pg_catalog.jsonb_build_object(
    'outcome','IDENTITY_CONFLICT','lead_id',null);end if;
  if v_lead is null then
   select a.lead_id,l.telefone_cliente_normalizado into v_lead,v_numero_principal
   from prumo_private.aliases_identidade_s0 a
   join public.leads_loja l on l.concessionaria_id=a.concessionaria_id and l.id=a.lead_id
   where a.concessionaria_id=p_loja and a.chave_variante_sintetica=v_chave
     and a.mobile_confirmado_sintetico
   order by a.registrado_em limit 1;
  end if;
  if v_lead is null and v_total>0 then
   -- A matching old phone without explicit mobile evidence is not enough
   -- to merge its history with a different representation.
   return pg_catalog.jsonb_build_object('outcome','NEEDS_REVIEW','lead_id',null);
  end if;
 end if;
 if v_lead is null then
  insert into public.leads_loja(concessionaria_id,telefone_cliente_normalizado)
   values(p_loja,p_numero)
   on conflict(concessionaria_id,telefone_cliente_normalizado) do nothing
   returning id into v_lead;
  v_criado:=(v_lead is not null);
  if v_lead is null then
   select id into v_lead from public.leads_loja
    where concessionaria_id=p_loja and telefone_cliente_normalizado=p_numero;
  end if;
  v_numero_principal:=p_numero;
 end if;
 if v_lead is null then raise exception 'CONCURRENT_LEAD_RETRY' using errcode='40001';end if;
 v_decisao:=case when v_criado then 'NEW_SCOPED_CONTACT'
   when v_numero_principal=p_numero then 'MATCH_EXACT'
   else 'MATCH_CANONICAL_VARIANT' end;
 insert into prumo_private.aliases_identidade_s0(
  concessionaria_id,lead_id,numero_sintetico,chave_variante_sintetica,
  origem,mobile_confirmado_sintetico)
 values(p_loja,v_lead,p_numero,v_chave,p_origem,p_mobile_confirmado)
 on conflict(concessionaria_id,numero_sintetico) do nothing
 returning id into v_alias;
 if v_alias is not null then
  insert into prumo_private.eventos_identidade_s0(concessionaria_id,lead_id,alias_id,decisao)
   values(p_loja,v_lead,v_alias,v_decisao);
 else
  -- Existing alias must not be silently rebound to another lead.
  if exists(select 1 from prumo_private.aliases_identidade_s0
   where concessionaria_id=p_loja and numero_sintetico=p_numero
   and lead_id<>v_lead) then
   return pg_catalog.jsonb_build_object('outcome','IDENTITY_CONFLICT','lead_id',null);
  end if;
 end if;
 return pg_catalog.jsonb_build_object('outcome',v_decisao,
   'lead_id',v_lead,'numero_principal_sintetico',v_numero_principal,
   'lead_criado',v_criado);
end $fn$;

-- Adapter for synthetic C02 only; leaves original C02 contract untouched.
-- p_mobile_confirmado is a trusted TEST FIXTURE assertion, not client input.
create function prumo_private.receber_mensagem_identidade_s0(
 p_canal uuid,p_numero text,p_id_externo text,p_texto text,
 p_mobile_confirmado boolean
) returns jsonb language plpgsql security invoker set search_path='' as $fn$
declare v_loja uuid;v_res jsonb;v_motivo text;
begin
 if current_user<>'postgres' then raise exception 'INTERNAL_ONLY' using errcode='42501';end if;
 select c.concessionaria_id into v_loja
 from public.canais_loja c join public.concessionarias l
 on l.id=c.concessionaria_id and l.ativo
 where c.id=p_canal and c.modo='simulado';
 if v_loja is null then raise exception 'UNKNOWN_CHANNEL' using errcode='22023';end if;
 if p_id_externo is null or p_id_externo !~ '^[A-Za-z0-9_.:-]{1,120}$'
 or p_texto is null or length(btrim(p_texto)) not between 1 and 1024
 then raise exception 'INVALID_INBOUND_SYNTHETIC' using errcode='22023';end if;
 v_res:=prumo_private.resolver_contato_s0(
   v_loja,p_numero,'CANAL_SINTETICO',p_mobile_confirmado);
 if v_res->>'outcome' in ('IDENTITY_CONFLICT','NEEDS_REVIEW') then
  v_motivo:=v_res->>'outcome';
  insert into prumo_private.pendencias_identidade_s0(
    concessionaria_id,canal_id,id_externo,telefone_sintetico,texto_sintetico,motivo)
  values(v_loja,p_canal,p_id_externo,p_numero,p_texto,v_motivo)
  on conflict(concessionaria_id,canal_id,id_externo) do nothing;
  return pg_catalog.jsonb_build_object('outcome',v_motivo,'roteamento','HUMANO_PENDENTE');
 end if;
 return prumo_private.receber_mensagem_sintetica(
   p_canal,v_res->>'numero_principal_sintetico',p_id_externo,p_texto);
end $fn$;

revoke all on function prumo_private.chave_variante_br_s0(text),
 prumo_private.resolver_contato_s0(uuid,text,text,boolean),
 prumo_private.receber_mensagem_identidade_s0(uuid,text,text,text,boolean)
 from public,anon,authenticated,service_role,prumo_s0_gateway,prumo_s0_signer;
