-- I66 read-only positive/negative ACL probes, inside I64/I65 outer ROLLBACK.
-- I65 requires the legacy facade to be present before this candidate.
do $gate$ begin
 if not pg_catalog.has_schema_privilege('authenticated',
     'prumo_s1_interface','USAGE')
 or not pg_catalog.has_function_privilege('authenticated',
     'prumo_s1_interface.s1_mover_atendimento_sessao(uuid,uuid,uuid,uuid)','EXECUTE')
 or not pg_catalog.has_function_privilege('authenticated',
     'prumo_s1_interface.s1_pausar_operador_sessao(uuid,text)','EXECUTE')
 or not pg_catalog.has_function_privilege('authenticated',
     'prumo_s1_interface.s1_reativar_operador_sessao(uuid)','EXECUTE')
 then raise exception 'I66_BASELINE_LEGACY_FACADE_NOT_ACCESSIBLE' using errcode='42501';end if;
end $gate$;
\echo 'PASS I66-01: legacy authenticated SQL schema and all three EXECUTE grants reproduced'

set local role authenticated;
do $gate$ begin
 begin
  perform prumo_s1_interface.s1_mover_atendimento_sessao(
      null,null,null,null);
  raise exception 'I66_LEGACY_MOVER_DID_NOT_REACH_HELPER';
 exception when insufficient_privilege then
   if SQLERRM not in ('SESSAO_AUTENTICADA_OBRIGATORIA','IDENTIDADE_SESSAO_INVALIDA',
      'CLAIMS_SESSAO_INVALIDOS','SESSAO_REVOGADA_OU_INEXISTENTE') then
    raise exception 'I66_UNEXPECTED_PRE_REVOKE_PERMISSION_ERROR: %',
      SQLERRM;end if;
 end;
end $gate$;
reset role;
\echo 'PASS I66-02: direct caller reached privileged legacy facade before revoke; session still fail-closed'

\ir s1_092_legacy_interface_acl_quarantine_local_only.sql
\echo 'PASS I66-03: candidate removed all schema USAGE and function EXECUTE for client roles'

set local role authenticated;
do $gate$ begin
 begin
  perform prumo_s1_interface.s1_mover_atendimento_sessao(
       null,null,null,null);
  raise exception 'I66_LEGACY_MOVE_STILL_EXECUTED';
 exception when insufficient_privilege then
  if pg_catalog.strpos(pg_catalog.lower(SQLERRM),'permission denied')=0 then
   raise exception 'I66_LEGACY_MOVE_REACHED_HELPER: %',SQLERRM;end if;
 end;
 begin
  perform prumo_s1_interface.s1_pausar_operador_sessao(null,null);
  raise exception 'I66_LEGACY_PAUSE_STILL_EXECUTED';
 exception when insufficient_privilege then
  if pg_catalog.strpos(pg_catalog.lower(SQLERRM),'permission denied')=0 then
   raise exception 'I66_LEGACY_PAUSE_REACHED_HELPER: %',SQLERRM;end if;
 end;
 begin
  perform prumo_s1_interface.s1_reativar_operador_sessao(null);
  raise exception 'I66_LEGACY_RESUME_STILL_EXECUTED';
 exception when insufficient_privilege then
  if pg_catalog.strpos(pg_catalog.lower(SQLERRM),'permission denied')=0 then
   raise exception 'I66_LEGACY_RESUME_REACHED_HELPER: %',SQLERRM;end if;
 end;
end $gate$;
reset role;
\echo 'PASS I66-04: same authenticated role cannot execute MOVE/PAUSE/RESUME legacy facades after revoke'

do $gate$ begin
 if (select count(*) from pg_catalog.pg_proc p
     join pg_catalog.pg_namespace n on n.oid=p.pronamespace
     where n.nspname='prumo_s1_interface')<>3
 or not exists(select 1 from pg_catalog.pg_proc p
     where p.oid='prumo_s1_interface.s1_mover_atendimento_sessao(uuid,uuid,uuid,uuid)'::regprocedure
     and p.prosecdef and pg_catalog.pg_get_userbyid(p.proowner)='postgres')
 or not exists(select 1 from pg_catalog.pg_proc p
     where p.oid='prumo_s1_interface.s1_pausar_operador_sessao(uuid,text)'::regprocedure
     and p.prosecdef and pg_catalog.pg_get_userbyid(p.proowner)='postgres')
 then raise exception 'I66_OWNER_OR_BODY_MUTATED' using errcode='42501';end if;
end $gate$;
\echo 'PASS I66-05: legacy function bodies and owners retained for rollback, privileges only narrowed'

do $gate$ begin
 if pg_catalog.has_function_privilege('authenticated',
    'prumo_private.s1_mover_excecao_caso_i61(uuid,uuid,uuid,uuid,uuid)','EXECUTE')
 or pg_catalog.has_schema_privilege('authenticated','prumo_private','USAGE')
 or pg_catalog.has_table_privilege('authenticated',
    'prumo_private.s1_excecoes_caso_i61','SELECT')
 then raise exception 'I66_PRIVATE_SCOPE_GRANTED' using errcode='42501';end if;
end $gate$;
\echo 'PASS I66-06: canonical I61 private ledger and movement remain inaccessible to raw client SQL'

set local role authenticated;
select pg_catalog.set_config('request.jwt.claim.sub',
 '86310000-0000-4000-8000-000000000004',true);
do $gate$ begin
 if not exists(select 1 from public.casos_humanos
   where id='86350000-0000-4000-8000-000000000003')
 or exists(select 1 from public.casos_humanos
   where id='86350000-0000-4000-8000-000000000001')
 or not exists(select 1 from public.leads_loja
   where id='86330000-0000-4000-8000-000000000002')
 then raise exception 'I66_RLS_SUPERVISOR_READ_DRIFT' using errcode='42501';end if;
end $gate$;
reset role;
\echo 'PASS I66-07: supervisor-specific I63/I64 reads unchanged after legacy ACL quarantine'

do $gate$ declare n int;begin
 select count(*) into n from pg_catalog.pg_proc p
 join pg_catalog.pg_namespace ns on ns.oid=p.pronamespace
 where ns.nspname='prumo_private' and p.prosecdef
  and not exists(select 1 from pg_catalog.unnest(
    coalesce(p.proconfig,array[]::text[])) as cfg(item)
    where cfg.item in ('search_path=','search_path=""'));
 if n<>0 then raise exception 'I66_UNSAFE_PRIVATE_SEARCHPATH: %',n;end if;
end $gate$;
\echo 'PASS I66-08: SECURITY DEFINER protections and prior catalog isolation remain intact'
