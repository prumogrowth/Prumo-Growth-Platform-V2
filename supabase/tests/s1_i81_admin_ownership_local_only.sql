-- I81: administrative domain ownership, NOT case dispatch or Auth ownership.
-- Disposable PG17 only, after the EXACT certified I80. No hosted migration.
begin;
set local lock_timeout='3s';
set local statement_timeout='20s';
do $guard$
declare x record;p record;
begin
 if current_user<>'postgres' or session_user<>'postgres' or current_database()<>'postgres'
 or current_setting('server_version_num')::int/10000<>17
 or current_setting('prumo.i81_disposable',true) is distinct from 'YES'
 then raise exception 'I81_DISPOSABLE_ONLY' using errcode='42501';end if;
 -- Unknown/drifted bodies fail BEFORE creating any role, policy or grant.
 for x in select * from (values
 ('prumo_private.s1_exigir_executor_interno_equipe()','bd4a56f41cf9bcd39e26ebbb1e2aa3e1024ce27a4d4bd7173ff738af4f6a98ff',false),
 ('prumo_private.s1_i79_admin_bridge(uuid,uuid,text,uuid,text,uuid,bigint,text,uuid)','8e3414e01794e3a3d8a3c3bdcd20382343a44056be67470781d137935794646d',true),
 ('prumo_private.s1_i80_snapshot(uuid,uuid)','53659cd61ee4f51c998dd6446bbf2612780d90d38aa2c4820a5471b5ed7090e4',false),
 ('prumo_private.s1_i80_bridge(uuid,uuid,text,uuid,text,uuid,text,uuid,uuid,integer,text,uuid)','5c6c608b5efde5b4a12f3bb65e1d97fec981f2a534c19496dc14eb87788668bb',true),
 ('prumo_private.s1_i79_consistencia()','a57ff123bd7adffbadd0cf0856a93d8ea92b89acb3377b33b25935c75fead416',true),
 ('public.s0_verificar_atribuicao()','2f4033ec636f13e4f9465d75e2855def28e0957ce5f61cb8f3a8a9b7bb116821',false),
 ('prumo_private.s1_validar_nova_atribuicao()','92cd4b2cfd212ca931e41ea90c33a29d6013d459736543b9562ba18d325fdc0f',false),
 ('prumo_private.s1_prova_excecao_i61(uuid,uuid,uuid,uuid)','89bcd3febf28e8da6a1ec03f74c3a2fc1fe53b242b4b64f6b716b4edf94ea57c',false)
 ) v(signature,digest,is_definer)
 loop
  select pg_get_userbyid(proowner) as owner,prosecdef,prosrc into p
  from pg_proc where oid=to_regprocedure(x.signature);
  if not found or p.owner<>'postgres' or p.prosecdef<>x.is_definer
   or encode(sha256(convert_to(p.prosrc,'UTF8')),'hex')<>x.digest
  then raise exception 'I81_PREREQUISITE_DRIFT: %',x.signature using errcode='42501';end if;
 end loop;
end $guard$;

create role prumo_s1_admin_domain_local nologin noinherit nosuperuser nocreatedb nocreaterole noreplication nobypassrls;
create role prumo_s1_professional_validator_local nologin noinherit nosuperuser nocreatedb nocreaterole noreplication nobypassrls;
grant usage on schema public,prumo_private to prumo_s1_admin_domain_local,prumo_s1_professional_validator_local;

-- Preserve the original I46 guard, INVOKER, error and all trigger attachments.
-- Only the inaccessible administrative domain is added to the executor set.
-- No JWT/GUC/role membership predicate can impersonate that current_user.
do $patch$
declare d text;
begin
 d:=pg_get_functiondef('prumo_private.s1_exigir_executor_interno_equipe()'::regprocedure);
 execute replace(d,'if current_user<>''postgres'' then',
  'if current_user not in (''postgres'',''prumo_s1_admin_domain_local'') then');
end $patch$;

-- Auth keeps its ownership and ACLs. This tiny fixed-schema boolean shim
-- exposes no email/JWT/metadata; only domain EXECUTE. REGISTER retains the
-- original FOR SHARE identity lock; I80 inventory retains its nonlocking read.
create function prumo_private.s1_i81_auth_identity_exists(p_actor uuid,p_lock boolean)
returns boolean language plpgsql security definer set search_path='' as $auth$
begin
 if p_actor is null or p_lock is null then return false;end if;
 if p_lock then
  perform 1 from auth.users u where u.id=p_actor for share;
 else
  perform 1 from auth.users u where u.id=p_actor;
 end if;
 return found;
