\set ON_ERROR_STOP on
-- WA41: ACL and ownership checks on real S0/045 lab objects; ROLLBACK.
begin;
do $wa41_tests$
declare v_verifier oid;v_wrapper oid;
 v_signer text:='prumo_s0_meta_signer_lab';
 v_function text:='prumo_private.meta_verificar_handoff_fixture_s0(uuid,text,text,text,uuid,uuid,text,text,text,text,text,text,text,bigint,uuid,text)';
 v_material text:='prumo_private.meta_material_handoff_fixture_s0(uuid,text,text,text,uuid,uuid,text,text,text,text,text,text,text,bigint,uuid)';
 v_write text:='prumo_private.archivar_status_meta_tecnico_fixture_s0(text,text,text,uuid,uuid,text,text,text,text,text,text,text)';
begin
 if not exists(select 1 from pg_catalog.pg_roles where rolname=v_signer
  and not rolcanlogin and not rolinherit and not rolsuper and not rolbypassrls
  and not rolcreatedb and not rolcreaterole and not rolreplication)
 then raise exception 'WA41-01 unsafe signer role';end if;
 raise notice 'WA41-01 PASS';

 if exists(select 1 from pg_catalog.pg_auth_members am
  join pg_catalog.pg_roles r on r.oid=am.member
  where am.roleid=v_signer::regrole and r.rolname not in ('postgres','supabase_admin'))
 then raise exception 'WA41-02 delegated signer';end if;
 raise notice 'WA41-02 PASS';

 v_verifier:=v_function::regprocedure;
 if (select p.proowner::regrole::text from pg_catalog.pg_proc p
     where p.oid=v_verifier)<>v_signer
 then raise exception 'WA41-03 verifier owner';end if;
 raise notice 'WA41-03 PASS';

 if not (select p.prosecdef from pg_catalog.pg_proc p where p.oid=v_verifier)
   or position('search_path=' in pg_catalog.pg_get_functiondef(v_verifier))=0
 then raise exception 'WA41-04 not restricted definer';end if;
 raise notice 'WA41-04 PASS';

 v_wrapper:='prumo_private.meta_arquivar_handoff_assinado_fixture_s0(uuid,text,text,text,uuid,uuid,text,text,text,text,text,text,text,bigint,uuid,text)'::regprocedure;
 if (select p.proowner::regrole::text from pg_catalog.pg_proc p where p.oid=v_wrapper)<>'postgres'
 then raise exception 'WA41-05 expected explicit privileged DOMAIN wrapper';end if;
 raise notice 'WA41-05 PASS';

 if pg_catalog.has_function_privilege('prumo_s0_meta_ingress_lab',v_verifier,'EXECUTE')
 then raise exception 'WA41-06 ingress can call signer directly';end if;
 raise notice 'WA41-06 PASS';

 if exists(select 1 from (values('anon'),('authenticated'),('service_role'),
   ('prumo_s0_gateway'),('prumo_s0_signer'),('prumo_s0_signed_executor')) v(role)
  where pg_catalog.has_function_privilege(v.role,v_verifier,'EXECUTE'))
 then raise exception 'WA41-07 browser or human roles can verify';end if;
 raise notice 'WA41-07 PASS';

 if not pg_catalog.has_function_privilege('postgres',v_verifier,'EXECUTE')
 then raise exception 'WA41-08 wrapper cannot call verifier';end if;
 raise notice 'WA41-08 PASS';

 if not pg_catalog.has_table_privilege(v_signer,'prumo_private.meta_servico_chaves_fixture_s0','SELECT')
  or pg_catalog.has_table_privilege(v_signer,'prumo_private.meta_servico_chaves_fixture_s0','UPDATE')
  or pg_catalog.has_table_privilege(v_signer,'prumo_private.meta_servico_chaves_fixture_s0','DELETE')
  or pg_catalog.has_table_privilege(v_signer,'prumo_private.meta_servico_chaves_fixture_s0','INSERT')
 then raise exception 'WA41-09 key privileges too wide';end if;
 raise notice 'WA41-09 PASS';

 if not pg_catalog.has_table_privilege(v_signer,'prumo_private.meta_servico_nonces_fixture_s0','INSERT')
  or not pg_catalog.has_table_privilege(v_signer,'prumo_private.meta_servico_nonces_fixture_s0','SELECT')
  or pg_catalog.has_table_privilege(v_signer,'prumo_private.meta_servico_nonces_fixture_s0','UPDATE')
  or pg_catalog.has_table_privilege(v_signer,'prumo_private.meta_servico_nonces_fixture_s0','DELETE')
 then raise exception 'WA41-10 nonce privileges too wide';end if;
 raise notice 'WA41-10 PASS';

 if pg_catalog.has_function_privilege(v_signer,v_write,'EXECUTE')
  or pg_catalog.has_table_privilege(v_signer,'prumo_private.meta_status_forense_fixture_s0','SELECT')
  or pg_catalog.has_table_privilege(v_signer,'prumo_private.meta_status_forense_fixture_s0','INSERT')
 then raise exception 'WA41-11 verifier has forensic write';end if;
 raise notice 'WA41-11 PASS';

 if (select count(*) from pg_catalog.pg_policies
   where schemaname='prumo_private' and tablename='meta_servico_chaves_fixture_s0'
   and policyname='wa41_signer_keys_select')<>1
 or (select count(*) from pg_catalog.pg_policies
   where schemaname='prumo_private' and tablename='meta_servico_nonces_fixture_s0'
   and policyname like 'wa41_signer_nonces_%')<>2
 then raise exception 'WA41-12 RLS missing';end if;
 raise notice 'WA41-12 PASS';

 if pg_catalog.has_schema_privilege(v_signer,'prumo_private','CREATE')
 then raise exception 'WA41-13 verifier can create S0 objects';end if;
 raise notice 'WA41-13 PASS';

 if pg_catalog.has_table_privilege('prumo_s0_meta_ingress_lab',
     'prumo_private.meta_servico_chaves_fixture_s0','SELECT')
  or pg_catalog.has_table_privilege('service_role',
     'prumo_private.meta_servico_nonces_fixture_s0','SELECT')
 then raise exception 'WA41-14 secret or nonce disclosed';end if;
 raise notice 'WA41-14 PASS';

 if pg_catalog.has_function_privilege(v_signer,
    'prumo_private.gateway_cancelar_plano_assinado_s0(uuid,uuid,uuid,uuid,bigint,uuid,bigint,uuid,text)','EXECUTE')
 then raise exception 'WA41-15 human gateway reachable';end if;
 raise notice 'WA41-15 PASS';

 if not pg_catalog.has_function_privilege(v_signer,v_material,'EXECUTE')
  or pg_catalog.has_function_privilege('anon',v_material,'EXECUTE')
 then raise exception 'WA41-16 material scope invalid';end if;
 raise notice 'WA41-16 PASS';
end $wa41_tests$;
rollback;
