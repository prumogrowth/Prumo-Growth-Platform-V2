-- S1-002/I20 - exclusivamente fixture local no Docker CI.
-- NAO E MIGRATION. NAO executar em Supabase hospedado/operacional.
-- O S0 ja tem prova assinada propria; nao a modifica ou reusa segredos.
create schema prumo_s1_signed_i20 authorization postgres;
revoke all on schema prumo_s1_signed_i20 from public,anon,authenticated,service_role;

create role prumo_s1_signed_login_ci login noinherit
 nosuperuser nocreatedb nocreaterole noreplication nobypassrls
 password 'I20_Temporary_Only_Not_Production_2026!';
grant usage on schema prumo_s1_signed_i20 to prumo_s1_signed_login_ci;

create table prumo_s1_signed_i20.chaves(
 id uuid primary key, segredo bytea not null check(octet_length(segredo)>=32),
 valido_desde timestamptz not null,
 valido_ate timestamptz not null, ativo boolean not null default true,
 check(valido_ate>valido_desde)
);
create table prumo_s1_signed_i20.nonces(
 id uuid primary key,
 chave_id uuid not null references prumo_s1_signed_i20.chaves(id),
 usado_em timestamptz not null default clock_timestamp()
);
alter table prumo_s1_signed_i20.chaves enable row level security;
alter table prumo_s1_signed_i20.nonces enable row level security;
revoke all on prumo_s1_signed_i20.chaves,prumo_s1_signed_i20.nonces
 from public,anon,authenticated,service_role,prumo_s1_signed_login_ci;

-- Layout canônico: 6 UUIDs opcionais, motivo do enum ou '-', epoch e nonce.
-- Campos sempre em ordem fixa, sem JSON flutuante e sem texto livre.
create function prumo_s1_signed_i20.material(
 p_operacao text,p_ator uuid,p_sessao uuid,
 p_loja uuid,p_caso uuid,p_atribuicao uuid,p_destino uuid,
 p_operador uuid,p_motivo text,p_emitido bigint,p_nonce uuid
) returns text language sql immutable set search_path='' as $s$
 select pg_catalog.concat_ws('|',
 'prumo-s1-i20-v1',p_operacao,p_ator::text,p_sessao::text,
 coalesce(p_loja::text,'-'),coalesce(p_caso::text,'-'),
 coalesce(p_atribuicao::text,'-'),coalesce(p_destino::text,'-'),
 coalesce(p_operador::text,'-'),coalesce(p_motivo,'-'),
 p_emitido::text,p_nonce::text)
$s$;

create function prumo_s1_signed_i20.invocar(
 p_operacao text,p_ator uuid,p_sessao uuid,
 p_loja uuid,p_caso uuid,p_atribuicao uuid,p_destino uuid,
 p_operador uuid,p_motivo text,
 p_chave uuid,p_emitido bigint,p_nonce uuid,p_hmac text
) returns jsonb language plpgsql security definer set search_path='' as $gw$
declare
 v_agora bigint;
 v_segredo bytea;
 v_material text;
 v_esperada bytea;
 v_criptoschema text;
 v_insert uuid;
 v_resultado jsonb;
