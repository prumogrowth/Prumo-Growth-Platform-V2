-- CFI-01 ATOMIC / LOCAL DISPOSABLE POSTGRES ONLY. Not a production migration.
-- Uses current S0/S1 tables; no commercial status or F03 form write.
-- After s0_cfi01_signed_prerequisite_local_only.sql and closure fixture.
-- The test key/password are PUBLISHED, unsafe outside a throwaway database.
create role prumo_cfi01_atomic_owner_local nologin noinherit
  nosuperuser nocreatedb nocreaterole noreplication nobypassrls;
grant usage on schema public,prumo_private to prumo_cfi01_atomic_owner_local;
-- Supabase may install pgcrypto in "extensions" or another trusted schema.
-- Mirror S0/027: grant ONLY required crypto functions to the NOLOGIN owner.
-- Never expose schema usage or HMAC to the restricted SQL login.
do $crypto_acl$
declare v_schema name;
begin
 select n.nspname into v_schema
 from pg_catalog.pg_extension e
 join pg_catalog.pg_namespace n on n.oid=e.extnamespace
 where e.extname='pgcrypto';
 if v_schema is null then
   raise exception 'CFI01_PGCRYPTO_NOT_INSTALLED' using errcode='42501';
 end if;
 execute pg_catalog.format(
   'grant usage on schema %I to prumo_cfi01_atomic_owner_local',v_schema);
 execute pg_catalog.format(
   'grant execute on function %I.hmac(bytea,bytea,text) to prumo_cfi01_atomic_owner_local',
   v_schema);
 execute pg_catalog.format(
   'grant execute on function %I.digest(bytea,text) to prumo_cfi01_atomic_owner_local',
   v_schema);
end $crypto_acl$;
grant select on public.equipe_prumo_s1,
 public.casos_humanos,public.ciclos_comerciais,public.concessionarias,
 public.atribuicoes_humanas,public.vinculos_papel_escopo,
 public.conversas,public.mensagens,
 prumo_private.cfi01_signing_keys_local,
 prumo_private.cfi01_human_closure_events_local,
 prumo_private.cfi01_consumed_nonces_local
 to prumo_cfi01_atomic_owner_local;
grant insert on prumo_private.cfi01_consumed_nonces_local,
 prumo_private.cfi01_human_closure_events_local
 to prumo_cfi01_atomic_owner_local;
-- Locking S0 rows FOR UPDATE requires UPDATE privilege on these relations.
-- This role is NOLOGIN/NOINHERIT; only the allowlisted SECURITY DEFINER uses it.
grant update on public.casos_humanos,public.ciclos_comerciais,
 public.concessionarias,public.atribuicoes_humanas,public.conversas
 to prumo_cfi01_atomic_owner_local;
-- PostgreSQL FOR SHARE/FOR KEY SHARE requires UPDATE privilege as well.
-- Grant only identity columns, never customer text or signing key secret.
grant update(ator_id) on public.equipe_prumo_s1 to prumo_cfi01_atomic_owner_local;
grant update(id) on public.vinculos_papel_escopo to prumo_cfi01_atomic_owner_local;
grant update(id) on public.mensagens to prumo_cfi01_atomic_owner_local;
grant update(id) on prumo_private.cfi01_human_closure_events_local
 to prumo_cfi01_atomic_owner_local;
grant update(key_id) on prumo_private.cfi01_signing_keys_local
 to prumo_cfi01_atomic_owner_local;

-- Domain relations have RLS deny by default. Policies exist ONLY for this
-- inaccessible NOLOGIN owner and only in this disposable fixture.
create policy cfi01_owner_read_case_lab on public.casos_humanos
 for select to prumo_cfi01_atomic_owner_local using (true);
create policy cfi01_owner_read_cycle_lab on public.ciclos_comerciais
 for select to prumo_cfi01_atomic_owner_local using (true);
create policy cfi01_owner_read_store_lab on public.concessionarias
 for select to prumo_cfi01_atomic_owner_local using (true);
create policy cfi01_owner_read_assignment_lab on public.atribuicoes_humanas
 for select to prumo_cfi01_atomic_owner_local using (true);
create policy cfi01_owner_read_grant_lab on public.vinculos_papel_escopo
 for select to prumo_cfi01_atomic_owner_local using (true);
create policy cfi01_owner_read_conversation_lab on public.conversas
 for select to prumo_cfi01_atomic_owner_local using (true);
create policy cfi01_owner_read_message_lab on public.mensagens
 for select to prumo_cfi01_atomic_owner_local using (true);
-- S1 table normally has RLS; setting policy to owner only where enabled.
create policy cfi01_owner_read_team_lab on public.equipe_prumo_s1
 for select to prumo_cfi01_atomic_owner_local using (true);
