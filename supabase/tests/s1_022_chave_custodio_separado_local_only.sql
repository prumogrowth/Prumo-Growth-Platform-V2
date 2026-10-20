-- S1-002/I22 - fixture somente Docker local CI, DEPOIS de I20 e I21.
-- Separa custodia da chave (NOLOGIN) do executor da transacao/nonce (NOLOGIN).
-- NAO E MIGRATION, SEM executacao no Supabase hospedado, SEM segredo real.
begin;
do $guard$
begin
 if current_user <> 'postgres'
   then raise exception 'I22_ONLY_LOCAL_POSTGRES' using errcode='42501';end if;
 if exists(select 1 from pg_catalog.pg_roles
   where rolname='prumo_s1_i22_custodio')
 then raise exception 'I22_ROLE_EXISTS' using errcode='42501'; end if;
 create role prumo_s1_i22_custodio nologin noinherit
  nosuperuser nocreatedb nocreaterole noreplication nobypassrls;
 grant prumo_s1_i22_custodio to postgres with inherit false, set true;
end $guard$;
grant usage on schema prumo_s1_signed_i20 to prumo_s1_i22_custodio;
grant execute on function prumo_s1_signed_i20.material(
 text,uuid,uuid,uuid,uuid,uuid,uuid,uuid,text,bigint,uuid)
 to prumo_s1_i22_custodio;
-- Apenas o custodio pode invocar pgcrypto com o material da chave.
do $crypt$
declare schema_name text;
begin
 select n.nspname into schema_name
 from pg_catalog.pg_extension e join pg_catalog.pg_namespace n
 on n.oid=e.extnamespace where e.extname='pgcrypto';
 if schema_name is null
 then raise exception 'I22_PGCRYPTO_ABSENT' using errcode='42501';end if;
 execute pg_catalog.format('grant usage on schema %I to prumo_s1_i22_custodio',schema_name);
 execute pg_catalog.format(
  'grant execute on function %I.hmac(bytea,bytea,text) to prumo_s1_i22_custodio',
  schema_name);
end $crypt$;

-- A rotina so retorna VOID. Nenhuma chave/bytes/booleano HMAC sai.
-- Lock consultado por administracao e pelo verificador antes da leitura
-- evita validar uma chave simultaneamente revogada.
create function prumo_s1_signed_i20.verificar_hmac(
 p_operacao text,p_ator uuid,p_sessao uuid,
 p_loja uuid,p_caso uuid,p_atribuicao uuid,p_destino uuid,
 p_operador uuid,p_motivo text,p_chave uuid,p_emitido bigint,
 p_nonce uuid,p_hmac text
) returns void language plpgsql security definer set search_path='' as $fn$
declare
 v_segredo bytea;
 v_material text;
 v_esperada bytea;
 v_schema text;
begin
 if p_chave is null or p_emitido is null or p_nonce is null
  or p_hmac is null or p_hmac !~ '^[0-9a-f]{64}$'
 then raise exception 'I22_PROOF_INVALID' using errcode='42501';end if;
 perform pg_catalog.pg_advisory_xact_lock(
  pg_catalog.hashtextextended('prumo-s1-key-v1:'||p_chave::text,0));
 select c.segredo into v_segredo
 from prumo_s1_signed_i20.chaves c
 where c.id=p_chave and c.ativo
  and c.valido_desde<=pg_catalog.to_timestamp(p_emitido)
  and c.valido_ate>pg_catalog.clock_timestamp();
 if not found then
  raise exception 'I22_PROOF_INVALID' using errcode='42501';end if;
 select n.nspname into v_schema
 from pg_catalog.pg_extension e join pg_catalog.pg_namespace n
 on n.oid=e.extnamespace where e.extname='pgcrypto';
 if v_schema is null then
  raise exception 'I22_PGCRYPTO_MISSING' using errcode='42501';end if;
 v_material:=prumo_s1_signed_i20.material(
  p_operacao,p_ator,p_sessao,p_loja,p_caso,p_atribuicao,
  p_destino,p_operador,p_motivo,p_emitido,p_nonce);
 execute pg_catalog.format('select %I.hmac($1,$2,''sha256'')',v_schema)
  into v_esperada using pg_catalog.convert_to(v_material,'UTF8'),v_segredo;
 if v_esperada is distinct from pg_catalog.decode(p_hmac,'hex')
 then raise exception 'I22_PROOF_INVALID' using errcode='42501';end if;
end $fn$;

-- Grants removidos ainda sob owner postgres; a nova role NOLOGIN recebe
-- o ownership com CREATE temporario somente dentro da transacao.
revoke all on function prumo_s1_signed_i20.verificar_hmac(
 text,uuid,uuid,uuid,uuid,uuid,uuid,uuid,text,uuid,bigint,uuid,text)
 from public,anon,authenticated,service_role,prumo_s1_signed_login_ci,
  prumo_s1_i21_executor,prumo_s1_i22_custodio;