begin
 -- Fail closed: esta função é o único comando com EXECUTE pela role SQL.
 if p_ator is null or p_sessao is null or p_chave is null or
    p_emitido is null or p_nonce is null or p_hmac is null or
    p_hmac !~ '^[0-9a-f]{64}$' or
    not (
     (p_operacao='MOVER' and p_loja is not null and p_caso is not null
      and p_atribuicao is not null and p_destino is not null
      and p_operador is null and p_motivo is null)
     or (p_operacao='PAUSAR' and p_operador is not null
      and p_motivo in ('AUSENCIA_TEMPORARIA','INDISPONIBILIDADE_OPERACIONAL')
      and p_loja is null and p_caso is null and p_atribuicao is null and p_destino is null)
     or (p_operacao='REATIVAR' and p_operador is not null
      and p_motivo is null and p_loja is null and p_caso is null
      and p_atribuicao is null and p_destino is null)
    ) then
  raise exception 'PROVA_S1_INVALIDA' using errcode='42501';
 end if;
 v_agora:=extract(epoch from pg_catalog.clock_timestamp())::bigint;
 if p_emitido<v_agora-30 or p_emitido>v_agora+5 then
  raise exception 'PROVA_S1_EXPIRADA' using errcode='42501';
 end if;
 select k.segredo into v_segredo from prumo_s1_signed_i20.chaves k
 where k.id=p_chave and k.ativo and k.valido_desde<=pg_catalog.to_timestamp(p_emitido)
   and k.valido_ate>pg_catalog.clock_timestamp()
 for share of k;
 if not found then
  raise exception 'PROVA_S1_SEM_CHAVE_ATIVA' using errcode='42501';
 end if;
 select n.nspname into v_criptoschema from pg_catalog.pg_extension e
 join pg_catalog.pg_namespace n on n.oid=e.extnamespace
 where e.extname='pgcrypto';
 if v_criptoschema is null then
  raise exception 'HMAC_S1_INDISPONIVEL' using errcode='42501';
 end if;
 v_material:=prumo_s1_signed_i20.material(
  p_operacao,p_ator,p_sessao,p_loja,p_caso,p_atribuicao,p_destino,
  p_operador,p_motivo,p_emitido,p_nonce);
 execute pg_catalog.format('select %I.hmac($1,$2,''sha256'')',v_criptoschema)
 into v_esperada using pg_catalog.convert_to(v_material,'UTF8'),v_segredo;
 if v_esperada is distinct from pg_catalog.decode(p_hmac,'hex') then
  raise exception 'PROVA_S1_ASSINATURA_INVALIDA' using errcode='42501';
 end if;
 insert into prumo_s1_signed_i20.nonces(id,chave_id)
 values(p_nonce,p_chave) on conflict do nothing returning id into v_insert;
 if v_insert is null then
  raise exception 'PROVA_S1_REUTILIZADA' using errcode='42501';
 end if;

 -- Só apos HMAC válida e nonce inédito materializamos o contexto GoTrue.
 -- Nem a role SQL nem o corpo HTTP do usuário podem chamar fachadas diretas.
 perform pg_catalog.set_config('request.jwt.claims',
  pg_catalog.jsonb_build_object('role','authenticated','sub',p_ator::text,
    'session_id',p_sessao::text)::text,true);
 perform pg_catalog.set_config('request.jwt.claim.sub',p_ator::text,true);
 perform pg_catalog.set_config('request.jwt.claim.role','authenticated',true);
 if p_operacao='MOVER' then
  v_resultado:=prumo_s1_interface.s1_mover_atendimento_sessao(
   p_loja,p_caso,p_atribuicao,p_destino);
 elsif p_operacao='PAUSAR' then
  v_resultado:=prumo_s1_interface.s1_pausar_operador_sessao(p_operador,p_motivo);
 else
  v_resultado:=prumo_s1_interface.s1_reativar_operador_sessao(p_operador);
 end if;
 return v_resultado;
end $gw$;

revoke all on function
 prumo_s1_signed_i20.material(text,uuid,uuid,uuid,uuid,uuid,uuid,uuid,text,bigint,uuid)
 from public,anon,authenticated,service_role,prumo_s1_signed_login_ci;
revoke all on function
 prumo_s1_signed_i20.invocar(
 text,uuid,uuid,uuid,uuid,uuid,uuid,uuid,text,uuid,bigint,uuid,text)
 from public,anon,authenticated,service_role,prumo_s1_signed_login_ci;
grant execute on function
 prumo_s1_signed_i20.invocar(
 text,uuid,uuid,uuid,uuid,uuid,uuid,uuid,text,uuid,bigint,uuid,text)
 to prumo_s1_signed_login_ci;