end $auth$;
revoke all on function prumo_private.s1_i81_auth_identity_exists(uuid,boolean)
 from public,anon,authenticated,service_role,prumo_cfi01_pgtest_login,prumo_s0_g1_executor_local;
grant execute on function prumo_private.s1_i81_auth_identity_exists(uuid,boolean) to prumo_s1_admin_domain_local;
grant execute on function prumo_private.cfi01_session_valid_local(uuid,uuid) to prumo_s1_admin_domain_local;
do $patch$
declare d text;
begin
 d:=pg_get_functiondef('prumo_private.s1_i79_admin_bridge(uuid,uuid,text,uuid,text,uuid,bigint,text,uuid)'::regprocedure);
 execute replace(d,'perform 1 from auth.users u where u.id=p_target for share;'||chr(10)||'   if not found then',
  'if not prumo_private.s1_i81_auth_identity_exists(p_target,true) then');
 d:=pg_get_functiondef('prumo_private.s1_i80_snapshot(uuid,uuid)'::regprocedure);
 execute replace(d,'exists(select 1 from auth.users u where u.id=p_target)',
  'prumo_private.s1_i81_auth_identity_exists(p_target,false)');
end $patch$;

-- Explicit object and column privileges, NO table/schema ownership transfer.
grant select(id),insert(id),update(id) on public.atores to prumo_s1_admin_domain_local;
grant select on public.equipe_prumo_s1 to prumo_s1_admin_domain_local,prumo_s1_professional_validator_local;
grant insert(ator_id,cargo,estado),update(cargo,estado) on public.equipe_prumo_s1 to prumo_s1_admin_domain_local;
grant update(ator_id) on public.equipe_prumo_s1 to prumo_s1_professional_validator_local;
grant insert(ator_id,estado_anterior,estado_posterior) on public.equipe_prumo_eventos_s1 to prumo_s1_admin_domain_local;
grant select on prumo_private.s1_gestor_operadores,prumo_private.s1_responsaveis_plataforma
 to prumo_s1_admin_domain_local,prumo_s1_professional_validator_local;
grant insert(gestor_id,operador_id),update(encerrado_em) on prumo_private.s1_gestor_operadores to prumo_s1_admin_domain_local;
-- Locking SELECT requires UPDATE ACL, but WITH CHECK(false) bars row changes.
grant update(ator_id) on prumo_private.s1_responsaveis_plataforma to prumo_s1_admin_domain_local;
grant select on public.vinculos_papel_escopo,prumo_private.s1_intake_estado to prumo_s1_admin_domain_local;
grant update(id) on public.vinculos_papel_escopo to prumo_s1_admin_domain_local;
grant update(operador_id) on prumo_private.s1_intake_estado to prumo_s1_admin_domain_local;
grant select(id,concessionaria_id,caso_id,operador_id,atribuida_em,encerrada_em),update(id)
 on public.atribuicoes_humanas to prumo_s1_admin_domain_local;
grant select(id,concessionaria_id,lead_id,ciclo_id),update(id) on public.casos_humanos to prumo_s1_admin_domain_local;
grant select,update(revogada_em) on prumo_private.s1_excecoes_caso_i61 to prumo_s1_admin_domain_local;
grant insert(excecao_id,evento,solicitante_id) on prumo_private.s1_excecoes_caso_eventos_i61 to prumo_s1_admin_domain_local;
grant usage on sequence prumo_private.s1_gestor_operadores_id_seq,prumo_private.s1_excecoes_caso_eventos_i61_id_seq
 to prumo_s1_admin_domain_local;
grant select,insert on prumo_private.s1_i79_requests,prumo_private.s1_i79_audit,
 prumo_private.s1_i80_previews,prumo_private.s1_i80_applications,prumo_private.s1_i80_audit to prumo_s1_admin_domain_local;