grant execute on function prumo_s1_signed_i20.verificar_hmac(
 text,uuid,uuid,uuid,uuid,uuid,uuid,uuid,text,uuid,bigint,uuid,text)
 to prumo_s1_i21_executor;

grant create on schema prumo_s1_signed_i20 to prumo_s1_i22_custodio;
alter table prumo_s1_signed_i20.chaves owner to prumo_s1_i22_custodio;
alter function prumo_s1_signed_i20.verificar_hmac(
 text,uuid,uuid,uuid,uuid,uuid,uuid,uuid,text,uuid,bigint,uuid,text)
 owner to prumo_s1_i22_custodio;
revoke create on schema prumo_s1_signed_i20 from prumo_s1_i22_custodio;

-- O executor nao le a tabela de chaves nem a altera. Cuida so da
-- gravacao de nonces e da transacao de negocio (via interfaces I14).
revoke all on prumo_s1_signed_i20.chaves from
 prumo_s1_i21_executor,prumo_s1_signed_login_ci,public,anon,authenticated,service_role;
revoke all on prumo_s1_signed_i20.nonces from
 prumo_s1_i22_custodio,prumo_s1_signed_login_ci,public,anon,authenticated,service_role;

-- Para reescrever o corpo existente e preservar o ownership da funcao,
-- concede-se CREATE somente na transacao atual e executa-se como seu owner.
grant create on schema prumo_s1_signed_i20 to prumo_s1_i21_executor;
set local role prumo_s1_i21_executor;
create or replace function prumo_s1_signed_i20.invocar(
 p_operacao text,p_ator uuid,p_sessao uuid,
 p_loja uuid,p_caso uuid,p_atribuicao uuid,p_destino uuid,
 p_operador uuid,p_motivo text,
 p_chave uuid,p_emitido bigint,p_nonce uuid,p_hmac text
) returns jsonb language plpgsql security definer set search_path='' as $gw$
declare
 v_agora bigint;
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
 perform prumo_s1_signed_i20.verificar_hmac(
   p_operacao,p_ator,p_sessao,p_loja,p_caso,p_atribuicao,p_destino,
   p_operador,p_motivo,p_chave,p_emitido,p_nonce,p_hmac);
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

reset role;
revoke create on schema prumo_s1_signed_i20 from prumo_s1_i21_executor;

-- Check fail-closed da matriz ANTES do COMMIT.
do $assert$
declare fn_owner text; key_owner text; nonce_owner text; check_owner text;
begin
 select pg_catalog.pg_get_userbyid(p.proowner) into fn_owner
 from pg_catalog.pg_proc p where p.oid='prumo_s1_signed_i20.invocar(
 text,uuid,uuid,uuid,uuid,uuid,uuid,uuid,text,uuid,bigint,uuid,text)'::regprocedure;
 select pg_catalog.pg_get_userbyid(p.proowner) into check_owner
 from pg_catalog.pg_proc p where p.oid='prumo_s1_signed_i20.verificar_hmac(
 text,uuid,uuid,uuid,uuid,uuid,uuid,uuid,text,uuid,bigint,uuid,text)'::regprocedure;
 select pg_catalog.pg_get_userbyid(c.relowner) into key_owner
 from pg_catalog.pg_class c where c.oid='prumo_s1_signed_i20.chaves'::regclass;
 select pg_catalog.pg_get_userbyid(c.relowner) into nonce_owner
 from pg_catalog.pg_class c where c.oid='prumo_s1_signed_i20.nonces'::regclass;
 if fn_owner<>'prumo_s1_i21_executor' or nonce_owner<>'prumo_s1_i21_executor'
  or key_owner<>'prumo_s1_i22_custodio' or check_owner<>'prumo_s1_i22_custodio'
  or has_table_privilege('prumo_s1_i21_executor','prumo_s1_signed_i20.chaves','SELECT')
  or has_table_privilege('prumo_s1_i21_executor','prumo_s1_signed_i20.chaves','UPDATE')
  or has_table_privilege('prumo_s1_i22_custodio','prumo_s1_signed_i20.nonces','INSERT')
  or has_schema_privilege('prumo_s1_i22_custodio','prumo_s1_signed_i20','CREATE')
  or has_schema_privilege('prumo_s1_i21_executor','prumo_s1_signed_i20','CREATE')
  or pg_has_role('prumo_s1_i21_executor','prumo_s1_i22_custodio','MEMBER')
  or has_function_privilege('prumo_s1_signed_login_ci',
   'prumo_s1_signed_i20.verificar_hmac(
   text,uuid,uuid,uuid,uuid,uuid,uuid,uuid,text,uuid,bigint,uuid,text)','EXECUTE')
 then raise exception 'I22_ACL_ISOLATION_FAILED' using errcode='42501';end if;
end $assert$;
commit;