-- RLS also checks UPDATE policy for locked rows on relevant S0 tables.
-- Only the NOLOGIN definer role gets these laboratory policies.
create policy cfi01_owner_lock_case_lab on public.casos_humanos
 for update to prumo_cfi01_atomic_owner_local using (true) with check (true);
create policy cfi01_owner_lock_cycle_lab on public.ciclos_comerciais
 for update to prumo_cfi01_atomic_owner_local using (true) with check (true);
create policy cfi01_owner_lock_store_lab on public.concessionarias
 for update to prumo_cfi01_atomic_owner_local using (true) with check (true);
create policy cfi01_owner_lock_assignment_lab on public.atribuicoes_humanas
 for update to prumo_cfi01_atomic_owner_local using (true) with check (true);
create policy cfi01_owner_lock_conversation_lab on public.conversas
 for update to prumo_cfi01_atomic_owner_local using (true) with check (true);
create policy cfi01_owner_lock_message_lab on public.mensagens
 for update to prumo_cfi01_atomic_owner_local using (true) with check (true);
create policy cfi01_owner_lock_grant_lab on public.vinculos_papel_escopo
 for update to prumo_cfi01_atomic_owner_local using (true) with check (true);
create policy cfi01_owner_lock_team_lab on public.equipe_prumo_s1
 for update to prumo_cfi01_atomic_owner_local using (true) with check (true);

-- Supabase reserves ownership/ACL of auth.sessions for the Auth service.
-- The migration role cannot grant its SELECT/UPDATE to our NOLOGIN owner.
-- Use a narrowly scoped postgres-owned helper (precedent S0/C07) that
-- checks only the actor/session tuple under a row lock in THIS transaction.
-- The atomic owner receives EXECUTE only, not direct auth schema rights.
create function prumo_private.cfi01_session_valid_local(
 p_actor uuid,p_session uuid
) returns boolean
language plpgsql security definer set search_path=''
as $session$
begin
 if p_actor is null or p_session is null then
   return false;
 end if;
 perform 1 from auth.sessions s
 where s.id=p_session and s.user_id=p_actor for key share;
 return found;
end $session$;
revoke all on function prumo_private.cfi01_session_valid_local(uuid,uuid)
 from public,anon,authenticated,service_role,prumo_cfi01_pgtest_login;
grant execute on function prumo_private.cfi01_session_valid_local(uuid,uuid)
 to prumo_cfi01_atomic_owner_local;

create function prumo_private.cfi01_atomic_signed_closure_local(
 p_operation text,p_actor uuid,p_session uuid,p_case uuid,
 p_cycle_version bigint,p_event uuid,p_idempotency_key text,
 p_key_id uuid,p_issued_at bigint,p_nonce uuid,p_signature text
) returns table(state text,event_ref uuid)
language plpgsql security definer set search_path=''
as $fn$
declare
  v_secret bytea;
  v_material text;
  v_crypto_schema name;
  v_hmac bytea;
  v_hash text;
  v_serialized text;
  v_shop uuid;
  v_assignment uuid;
  v_version bigint;
  v_status text;
  v_last_message uuid;
  v_count integer;
  v_existing record;
  v_inserted uuid;
  v_nonce uuid;
