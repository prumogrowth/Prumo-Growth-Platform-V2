-- CFI-01 / LAB ONLY: restricted SQL login and independently signed gate.
-- Apply ONLY after S0/S1 fixtures to disposable PostgreSQL 17 database.
-- Does NOT authorize F03 to apply data, read messages or confirm any sale.
-- TEST-ONLY key/password are intentionally fixed; never use in production.
create role prumo_cfi01_pgtest_login login noinherit
  nosuperuser nocreatedb nocreaterole noreplication nobypassrls
  password 'cf-i01-disposable-test-only-not-production';
create table prumo_private.cfi01_signing_keys_local(
 key_id uuid primary key,
 secret bytea not null check(octet_length(secret)>=32),
 active boolean not null default true
);
create table prumo_private.cfi01_consumed_nonces_local(
 nonce uuid primary key,
 key_id uuid not null references prumo_private.cfi01_signing_keys_local(key_id),
 used_at timestamptz not null default statement_timestamp()
);
insert into prumo_private.cfi01_signing_keys_local(key_id,secret)
values('cfeed000-0000-4000-8000-000000000001'::uuid,
 pg_catalog.decode('1160b59cd3466f55112233445566778899aabbccddeeff001122334455667788','hex'));
revoke all on prumo_private.cfi01_signing_keys_local,
  prumo_private.cfi01_consumed_nonces_local
  from public,anon,authenticated,service_role,prumo_cfi01_pgtest_login;

create function prumo_private.cfi01_signed_prerequisite_local(
  p_operation text,p_actor uuid,p_session uuid,p_case uuid,
  p_cycle_version bigint,p_event uuid,p_key_id uuid,
  p_issued_at bigint,p_nonce uuid,p_signature text
) returns text
language plpgsql security definer set search_path=''
as $fn$
declare
  v_secret bytea;
  v_material text;
  v_signature bytea;
  v_shop uuid;
  v_assignment uuid;
  v_actual_version bigint;
  v_status text;
  v_nonce uuid;
