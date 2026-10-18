\set ON_ERROR_STOP on
begin;
do $priv$
declare v_proc oid;
begin
 if not exists(select 1 from pg_catalog.pg_roles where rolname='prumo_s0_signer'
   and not rolcanlogin and not rolinherit and not rolsuper and not rolbypassrls
   and not rolcreatedb and not rolcreaterole)
 then raise exception 'FAIL OWNER-01: signer role can login/inherit/escalate';end if;
 if exists(select 1 from pg_catalog.pg_auth_members am
   join pg_catalog.pg_roles member_role on member_role.oid=am.member
   where am.roleid='prumo_s0_signer'::regrole
     and member_role.rolname not in ('postgres','supabase_admin'))
 then raise exception 'FAIL OWNER-01: non-admin role inherits signer privileges';end if;
 v_proc:='prumo_private.gateway_validar_prova_s0(
 text,uuid,uuid,uuid,uuid,bigint,text,text,uuid,uuid,bigint,uuid,text)'::regprocedure::oid;
 if not exists(select 1 from pg_catalog.pg_proc
   where oid=v_proc and prosecdef and
     pg_catalog.pg_get_userbyid(proowner)='prumo_s0_signer')
 then raise exception 'FAIL OWNER-01: HMAC validator still owned by privileged postgres';end if;
 if has_function_privilege('prumo_s0_gateway',v_proc,'EXECUTE')
 or has_function_privilege('anon',v_proc,'EXECUTE')
 or has_function_privilege('authenticated',v_proc,'EXECUTE')
 or has_function_privilege('service_role',v_proc,'EXECUTE')
 then raise exception 'FAIL OWNER-01: direct verifier exposure';end if;
end $priv$;
\echo 'PASS OWNER-01: validador HMAC tem dono restrito NOLOGIN e nao e executavel externamente'

do $priv$
begin
 if not has_column_privilege('prumo_s0_signer',
    'prumo_private.gateway_chaves_assinatura_s0','segredo','SELECT')
 or not has_column_privilege('prumo_s0_signer',
    'prumo_private.gateway_provas_usadas_s0','nonce','INSERT')
 or has_column_privilege('prumo_s0_signer',
    'prumo_private.gateway_chaves_assinatura_s0','motivo_revogacao','SELECT')
 or has_table_privilege('prumo_s0_signer','public.leads_loja','SELECT')

 or has_table_privilege('prumo_s0_signer',
    'prumo_private.gateway_eventos_chave_s0','INSERT')
 or has_function_privilege('prumo_s0_signer',
    'prumo_private.gateway_cancelar_plano_assinado_s0(uuid,uuid,uuid,uuid,bigint,uuid,bigint,uuid,text)',
    'EXECUTE')
 or has_function_privilege('prumo_s0_signer',
    'prumo_private.alterar_estado_chave_gateway_s0(uuid,bigint,boolean,text)',
    'EXECUTE')
 then raise exception 'FAIL OWNER-02: verifier has commercial or administrative privileges';end if;
 if pg_catalog.to_regclass('auth.sessions') is not null then
  if has_table_privilege('prumo_s0_signer','auth.sessions','SELECT')
  then raise exception 'FAIL OWNER-02: signer can read Supabase sessions';end if;
 end if;
end $priv$;
\echo 'PASS OWNER-02: dono do validador tem somente grants tecnicos e nao acessa dados comerciais'

-- Both signed application entrypoints still run as postgres for compatibility
-- with legacy domain functions, making this only a partial hardening.
do $scope$
begin
 if not exists(select 1 from pg_catalog.pg_proc p where
   p.oid='prumo_private.gateway_cancelar_plano_assinado_s0(
     uuid,uuid,uuid,uuid,bigint,uuid,bigint,uuid,text)'::regprocedure::oid
   and p.prosecdef and pg_catalog.pg_get_userbyid(p.proowner)='postgres')
 or not exists(select 1 from pg_catalog.pg_proc p where
   p.oid='prumo_private.gateway_conciliar_c07_assinado_s0(
     uuid,uuid,uuid,uuid,bigint,text,text,uuid,uuid,bigint,uuid,text)'::regprocedure::oid
   and p.prosecdef and pg_catalog.pg_get_userbyid(p.proowner)='postgres')
 then raise exception 'FAIL OWNER-03: unexpected domain entrypoint ownership';end if;
end $scope$;
\echo 'PASS OWNER-03: limite declarado -- wrappers de dominio ainda exigem revisao do owner postgres'
rollback;