begin
  if session_user <> 'prumo_cfi01_pgtest_login'
     or p_operation not in ('capture_human_closure','recheck_human_closure')
     or p_actor is null or p_session is null or p_case is null
     or p_cycle_version is null or p_cycle_version<1 or
        p_cycle_version>9223372036854775807
     or p_idempotency_key is null
     or p_idempotency_key !~ '^[a-zA-Z0-9._:-]{8,128}$'
     or p_key_id is null or p_nonce is null or p_issued_at is null
     or p_signature is null or p_signature !~ '^[0-9a-f]{64}$'
     or (p_operation='capture_human_closure' and p_event is not null)
     or (p_operation='recheck_human_closure' and p_event is null)
  then raise exception 'CFI01_ATOMIC_DENIED' using errcode='42501';end if;

  if p_issued_at < pg_catalog.date_part('epoch',pg_catalog.clock_timestamp())::bigint - 30
    or p_issued_at > pg_catalog.date_part('epoch',pg_catalog.clock_timestamp())::bigint + 5
  then raise exception 'CFI01_ATOMIC_EXPIRED' using errcode='42501';end if;

  v_material := pg_catalog.concat_ws('|','cfi01-atomic-local-v1',
    p_operation,p_actor::text,p_session::text,p_case::text,
    p_cycle_version::text,coalesce(p_event::text,'-'),p_idempotency_key,
    p_key_id::text,p_issued_at::text,p_nonce::text);

  select k.secret into v_secret from prumo_private.cfi01_signing_keys_local k
    where k.key_id=p_key_id and k.active for share;
  if v_secret is null then
    raise exception 'CFI01_ATOMIC_KEY_DENIED' using errcode='42501';end if;
  select n.nspname into v_crypto_schema
    from pg_catalog.pg_extension e
    join pg_catalog.pg_namespace n on n.oid=e.extnamespace
    where e.extname='pgcrypto';
  if v_crypto_schema is null then
    raise exception 'CFI01_ATOMIC_CRYPTO_UNAVAILABLE' using errcode='42501';end if;
  execute pg_catalog.format('select %I.hmac($1,$2,''sha256'')',v_crypto_schema)
    into v_hmac using pg_catalog.convert_to(v_material,'utf8'),v_secret;
  if v_hmac is distinct from pg_catalog.decode(p_signature,'hex') then
    raise exception 'CFI01_ATOMIC_HMAC_DENIED' using errcode='42501';end if;

  -- Single S0-authoritative transaction; same cursor/role for all locks,
  -- exact S1 TEAM -> CASE -> CONVERSA -> MENSAGEM -> RECIBO order.
  if not prumo_private.cfi01_session_valid_local(p_actor,p_session)
  then raise exception 'CFI01_ATOMIC_SESSION_DENIED' using errcode='42501';end if;
  if not exists (select 1 from public.equipe_prumo_s1 t
      where t.ator_id=p_actor and t.estado='ativo' for share)
  then raise exception 'CFI01_ATOMIC_TEAM_DENIED' using errcode='42501';end if;

  select h.concessionaria_id,a.id,c.versao_registro,c.status_comercial
    into v_shop,v_assignment,v_version,v_status
    from public.casos_humanos h
    join public.ciclos_comerciais c
      on c.concessionaria_id=h.concessionaria_id and c.id=h.ciclo_id
    join public.concessionarias l
      on l.id=h.concessionaria_id and l.ativo=true
    join public.atribuicoes_humanas a
      on a.caso_id=h.id and a.concessionaria_id=h.concessionaria_id
      and a.operador_id=p_actor and a.encerrada_em is null
    where h.id=p_case
    for update of h,c,l,a;
  if v_shop is null or v_status not in (
      'em atendimento pelo operador','cadastro enviado ao operador')
  then raise exception 'CFI01_ATOMIC_CASE_DENIED' using errcode='42501';end if;
  if v_version<>p_cycle_version then
    raise exception 'CFI01_ATOMIC_STALE' using errcode='40001';end if;
  if not exists(select 1 from public.vinculos_papel_escopo v
    where v.ator_id=p_actor and v.concessionaria_id=v_shop
      and v.papel in ('operador','gestor')
      and v.valido_desde<=pg_catalog.statement_timestamp()
      and (v.valido_ate is null or v.valido_ate>pg_catalog.statement_timestamp())
      for share)
  then raise exception 'CFI01_ATOMIC_GRANT_DENIED' using errcode='42501';end if;

  perform 1 from public.conversas v
    where v.concessionaria_id=v_shop and v.caso_id=p_case
    order by v.id for update;
  if not found then
    return query select 'NO_CONVERSATION'::text,null::uuid;return;
  end if;
  -- First lock every existing message row. New messages referencing the
  -- parent conversation FK wait for the FOR UPDATE lock on the conversation.
  perform 1 from public.mensagens m
    join public.conversas v
      on v.id=m.conversa_id and v.concessionaria_id=m.concessionaria_id
    where v.concessionaria_id=v_shop and v.caso_id=p_case
    order by m.criada_em,m.id for share of m;
  select count(*)::integer,
         (array_agg(m.id order by m.criada_em,m.id))[
            count(*)::integer],
         coalesce(jsonb_agg(
            jsonb_build_array(m.id,m.criada_em,m.direcao,m.origem,
                              m.conteudo_sintetico,m.enviada_por)
            order by m.criada_em,m.id)::text,'[]')
    into v_count,v_last_message,v_serialized
    from public.mensagens m
    join public.conversas v
      on v.id=m.conversa_id and v.concessionaria_id=m.concessionaria_id
    where v.concessionaria_id=v_shop and v.caso_id=p_case;
  if v_count<1 or v_count>2500 then
    return query select 'NO_CONVERSATION'::text,null::uuid;return;
  end if;
  execute pg_catalog.format('select pg_catalog.encode(%I.digest($1,''sha256''),''hex'')',
                             v_crypto_schema)
    into v_hash using pg_catalog.convert_to(v_serialized,'utf8');

  select e.id,e.ator_id,e.sessao_id,e.atribuicao_id,e.versao_ciclo,
         e.snapshot_sha256,e.ultima_mensagem_id,e.quantidade_mensagens
    into v_existing
    from prumo_private.cfi01_human_closure_events_local e
    where e.concessionaria_id=v_shop and e.caso_id=p_case
      and (e.chave_idempotencia=p_idempotency_key or
           (p_operation='recheck_human_closure' and e.id=p_event))
    for update;
  if p_operation='recheck_human_closure' then
    if v_existing.id is null or v_existing.id <> p_event
       or v_existing.ator_id<>p_actor or v_existing.sessao_id<>p_session
       or v_existing.atribuicao_id<>v_assignment
    then raise exception 'CFI01_ATOMIC_RECEIPT_DENIED' using errcode='42501';end if;
    if v_existing.versao_ciclo<>v_version or v_existing.snapshot_sha256<>v_hash
       or v_existing.ultima_mensagem_id<>v_last_message
       or v_existing.quantidade_mensagens<>v_count
    then raise exception 'CFI01_ATOMIC_STALE' using errcode='40001';end if;
    if not exists(select 1 from prumo_private.cfi01_human_closure_events_local e
      where e.id=p_event and e.chave_idempotencia=p_idempotency_key)
    then raise exception 'CFI01_ATOMIC_RECEIPT_DENIED' using errcode='42501';end if;
  elsif v_existing.id is not null then
    if v_existing.ator_id<>p_actor or v_existing.sessao_id<>p_session
       or v_existing.atribuicao_id<>v_assignment then
      raise exception 'CFI01_ATOMIC_REPLAY_DENIED' using errcode='42501';end if;
    if v_existing.versao_ciclo<>v_version
       or v_existing.snapshot_sha256<>v_hash then
      raise exception 'CFI01_ATOMIC_STALE' using errcode='40001';end if;
  end if;

  insert into prumo_private.cfi01_consumed_nonces_local(nonce,key_id)
    values(p_nonce,p_key_id) on conflict do nothing returning nonce into v_nonce;
  if v_nonce is null then
    raise exception 'CFI01_ATOMIC_NONCE_REPLAY' using errcode='42501';end if;
  if p_operation='recheck_human_closure' then
    return query select 'VERIFIED_REVIEW_ONLY_LOCAL'::text,null::uuid;return;
  end if;
  if v_existing.id is not null then
    return query select 'ALREADY_CAPTURED'::text,v_existing.id;return;
  end if;
  insert into prumo_private.cfi01_human_closure_events_local
    (concessionaria_id,caso_id,ator_id,sessao_id,atribuicao_id,
     versao_ciclo,chave_idempotencia,snapshot_sha256,
     ultima_mensagem_id,quantidade_mensagens)
   values(v_shop,p_case,p_actor,p_session,v_assignment,
          v_version,p_idempotency_key,v_hash,v_last_message,v_count)
   on conflict do nothing returning id into v_inserted;
  if v_inserted is null then
    return query select 'DUPLICATE_SNAPSHOT'::text,null::uuid;return;
  end if;
  return query select 'CAPTURED_LOCAL_ONLY'::text,v_inserted;