-- Role-specific policies do not widen authenticated/service_role policies.
do $policies$
declare t text;
begin
 foreach t in array array['public.atores','public.equipe_prumo_s1','prumo_private.s1_responsaveis_plataforma',
  'prumo_private.s1_gestor_operadores','public.vinculos_papel_escopo','prumo_private.s1_intake_estado',
  'public.atribuicoes_humanas','public.casos_humanos','prumo_private.s1_excecoes_caso_i61',
  'prumo_private.s1_i79_requests','prumo_private.s1_i79_audit','prumo_private.s1_i80_previews',
  'prumo_private.s1_i80_applications','prumo_private.s1_i80_audit']
 loop
  execute format('create policy i81_domain_read on %s for select to prumo_s1_admin_domain_local using(true)',t);
 end loop;
 foreach t in array array['public.atores','prumo_private.s1_responsaveis_plataforma','public.vinculos_papel_escopo',
  'prumo_private.s1_intake_estado','public.atribuicoes_humanas','public.casos_humanos']
 loop
  execute format('create policy i81_domain_lock on %s for update to prumo_s1_admin_domain_local using(true) with check(false)',t);
 end loop;
 foreach t in array array['public.equipe_prumo_eventos_s1','prumo_private.s1_gestor_operadores',
  'prumo_private.s1_excecoes_caso_eventos_i61','prumo_private.s1_i79_requests','prumo_private.s1_i79_audit',
  'prumo_private.s1_i80_previews','prumo_private.s1_i80_applications','prumo_private.s1_i80_audit']
 loop
  execute format('create policy i81_domain_insert on %s for insert to prumo_s1_admin_domain_local with check(true)',t);
 end loop;
 foreach t in array array['public.equipe_prumo_s1','prumo_private.s1_gestor_operadores','prumo_private.s1_responsaveis_plataforma']
 loop
  execute format('create policy i81_validator_read on %s for select to prumo_s1_professional_validator_local using(true)',t);
 end loop;
end $policies$;
create policy i81_domain_register on public.atores for insert to prumo_s1_admin_domain_local with check(true);
create policy i81_domain_register on public.equipe_prumo_s1 for insert to prumo_s1_admin_domain_local
 with check(cargo in('gestor','consultor') and estado='pendente');
create policy i81_domain_classify on public.equipe_prumo_s1 for update to prumo_s1_admin_domain_local
 using(true) with check(cargo in('gestor','consultor'));
create policy i81_domain_close on prumo_private.s1_gestor_operadores for update to prumo_s1_admin_domain_local
 using(true) with check(encerrado_em is not null);
create policy i81_domain_revoke on prumo_private.s1_excecoes_caso_i61 for update to prumo_s1_admin_domain_local
 using(true) with check(revogada_em is not null);
create policy i81_validator_lock on public.equipe_prumo_s1 for update to prumo_s1_professional_validator_local
 using(true) with check(false);

-- INVOKER helpers keep their original bodies/owner. Only exact helpers needed
-- by the administrative path are executable, never the I54/I61 case commands.
grant execute on function prumo_private.s1_i79_validar_profissional(uuid),
 prumo_private.s1_i79_revogar_excecoes(uuid,uuid,uuid),
 prumo_private.s1_i80_digest(jsonb),prumo_private.s1_i80_snapshot(uuid,uuid),
 prumo_private.s1_i80_context(uuid,uuid,uuid),prumo_private.s1_i80_plan(jsonb,text,uuid),
 prumo_private.s1_i80_locks(uuid,uuid,uuid),prumo_private.s1_i80_preview_result(uuid)
 to prumo_s1_admin_domain_local;
grant execute on function prumo_private.s1_i79_validar_profissional(uuid) to prumo_s1_professional_validator_local;

-- Transfer only business bridges and pure deferred validator; HMAC executors,
-- key custodians, tables, case commands and Auth owner remain separate.
grant create on schema prumo_private to prumo_s1_admin_domain_local,prumo_s1_professional_validator_local;
grant prumo_s1_admin_domain_local,prumo_s1_professional_validator_local to postgres with inherit false,set true;
alter function prumo_private.s1_i79_admin_bridge(uuid,uuid,text,uuid,text,uuid,bigint,text,uuid) owner to prumo_s1_admin_domain_local;
alter function prumo_private.s1_i80_bridge(uuid,uuid,text,uuid,text,uuid,text,uuid,uuid,integer,text,uuid) owner to prumo_s1_admin_domain_local;
alter function prumo_private.s1_i79_consistencia() owner to prumo_s1_professional_validator_local;
revoke prumo_s1_admin_domain_local,prumo_s1_professional_validator_local from postgres;
revoke create on schema prumo_private from prumo_s1_admin_domain_local,prumo_s1_professional_validator_local;

-- Deliberate fault injection is installer-only and cannot survive COMMIT.
do $final$
begin
 if current_setting('prumo.i81_fail_before_commit',true)='YES' then
  raise exception 'I81_INSTALL_ROLLBACK_PROBE' using errcode='23514';end if;
 if exists(select 1 from pg_auth_members m join pg_roles r on r.oid=m.roleid
  where r.rolname in('prumo_s1_admin_domain_local','prumo_s1_professional_validator_local'))
 then raise exception 'I81_OWNER_MEMBERSHIP_REMAINS' using errcode='42501';end if;
end $final$;
commit;
