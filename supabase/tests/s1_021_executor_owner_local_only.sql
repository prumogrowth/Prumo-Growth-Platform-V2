-- S1-002/I21: evolucao somente no CI descartavel, APLICAR DEPOIS DA FIXTURE I20.
-- Nunca converter em migration, nunca executar contra Supabase hospedado.
-- Invocador assinado deixa de ser propriedade de postgres: executor NOLOGIN
-- não tem BYPASSRLS, SUPERUSER, CREATE, login ou escrita comercial direta.
do $guard$
begin
 if current_user<>'postgres' then
  raise exception 'I21_POSTGRES_LOCAL_REQUIRED' using errcode='42501';
 end if;
 if exists(select 1 from pg_roles where rolname='prumo_s1_i21_executor') then
  raise exception 'I21_ROLE_ALREADY_EXISTS' using errcode='42501';
 end if;
 create role prumo_s1_i21_executor nologin noinherit
  nosuperuser nocreatedb nocreaterole noreplication nobypassrls;
 -- PostgreSQL gerenciado exige capacidade SET ROLE para ALTER OWNER.
 grant prumo_s1_i21_executor to postgres with inherit false, set true;
end $guard$;

grant usage on schema prumo_s1_signed_i20,prumo_s1_interface
 to prumo_s1_i21_executor;
grant execute on function prumo_s1_signed_i20.material(
 text,uuid,uuid,uuid,uuid,uuid,uuid,uuid,text,bigint,uuid)
 to prumo_s1_i21_executor;
grant execute on function prumo_s1_interface.s1_mover_atendimento_sessao(
 uuid,uuid,uuid,uuid) to prumo_s1_i21_executor;
grant execute on function prumo_s1_interface.s1_pausar_operador_sessao(
 uuid,text) to prumo_s1_i21_executor;
grant execute on function prumo_s1_interface.s1_reativar_operador_sessao(
 uuid) to prumo_s1_i21_executor;

-- Schema pgcrypto pode ser específico do Supabase (prumo_crypto/extensions).
-- O verificador local necessita apenas de executar hmac; não recebe CREATE.
do $pgcrypto$
declare s text;
begin
 select n.nspname into s
 from pg_catalog.pg_extension e join pg_catalog.pg_namespace n
  on n.oid=e.extnamespace where e.extname='pgcrypto';
 if s is null then
  raise exception 'I21_PGCRYPTO_REQUIRED' using errcode='42501';
 end if;
 execute pg_catalog.format('grant usage on schema %I to prumo_s1_i21_executor',s);
end $pgcrypto$;

-- Esta etapa transfere a posse das DUAS tabelas efêmeras: o executor
-- consegue ler chave e consumir nonce SEM precisar de UPDATE amplo
-- em tabela de terceiros ou BYPASSRLS. A role é NOLOGIN e o login SQL
-- NÃO pode SET ROLE para ela; ownership de tabela será auditado no teste.
-- Não herdar este desenho sem revisão operacional de custódia de chaves.
-- Preserva manutenção e inspeção por postgres APENAS no sandbox.
-- Role postgres tinha posse original; grants explícitos não alcançam login CI.
grant select,insert,update,delete on prumo_s1_signed_i20.chaves,
 prumo_s1_signed_i20.nonces to postgres;
grant create on schema prumo_s1_signed_i20 to prumo_s1_i21_executor;
alter table prumo_s1_signed_i20.chaves owner to prumo_s1_i21_executor;
alter table prumo_s1_signed_i20.nonces owner to prumo_s1_i21_executor;

-- Transferir a única fachada assinada, preservando grants ao login SQL,
-- signature, comportamento, SQL e owner das três fachadas privadas I14.
alter function prumo_s1_signed_i20.invocar(
 text,uuid,uuid,uuid,uuid,uuid,uuid,uuid,text,uuid,bigint,uuid,text)
 owner to prumo_s1_i21_executor;
revoke create on schema prumo_s1_signed_i20 from prumo_s1_i21_executor;

-- O login SQL fica restrito a USAGE do schema e EXECUTE da única entrada;
-- outras formas de acesso e os grants I14 continuam vedados.
revoke all on schema prumo_s1_interface,prumo_private from prumo_s1_signed_login_ci;
revoke all on prumo_s1_signed_i20.chaves,prumo_s1_signed_i20.nonces
 from prumo_s1_signed_login_ci;

do $assert$
declare v text;
begin
 select pg_catalog.pg_get_userbyid(p.proowner) into v
 from pg_catalog.pg_proc p
 where p.oid='prumo_s1_signed_i20.invocar(
 text,uuid,uuid,uuid,uuid,uuid,uuid,uuid,text,uuid,bigint,uuid,text)'::regprocedure;
 if v is distinct from 'prumo_s1_i21_executor'
 or has_schema_privilege('prumo_s1_i21_executor','prumo_s1_signed_i20','CREATE')
 or pg_has_role('prumo_s1_signed_login_ci','prumo_s1_i21_executor','MEMBER')
 or has_schema_privilege('prumo_s1_signed_login_ci','prumo_s1_interface','USAGE')
 then
  raise exception 'I21_OWNER_OR_ACL_MISMATCH' using errcode='42501';
 end if;
end $assert$;
