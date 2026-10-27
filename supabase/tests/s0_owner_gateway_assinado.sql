\set ON_ERROR_STOP on
begin;
do $owner$
declare p oid;
begin
 if not exists(select 1 from pg_catalog.pg_roles r
 where r.rolname='prumo_s0_signed_executor' and not r.rolcanlogin
 and not r.rolinherit and not r.rolsuper and not r.rolcreatedb
 and not r.rolcreaterole and not r.rolreplication and not r.rolbypassrls)
 then raise exception 'FAIL OWNER-04: signed executor not restricted';end if;
 if exists(select 1 from pg_catalog.pg_auth_members a
 join pg_catalog.pg_roles m on m.oid=a.member
 where a.roleid='prumo_s0_signed_executor'::regrole
 and m.rolname not in ('postgres','supabase_admin'))
 then raise exception 'FAIL OWNER-04: untrusted member';end if;
 if not exists(select 1 from pg_catalog.pg_auth_members a
 join pg_catalog.pg_roles m on m.oid=a.member
 where a.roleid='prumo_s0_signed_executor'::regrole
 and m.rolname='postgres' and a.set_option and not a.inherit_option)
 then raise exception 'FAIL OWNER-04: managed postgres lacks SET-only role grant';end if;
 foreach p in array array[
 'prumo_private.gateway_cancelar_plano_assinado_s0(uuid,uuid,uuid,uuid,bigint,uuid,bigint,uuid,text)'::regprocedure::oid,
 'prumo_private.gateway_conciliar_c07_assinado_s0(uuid,uuid,uuid,uuid,bigint,text,text,uuid,uuid,bigint,uuid,text)'::regprocedure::oid
 ] loop
  if not exists(select 1 from pg_catalog.pg_proc f where f.oid=p
    and f.prosecdef and pg_catalog.pg_get_userbyid(f.proowner)='prumo_s0_signed_executor')
  then raise exception 'FAIL OWNER-04: signed function still postgres-owned';end if;
  if not has_function_privilege('prumo_s0_gateway',p,'EXECUTE')
   or has_function_privilege('anon',p,'EXECUTE')
   or has_function_privilege('authenticated',p,'EXECUTE')
   or has_function_privilege('service_role',p,'EXECUTE')
   or has_function_privilege('prumo_s0_signer',p,'EXECUTE')
  then raise exception 'FAIL OWNER-04: signed entrypoint ACL widened';end if;
 end loop;
end $owner$;
\echo 'PASS OWNER-04: assinadas têm dono técnico NOLOGIN e acesso gateway mínimo'

do $owner$
begin
 if has_schema_privilege('prumo_s0_signed_executor','prumo_private','CREATE')
 or not has_schema_privilege('prumo_s0_signed_executor','prumo_private','USAGE')
 or has_table_privilege('prumo_s0_signed_executor','public.leads_loja','SELECT')
 or has_table_privilege('prumo_s0_signed_executor','public.planos_recontato_sinteticos','UPDATE')
 or has_table_privilege('prumo_s0_signed_executor',
  'public.pendencias_reconciliacao_c07_sinteticas','UPDATE')
 or has_table_privilege('prumo_s0_signed_executor',
  'prumo_private.gateway_chaves_assinatura_s0','SELECT')
 or has_table_privilege('prumo_s0_signed_executor',
  'prumo_private.gateway_provas_usadas_s0','INSERT')
 or has_table_privilege('prumo_s0_signed_executor',
  'prumo_private.auditoria_gateway_s0','INSERT')
 or has_function_privilege('prumo_s0_signed_executor',
  'prumo_private.cancelar_plano_gestor_sintetico(uuid,uuid,uuid,bigint)','EXECUTE')
 or has_function_privilege('prumo_s0_signed_executor',
  'prumo_private.conciliar_pendencia_c07_sintetica(uuid,uuid,uuid,bigint,text,text,uuid)','EXECUTE')
 then raise exception 'FAIL OWNER-05: executor has direct privileged DML or raw domain';end if;
 if to_regclass('auth.sessions') is not null and
   has_table_privilege('prumo_s0_signed_executor','auth.sessions','SELECT')
 then raise exception 'FAIL OWNER-05: executor can read sessions';end if;
 if not has_function_privilege('prumo_s0_signed_executor',
  'prumo_private.gateway_validar_prova_s0(text,uuid,uuid,uuid,uuid,bigint,text,text,uuid,uuid,bigint,uuid,text)','EXECUTE')
 or not has_function_privilege('prumo_s0_signed_executor',
  'prumo_private.gateway_cancelar_plano_s0(uuid,uuid,uuid,uuid,bigint)','EXECUTE')
 or not has_function_privilege('prumo_s0_signed_executor',
  'prumo_private.gateway_conciliar_c07_s0(uuid,uuid,uuid,uuid,bigint,text,text,uuid)','EXECUTE')
 then raise exception 'FAIL OWNER-05: narrow dependencies missing';end if;
end $owner$;
\echo 'PASS OWNER-05: executor sem leitura comercial/segredos/sessoes, apenas chamadas delegadas'

do $owner$
declare p oid;
begin
 foreach p in array array[
 'prumo_private.gateway_cancelar_plano_s0(uuid,uuid,uuid,uuid,bigint)'::regprocedure::oid,
 'prumo_private.gateway_conciliar_c07_s0(uuid,uuid,uuid,uuid,bigint,text,text,uuid)'::regprocedure::oid
 ] loop
  if not exists(select 1 from pg_catalog.pg_proc f where f.oid=p
    and f.prosecdef and pg_catalog.pg_get_userbyid(f.proowner)='postgres')
  then raise exception 'FAIL OWNER-06: legacy owner unexpectedly changed';end if;
  if has_function_privilege('prumo_s0_gateway',p,'EXECUTE')
   or has_function_privilege('anon',p,'EXECUTE')
   or has_function_privilege('authenticated',p,'EXECUTE')
   or has_function_privilege('service_role',p,'EXECUTE')
  then raise exception 'FAIL OWNER-06: unsigned domain wrapper callable by public/gateway';end if;
 end loop;
 if has_function_privilege('prumo_s0_gateway',
   'prumo_private.gateway_validar_prova_s0(text,uuid,uuid,uuid,uuid,bigint,text,text,uuid,uuid,bigint,uuid,text)','EXECUTE')
 or has_function_privilege('prumo_s0_gateway',
   'prumo_private.cancelar_plano_gestor_sintetico(uuid,uuid,uuid,bigint)','EXECUTE')
 then raise exception 'FAIL OWNER-06: HMAC bypass available';end if;
end $owner$;
\echo 'PASS OWNER-06: legadas postgres restritas, gateway sem rota sem HMAC'
rollback;