begin
  -- No dynamic SQL or arbitrary tenant/role selection. SQL login has only
  -- EXECUTE on this function; definer authority is tightly allowlisted.
  if session_user <> 'prumo_cfi01_pgtest_login'
     or p_operation not in ('capture_human_closure','recheck_human_closure')
     or p_actor is null or p_session is null or p_case is null
     or p_cycle_version is null or p_cycle_version<1
     or p_key_id is null or p_nonce is null or p_issued_at is null
     or p_signature is null or p_signature !~ '^[0-9a-f]{64}$'
     or (p_operation='capture_human_closure' and p_event is not null)
     or (p_operation='recheck_human_closure' and p_event is null)
  then raise exception 'CFI01_PROOF_DENIED' using errcode='42501'; end if;

  if p_issued_at < pg_catalog.date_part('epoch',pg_catalog.clock_timestamp())::bigint - 30
     or p_issued_at > pg_catalog.date_part('epoch',pg_catalog.clock_timestamp())::bigint + 5
  then raise exception 'CFI01_PROOF_EXPIRED' using errcode='42501';end if;

  -- Clock and keyed canonical bytes are generated exclusively by S0 server.
  v_material := pg_catalog.concat_ws('|','cfi01-local-v1',p_operation,
        p_actor::text,p_session::text,p_case::text,p_cycle_version::text,
        pg_catalog.coalesce(p_event::text,'-'),p_issued_at::text,p_nonce::text);
  select k.secret into v_secret
    from prumo_private.cfi01_signing_keys_local k
    where k.key_id=p_key_id and k.active for share;
  if v_secret is null then
    raise exception 'CFI01_PROOF_DENIED' using errcode='42501';end if;
  v_signature := public.hmac(
     pg_catalog.convert_to(v_material,'utf8'),v_secret,'sha256');
  if v_signature is distinct from pg_catalog.decode(p_signature,'hex') then
    raise exception 'CFI01_PROOF_DENIED' using errcode='42501';end if;

  -- S0 authority; preserve S1 TEAM-before-CASE lock order.
  if not exists(select 1 from auth.sessions s
                where s.id=p_session and s.user_id=p_actor for key share)
  then raise exception 'CFI01_SESSION_DENIED' using errcode='42501';end if;

  if not exists(select 1 from public.equipe_prumo_s1 t
                where t.ator_id=p_actor and t.estado='ativo' for share)
  then raise exception 'CFI01_TEAM_DENIED' using errcode='42501';end if;

  select h.concessionaria_id,a.id,c.versao_registro,c.status_comercial
    into v_shop,v_assignment,v_actual_version,v_status
  from public.casos_humanos h
  join public.ciclos_comerciais c
    on c.id=h.ciclo_id and c.concessionaria_id=h.concessionaria_id
  join public.concessionarias l
    on l.id=h.concessionaria_id and l.ativo
  join public.atribuicoes_humanas a
    on a.caso_id=h.id and a.concessionaria_id=h.concessionaria_id
    and a.operador_id=p_actor and a.encerrada_em is null
  where h.id=p_case for update of h,c,l,a;

  if v_shop is null or v_status not in (
          'em atendimento pelo operador','cadastro enviado ao operador')
  then raise exception 'CFI01_CASE_DENIED' using errcode='42501';end if;
  if v_actual_version <> p_cycle_version then
    raise exception 'CFI01_STALE' using errcode='40001';end if;
  if not exists(select 1 from public.vinculos_papel_escopo v
      where v.ator_id=p_actor and v.concessionaria_id=v_shop
      and v.papel in ('operador','gestor')
      and v.valido_desde <= pg_catalog.statement_timestamp()
      and (v.valido_ate is null or v.valido_ate>pg_catalog.statement_timestamp())
      for share)
  then raise exception 'CFI01_GRANT_DENIED' using errcode='42501';end if;

  if p_operation='recheck_human_closure' then
    -- Receipt identity must refer to the same original authorized context.
    if not exists(select 1
       from prumo_private.cfi01_human_closure_events_local e
       where e.id=p_event and e.concessionaria_id=v_shop
         and e.caso_id=p_case and e.ator_id=p_actor
         and e.sessao_id=p_session and e.atribuicao_id=v_assignment
         and e.versao_ciclo=p_cycle_version
       for share)
    then raise exception 'CFI01_RECEIPT_DENIED' using errcode='42501';end if;
  end if;

  -- Nonce consumed only after all checks. ON CONFLICT is always DENIED.
  insert into prumo_private.cfi01_consumed_nonces_local(nonce,key_id)
    values(p_nonce,p_key_id) on conflict do nothing returning nonce into v_nonce;
  if v_nonce is null then
     raise exception 'CFI01_NONCE_REPLAY' using errcode='42501';end if;
  return 'SIGNED_PREREQUISITES_ONLY_LOCAL';
end $fn$;

-- A PostgreSQL SECURITY DEFINER owned by privileged postgres is a LAB
-- boundary, NOT a reviewed product least-privilege ownership solution.
revoke all on function prumo_private.cfi01_signed_prerequisite_local(
 text,uuid,uuid,uuid,bigint,uuid,uuid,bigint,uuid,text)
 from public,anon,authenticated,service_role;
grant usage on schema prumo_private to prumo_cfi01_pgtest_login;
grant execute on function prumo_private.cfi01_signed_prerequisite_local(
 text,uuid,uuid,uuid,bigint,uuid,uuid,bigint,uuid,text)
 to prumo_cfi01_pgtest_login;
-- Deny direct access to session, S1, tenant, case, message, receipt, key
-- and nonce tables; role has only the EXECUTE entrypoint above.
revoke all on auth.sessions,public.casos_humanos,public.atribuicoes_humanas,
 public.concessionarias,public.ciclos_comerciais,public.vinculos_papel_escopo,
 public.equipe_prumo_s1,public.conversas,public.mensagens,
 prumo_private.cfi01_human_closure_events_local
 from prumo_cfi01_pgtest_login;
