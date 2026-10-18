-- S0/031: opt-in synthetic C01 importer using the vetted S0/028/030
-- identity resolver. NEVER a Meta/Bank API or real mobile-ownership proof.
-- Existing importar_lote_sintetico stays untouched.
-- p_mobile_confirmado_sintetico is ONLY an administrator-authored TEST fixture.
create function prumo_private.importar_lote_identidade_s0(
 p_ator uuid,p_loja uuid,p_chave text,p_linhas jsonb
) returns jsonb language plpgsql security invoker set search_path='' as $fn$
declare
 v_hash text;v_lote uuid;v_anterior text;v_linha jsonb;v_tel text;
 v_mobile boolean;v_resultado jsonb;v_lead uuid;v_novo boolean;
 v_ordem integer:=0;v_aceitos integer:=0;v_rejeitados integer:=0;
 v_revisao integer:=0;v_motivo text;
begin
 if current_user<>'postgres' then
  raise exception 'INTERNAL_ONLY' using errcode='42501';end if;
 if not exists(
  select 1 from public.concessionarias c
  join public.vinculos_papel_escopo v on v.concessionaria_id=c.id
  where c.id=p_loja and c.ativo and v.ator_id=p_ator and v.papel='gestor'
   and v.valido_desde<=pg_catalog.statement_timestamp()
   and (v.valido_ate is null or v.valido_ate>pg_catalog.statement_timestamp())
 ) then raise exception 'FORBIDDEN_SCOPE' using errcode='42501';end if;
 if p_chave is null or pg_catalog.length(pg_catalog.btrim(p_chave)) not between 1 and 160
    or pg_catalog.jsonb_typeof(p_linhas) is distinct from 'array'
 then raise exception 'INVALID_BATCH' using errcode='22023';end if;
 if pg_catalog.jsonb_array_length(p_linhas) not between 1 and 100
 then raise exception 'INVALID_BATCH_SIZE' using errcode='22023';end if;
 -- Domain-separation tag prevents a legacy C01 call with the same key and
 -- payload from being misinterpreted as an idempotent replay of this importer.
 v_hash:=pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(
   'PRUMO-S0-C01-ALIAS-V1|'||p_linhas::text,'UTF8')),'hex');
 perform pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(
   's0-c01-alias:'||p_loja::text||':'||p_chave,31));
 select id,payload_fingerprint into v_lote,v_anterior
 from public.lotes_importacao
 where concessionaria_id=p_loja and chave_importacao=p_chave;
 if found then
  if v_anterior is distinct from v_hash then
   raise exception 'CONFLICT_IDEMPOTENCY_KEY' using errcode='23505';end if;
  return pg_catalog.jsonb_build_object('outcome','ALREADY_APPLIED','lote_id',v_lote);
 end if;
 insert into public.lotes_importacao(
    concessionaria_id,chave_importacao,payload_fingerprint)
 values(p_loja,p_chave,v_hash) returning id into v_lote;
 for v_linha in select value from pg_catalog.jsonb_array_elements(p_linhas) loop
  v_ordem:=v_ordem+1;
  v_tel:=null;v_mobile:=null;v_motivo:=null;v_lead:=null;v_novo:=false;
  if pg_catalog.jsonb_typeof(v_linha)='object'
     and pg_catalog.jsonb_typeof(v_linha->'telefone')='string' then
   v_tel:=v_linha->>'telefone';end if;
  if v_tel is null or v_tel !~ '^\+[1-9][0-9]{9,14}$' then
   v_motivo:='TELEFONE_INVALIDO';
  elsif pg_catalog.jsonb_typeof(v_linha->'mobile_confirmado_sintetico') is distinct from 'boolean' then
   v_motivo:='EVIDENCIA_FIXTURE_INVALIDA';
  else
   v_mobile:=(v_linha->>'mobile_confirmado_sintetico')::boolean;
   if v_mobile and prumo_private.chave_variante_br_s0(v_tel) is null then
    v_motivo:='MOVEL_FIXTURE_NAO_ELEGIVEL';
   end if;
  end if;
  if v_motivo is null then
   v_resultado:=prumo_private.resolver_contato_s0(
      p_loja,v_tel,'IMPORTACAO_SINTETICA',v_mobile);
   if v_resultado->>'outcome' in ('IDENTITY_CONFLICT','NEEDS_REVIEW') then
    v_motivo:=case when v_resultado->>'outcome'='IDENTITY_CONFLICT'
      then 'IDENTIDADE_CONFLITANTE' else 'IDENTIDADE_EM_REVISAO' end;
    v_revisao:=v_revisao+1;
   else
    v_lead:=(v_resultado->>'lead_id')::uuid;
    v_novo:=(v_resultado->>'lead_criado')::boolean;
    if v_lead is null then
     raise exception 'INVALID_IDENTITY_RESOLUTION' using errcode='40001';end if;
   end if;
  end if;
  if v_motivo is not null then
   insert into public.itens_lote(concessionaria_id,lote_id,ordinal_linha,
      resultado,motivo_rejeicao)
   values(p_loja,v_lote,v_ordem,'rejeitado',v_motivo);
   v_rejeitados:=v_rejeitados+1;
   continue;
  end if;
  insert into public.itens_lote(concessionaria_id,lote_id,ordinal_linha,lead_id)
  values(p_loja,v_lote,v_ordem,v_lead);
  if v_novo then
   insert into public.ciclos_comerciais(concessionaria_id,lead_id)
    values(p_loja,v_lead);
  else
   insert into public.reencontros_lote(concessionaria_id,lote_id,lead_id)
    values(p_loja,v_lote,v_lead) on conflict do nothing;
  end if;
  v_aceitos:=v_aceitos+1;
 end loop;
 return pg_catalog.jsonb_build_object(
  'outcome','APPLIED','lote_id',v_lote,
  'aceitos',v_aceitos,'rejeitados',v_rejeitados,'em_revisao',v_revisao);
end $fn$;
revoke all on function prumo_private.importar_lote_identidade_s0(
 uuid,uuid,text,jsonb)
 from public,anon,authenticated,service_role,prumo_s0_gateway,prumo_s0_signer;
