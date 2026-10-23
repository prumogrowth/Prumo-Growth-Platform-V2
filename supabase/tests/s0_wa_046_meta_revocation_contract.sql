\set ON_ERROR_STOP on
-- WA42 / S0-046: SQL catalog privileges and rollback-safe revoke fixtures.
begin;
do $wa42_assert$
declare fn oid;
begin
 fn:='prumo_private.meta_verificar_handoff_fixture_s0(
 uuid,text,text,text,uuid,uuid,text,text,text,text,text,text,text,bigint,uuid,text)'::regprocedure;
 if (select proowner::regrole::text from pg_catalog.pg_proc where oid=fn)
  <>'prumo_s0_meta_signer_lab' then raise exception 'WA42-01 owner';end if;
 raise notice 'WA42-01 PASS';
 if position('wa42-meta-key:' in pg_catalog.pg_get_functiondef(fn))=0
  or position('pg_advisory_xact_lock' in pg_catalog.pg_get_functiondef(fn))=0
 then raise exception 'WA42-02 verifier lock missing';end if;
 raise notice 'WA42-02 PASS';
 if position('wa42-meta-key:' in
   pg_catalog.pg_get_functiondef('prumo_private.meta_revogar_chave_fixture_s0(uuid)'::regprocedure))=0
 then raise exception 'WA42-03 revoker lock missing';end if;
 raise notice 'WA42-03 PASS';
 if not (select prosecdef from pg_catalog.pg_proc where oid=fn)
 then raise exception 'WA42-04 must isolate signer';end if;
 raise notice 'WA42-04 PASS';
 if pg_catalog.has_table_privilege('prumo_s0_meta_signer_lab',
   'prumo_private.meta_servico_chaves_fixture_s0','UPDATE')
 then raise exception 'WA42-05 signer can revoke key';end if;
 raise notice 'WA42-05 PASS';
 if pg_catalog.has_function_privilege('prumo_s0_meta_ingress_lab',
  'prumo_private.meta_revogar_chave_fixture_s0(uuid)','EXECUTE')
 then raise exception 'WA42-06 ingress can revoke';end if;
 raise notice 'WA42-06 PASS';
 if exists(select 1 from (values('anon'),('authenticated'),('service_role'),
  ('prumo_s0_gateway'),('prumo_s0_signer'),('prumo_s0_signed_executor'))
  roles(name) where pg_catalog.has_function_privilege(roles.name,
   'prumo_private.meta_revogar_chave_fixture_s0(uuid)','EXECUTE'))
 then raise exception 'WA42-07 commercial grants';end if;
 raise notice 'WA42-07 PASS';
 if (select p.proowner::regrole::text from pg_catalog.pg_proc p
     where p.oid='prumo_private.meta_revogar_chave_fixture_s0(uuid)'::regprocedure)
   <>'postgres'
 then raise exception 'WA42-08 unexpected revoker owner';end if;
 raise notice 'WA42-08 PASS';
 if pg_catalog.has_schema_privilege('prumo_s0_meta_signer_lab',
  'prumo_private','CREATE')
 then raise exception 'WA42-09 CREATE leak';end if;
 raise notice 'WA42-09 PASS';
 if pg_catalog.has_table_privilege('prumo_s0_meta_ingress_lab',
  'prumo_private.meta_servico_nonces_fixture_s0','SELECT')
 then raise exception 'WA42-10 nonce visibility';end if;
 raise notice 'WA42-10 PASS';
end $wa42_assert$;
insert into prumo_private.meta_servico_chaves_fixture_s0(
 chave_id,app_technical_ref,segredo,valido_desde,valido_ate,ativo)
values('f7600000-0000-4000-8000-000000000001','99999000001',
 pg_catalog.decode(pg_catalog.repeat('54',48),'hex'),
 pg_catalog.clock_timestamp()-interval '30 seconds',
 pg_catalog.clock_timestamp()+interval '30 minutes',true);
do $wa42_function$
declare v text;
begin
 v:=prumo_private.meta_revogar_chave_fixture_s0(
  'f7600000-0000-4000-8000-000000000001');
 if v<>'LAB_REVOKED'
  or (select ativo from prumo_private.meta_servico_chaves_fixture_s0
       where chave_id='f7600000-0000-4000-8000-000000000001')
 then raise exception 'WA42-11 revoke unsuccessful';end if;
 raise notice 'WA42-11 PASS';
 v:=prumo_private.meta_revogar_chave_fixture_s0(
  'f7600000-0000-4000-8000-000000000001');
 if v<>'LAB_ALREADY_REVOKED'
 then raise exception 'WA42-12 revocation not idempotent';end if;
 raise notice 'WA42-12 PASS';
end $wa42_function$;
rollback;