end $fn$;

revoke all on function prumo_private.cfi01_atomic_signed_closure_local(
 text,uuid,uuid,uuid,bigint,uuid,text,uuid,bigint,uuid,text)
 from public,anon,authenticated,service_role;
-- Grant to restricted login while the fixture installer still owns it.
grant execute on function prumo_private.cfi01_atomic_signed_closure_local(
 text,uuid,uuid,uuid,bigint,uuid,text,uuid,bigint,uuid,text)
 to prumo_cfi01_pgtest_login;
-- PostgreSQL 17 owner transfer needs SET ROLE permission. The Supabase
-- local `postgres` account is not necessarily superuser; grant TEMPORARY
-- membership and CREATE just for ownership transfer, revoke immediately.
grant create on schema prumo_private to prumo_cfi01_atomic_owner_local;
grant prumo_cfi01_atomic_owner_local to postgres with set true;
alter function prumo_private.cfi01_atomic_signed_closure_local(
 text,uuid,uuid,uuid,bigint,uuid,text,uuid,bigint,uuid,text)
 owner to prumo_cfi01_atomic_owner_local;
revoke prumo_cfi01_atomic_owner_local from postgres;
revoke create on schema prumo_private from prumo_cfi01_atomic_owner_local;

-- Only the server-held HMAC signing secret can cause this function to act.
-- The login cannot SELECT private rows or INSERT receipts directly.
