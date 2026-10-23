\set ON_ERROR_STOP on
-- I48: PG17 complete S0/013-037 catalog assertions; no DDL/DML.
do $audit$
declare
 raw_fn oid; signed_fn oid; reconcile_fn oid; verifier oid; trigger_fn oid;
 gateway_role oid; signer_role oid; exec_role oid; owner_name text;
 def_count int; rel_count int;
begin
 select oid into gateway_role from pg_catalog.pg_roles where rolname='prumo_s0_gateway';
 select oid into signer_role from pg_catalog.pg_roles where rolname='prumo_s0_signer';
 select oid into exec_role from pg_catalog.pg_roles where rolname='prumo_s0_signed_executor';
 if gateway_role is null or signer_role is null or exec_role is null then
  raise exception 'I48: missing S0 gateway roles';
 end if;
 if exists(select 1 from pg_catalog.pg_roles where oid in
 (gateway_role,signer_role,exec_role) and (rolcanlogin or rolsuper or rolbypassrls)) then
  raise exception 'I48: dangerous gateway role properties';
 end if;
 if exists(select 1 from pg_catalog.pg_auth_members am
 join pg_catalog.pg_roles mr on mr.oid=am.member
 where am.roleid in (gateway_role,signer_role,exec_role)
 and mr.rolname not in ('postgres','supabase_admin')) then
  raise exception 'I48: sensitive role delegated outside admin allowlist';
 end if;
 if pg_catalog.pg_has_role('authenticated'::regrole,gateway_role,'member')
 or pg_catalog.pg_has_role('authenticated'::regrole,signer_role,'member')
 or pg_catalog.pg_has_role('authenticated'::regrole,exec_role,'member')
 then raise exception 'I48: authenticated is gateway role member';
 end if;
 select oid into raw_fn from pg_catalog.pg_proc where pronamespace='prumo_private'::regnamespace
 and proname='gateway_cancelar_plano_s0';
 select oid into signed_fn from pg_catalog.pg_proc where pronamespace='prumo_private'::regnamespace
 and proname='gateway_cancelar_plano_assinado_s0';
 select oid into reconcile_fn from pg_catalog.pg_proc where pronamespace='prumo_private'::regnamespace
 and proname='gateway_conciliar_c07_assinado_s0';
 select oid into verifier from pg_catalog.pg_proc where pronamespace='prumo_private'::regnamespace
 and proname='gateway_validar_prova_s0';
 select oid into trigger_fn from pg_catalog.pg_proc where pronamespace='prumo_private'::regnamespace
 and proname='auditar_rotacao_gateway_s0';
 if raw_fn is null or signed_fn is null or reconcile_fn is null
 or verifier is null or trigger_fn is null then
  raise exception 'I48: missing gateway functions';
 end if;
 if pg_catalog.has_function_privilege(gateway_role,raw_fn,'EXECUTE')
 or pg_catalog.has_function_privilege(gateway_role,verifier,'EXECUTE')
 or not pg_catalog.has_function_privilege(gateway_role,signed_fn,'EXECUTE')
 or not pg_catalog.has_function_privilege(gateway_role,reconcile_fn,'EXECUTE')
 then raise exception 'I48: invalid gateway EXECUTE topology';
 end if;
 if exists(select 1 from pg_catalog.pg_proc p join pg_catalog.pg_roles r on r.oid=p.proowner
 where (p.oid=verifier and r.rolname<>'prumo_s0_signer')
 or (p.oid in (signed_fn,reconcile_fn) and r.rolname<>'prumo_s0_signed_executor'))
 then raise exception 'I48: gateway ownership boundary broken';
 end if;
 if exists(select 1 from unnest(array[raw_fn,signed_fn,reconcile_fn,verifier,trigger_fn]) f(oid)
 where pg_catalog.has_function_privilege('authenticated',f.oid,'EXECUTE')
 or pg_catalog.has_function_privilege('anon',f.oid,'EXECUTE'))
 then raise exception 'I48: untrusted direct EXECUTE on gateway functions';
 end if;
 if pg_catalog.has_table_privilege('authenticated','prumo_private.gateway_chaves_assinatura_s0','SELECT')
 or pg_catalog.has_table_privilege(gateway_role,'prumo_private.gateway_chaves_assinatura_s0','SELECT')
 or pg_catalog.has_table_privilege(gateway_role,'public.leads_loja','SELECT')
 then raise exception 'I48: direct gateway access to secrets or leads';
 end if;
 select count(*) into def_count from pg_catalog.pg_proc
 where pronamespace='prumo_private'::regnamespace and prosecdef;
 select count(*) into rel_count from pg_catalog.pg_class c
 join pg_catalog.pg_namespace n on n.oid=c.relnamespace
 where n.nspname='public' and c.relname in
 ('evidencias_elegibilidade_sinteticas','supressoes_contato_sinteticas')
 and c.relrowsecurity and pg_catalog.has_table_privilege('authenticated',c.oid,'SELECT');
 if def_count<4 or rel_count<>2 then
  raise exception 'I48: incomplete catalog; definers %, optout %',def_count,rel_count;
 end if;
 raise notice 'PASS I48-CATALOG-01: non-login gateway/signer/executor role graph';
 raise notice 'PASS I48-CATALOG-02: signed function ownership and EXECUTE boundary';
 raise notice 'PASS I48-CATALOG-03: untrusted roles cannot call gateway/HMAC or read secrets';
 raise notice 'PASS I48-CATALOG-04: S0/016 RLS present; private definers %',def_count;
end
$audit$;
