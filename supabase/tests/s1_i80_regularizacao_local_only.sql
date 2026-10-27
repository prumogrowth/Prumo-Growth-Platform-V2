-- I80/G2. Additive, guarded disposable PG17 delta after certified I79.
begin;
do $$ begin
 if current_user<>'postgres' or session_user<>'postgres' or current_database()<>'postgres'
 or current_setting('prumo.i80_disposable',true) is distinct from 'YES'
 or current_setting('server_version_num')::int/10000<>17
 or to_regprocedure('prumo_private.s1_i79_revogar_excecoes(uuid,uuid,uuid)') is null
 then raise exception 'I80_DISPOSABLE_ONLY' using errcode='42501';end if;
end $$;

create table prumo_private.s1_i80_previews (
 id uuid primary key default gen_random_uuid(),diretor_id uuid not null,session_id uuid not null,
 request_key text not null,target_id uuid not null,cargo text not null,manager_id uuid,
 inventory_sha256 text not null,snapshot jsonb not null,snapshot_sha256 text not null,
 blockers jsonb not null,impact jsonb not null,
 created_at timestamptz not null default clock_timestamp(),
 expires_at timestamptz not null default (clock_timestamp()+interval '5 minutes'),
 unique(diretor_id,request_key),check(expires_at>created_at)
);
create table prumo_private.s1_i80_applications (
 id uuid primary key default gen_random_uuid(),preview_id uuid not null unique references prumo_private.s1_i80_previews(id),
 diretor_id uuid not null,request_key text not null,receipt jsonb not null,
 created_at timestamptz not null default clock_timestamp(),unique(diretor_id,request_key)
);
create table prumo_private.s1_i80_audit (
 nonce uuid primary key references prumo_private.cfi01_consumed_nonces_local(nonce),
 diretor_id uuid not null,session_id uuid not null,action text not null,
 target_id uuid,preview_id uuid references prumo_private.s1_i80_previews(id),
 outcome text not null,created_at timestamptz not null default clock_timestamp()
);
alter table prumo_private.s1_i80_previews enable row level security;
alter table prumo_private.s1_i80_applications enable row level security;
alter table prumo_private.s1_i80_audit enable row level security;
revoke all on prumo_private.s1_i80_previews,prumo_private.s1_i80_applications,prumo_private.s1_i80_audit
 from public,anon,authenticated,service_role,prumo_cfi01_pgtest_login;
create trigger i80_preview_immutable before update or delete or truncate on prumo_private.s1_i80_previews
 for each statement execute function prumo_private.cfi01_immutable_fact_local();
create trigger i80_application_immutable before update or delete or truncate on prumo_private.s1_i80_applications
 for each statement execute function prumo_private.cfi01_immutable_fact_local();
create trigger i80_audit_immutable before update or delete or truncate on prumo_private.s1_i80_audit
 for each statement execute function prumo_private.cfi01_immutable_fact_local();

create function prumo_private.s1_i80_digest(p_state jsonb)
returns text language sql immutable security invoker set search_path='' as $$
 select encode(sha256(convert_to(p_state::text,'UTF8')),'hex')
$$;

-- Explicit authorization metadata only: no email, name, phone, message or JWT.
-- xmin detects ABA; aggregates are ordered and timezone is fixed for stable CAS.
create function prumo_private.s1_i80_snapshot(p_target uuid,p_manager uuid)
returns jsonb language plpgsql security invoker set search_path='' set timezone='UTC' as $$
declare v jsonb;n bigint;
begin
 select (select count(*) from public.vinculos_papel_escopo where ator_id=p_target)
  +(select count(*) from prumo_private.s1_gestor_operadores where operador_id=p_target or gestor_id=p_target)
  +(select count(*) from public.atribuicoes_humanas where operador_id=p_target)
  +(select count(*) from prumo_private.s1_excecoes_caso_i61 where operador_id=p_target or gestor_id=p_target) into n;
 v:=jsonb_build_object('target_id',p_target,'team',(select to_jsonb(t) from (
   select e.ator_id,e.cargo,e.estado,e.registrado_em,e.atualizado_em,e.xmin::text as row_version
   from public.equipe_prumo_s1 e where e.ator_id=p_target) t),
  'auth_identity_exists',exists(select 1 from auth.users u where u.id=p_target),
  'authority',(select to_jsonb(r) from(select x.ator_id,x.ativo,x.xmin::text as row_version
   from prumo_private.s1_responsaveis_plataforma x where x.ator_id=p_target) r),
  'candidate_manager',(select to_jsonb(m) from(select e.ator_id,e.cargo,e.estado,e.xmin::text as row_version
   from public.equipe_prumo_s1 e where e.ator_id=p_manager) m),'bounded',n<=2000);
 if n>2000 then return v||jsonb_build_object('row_count',n);end if;
 return v||jsonb_build_object(
  'relations',coalesce((select jsonb_agg(to_jsonb(g) order by g.id) from (
    select x.id,x.gestor_id,x.operador_id,x.atribuido_em,x.encerrado_em,x.xmin::text as row_version
    from prumo_private.s1_gestor_operadores x where x.operador_id=p_target or x.gestor_id=p_target) g),'[]'::jsonb),
  'peers',coalesce((select jsonb_agg(to_jsonb(e) order by e.ator_id) from (
    select x.ator_id,x.cargo,x.estado,x.xmin::text as row_version from public.equipe_prumo_s1 x
    where exists(select 1 from prumo_private.s1_gestor_operadores g where
     (g.gestor_id=p_target and g.operador_id=x.ator_id) or (g.operador_id=p_target and g.gestor_id=x.ator_id))) e),'[]'::jsonb),
  'grants',coalesce((select jsonb_agg(to_jsonb(g) order by g.id) from (
    select x.id,x.concessionaria_id,x.papel,x.valido_desde,x.valido_ate,x.xmin::text as row_version
    from public.vinculos_papel_escopo x where x.ator_id=p_target) g),'[]'::jsonb),
  'intake',(select to_jsonb(d) from(select x.pausado,x.versao,x.xmin::text as row_version
    from prumo_private.s1_intake_estado x where x.operador_id=p_target) d),
  'assignments',coalesce((select jsonb_agg(to_jsonb(a) order by a.id) from (
    select x.id,x.concessionaria_id,x.caso_id,x.operador_id,x.encerrada_em,x.xmin::text as row_version
    from public.atribuicoes_humanas x where x.operador_id=p_target) a),'[]'::jsonb),
  'cases',coalesce((select jsonb_agg(to_jsonb(h) order by h.id) from (
    select x.id,x.concessionaria_id,x.lead_id,x.ciclo_id,x.xmin::text as row_version from public.casos_humanos x
    where exists(select 1 from public.atribuicoes_humanas a where a.caso_id=x.id and a.operador_id=p_target)) h),'[]'::jsonb),
  'exceptions',coalesce((select jsonb_agg(to_jsonb(e) order by e.id) from (
    select x.id,x.concessionaria_id,x.caso_id,x.atribuicao_id,x.operador_id,x.gestor_id,x.criada_em,x.revogada_em,x.xmin::text as row_version
    from prumo_private.s1_excecoes_caso_i61 x where x.operador_id=p_target or x.gestor_id=p_target) e),'[]'::jsonb)
 );
end $$;

-- No classification is inferred. Facts only validate the Director's proposal.
create function prumo_private.s1_i80_plan(p_state jsonb,p_cargo text,p_manager uuid)
returns jsonb language plpgsql security invoker set search_path='' as $$
declare b jsonb:='[]';t jsonb:=p_state->'team';g jsonb;m jsonb:=p_state->'candidate_manager';
 v_current uuid;v_relation bigint;n bigint;children bigint;change_link boolean;revoke_ids jsonb;
begin
 if p_state->>'bounded'<>'true' then b:=b||'"INVENTORY_TOO_LARGE"'::jsonb;end if;
 if t is null or t='null'::jsonb then b:=b||'"MISSING_TEAM_USE_I79_REGISTER"'::jsonb;end if;
 if p_state->>'auth_identity_exists'<>'true' then b:=b||'"AUTH_IDENTITY_MISSING"'::jsonb;end if;
 if p_state->'authority'<>'null'::jsonb then b:=b||'"DIRECTOR_AUTHORITY_CONFLICT"'::jsonb;end if;
 if t->>'cargo' is not null and t->>'cargo'<>p_cargo then b:=b||'"CLASSIFIED_ROLE_CONFLICT"'::jsonb;end if;
 select count(*) into n from jsonb_array_elements(coalesce(p_state->'relations','[]')) r
  where r->>'operador_id'=p_state->>'target_id' and r->>'encerrado_em' is null;
 select count(*) into children from jsonb_array_elements(coalesce(p_state->'relations','[]')) r
  where r->>'gestor_id'=p_state->>'target_id' and r->>'encerrado_em' is null;
 select r into g from jsonb_array_elements(coalesce(p_state->'relations','[]')) r
  where r->>'operador_id'=p_state->>'target_id' and r->>'encerrado_em' is null order by (r->>'id')::bigint limit 1;
 v_current:=(g->>'gestor_id')::uuid;v_relation:=(g->>'id')::bigint;
 if n>1 then b:=b||'"MULTIPLE_ACTIVE_RELATIONS"'::jsonb;end if;
 if p_cargo='gestor' and n>0 then b:=b||'"MANAGER_HAS_PARENT_LINK"'::jsonb;end if;
 if p_cargo='consultor' and children>0 then b:=b||'"CONSULTANT_HAS_SUBORDINATES"'::jsonb;end if;
 if p_cargo='gestor' and t->>'estado'<>'ativo' and exists(
  select 1 from jsonb_array_elements(coalesce(p_state->'peers','[]')) e
  where e->>'cargo'='consultor' and e->>'estado'='ativo'
   and exists(select 1 from jsonb_array_elements(coalesce(p_state->'relations','[]')) r
    where r->>'gestor_id'=p_state->>'target_id' and r->>'operador_id'=e->>'ator_id' and r->>'encerrado_em' is null))
 then b:=b||'"INACTIVE_MANAGER_HAS_ACTIVE_CONSULTANTS"'::jsonb;end if;
 if p_cargo='consultor' then
  if t->>'estado'='pendente' and (n>0 or p_manager is not null)
  then b:=b||'"PENDING_CHEFIA_USE_I79_ACTIVATION"'::jsonb;end if;
  if p_manager is null and (t->>'estado'='ativo' or n>0) then b:=b||'"MANAGER_REQUIRED"'::jsonb;end if;
  if p_manager is not null and (m='null'::jsonb or m is null or m->>'cargo' is distinct from 'gestor'
    or m->>'estado' is distinct from 'ativo' or p_manager::text=p_state->>'target_id')
  then b:=b||'"MANAGER_NOT_CLASSIFIED_ACTIVE"'::jsonb;end if;
 end if;
 change_link:=p_cargo='consultor' and p_manager is distinct from v_current;
 if t->>'cargo' is not null and not change_link then b:=b||'"NOTHING_TO_REGULARIZE"'::jsonb;end if;
 -- A valid classified consultant uses the existing I79 TRANSFER, not a bypass.
 if t->>'cargo'='consultor' and n=1 and exists(select 1 from jsonb_array_elements(coalesce(p_state->'peers','[]')) e
  where e->>'ator_id'=v_current::text and e->>'cargo'='gestor' and e->>'estado'='ativo')
 then b:=b||'"CLASSIFIED_USE_I79_TRANSFER"'::jsonb;end if;
 select coalesce(jsonb_agg(e->>'id' order by e->>'id'),'[]') into revoke_ids
 from jsonb_array_elements(coalesce(p_state->'exceptions','[]')) e
 where e->>'operador_id'=p_state->>'target_id' and e->>'revogada_em' is null and (
  change_link or p_cargo<>'consultor' or e->>'gestor_id' is distinct from p_manager::text or
  not exists(select 1 from jsonb_array_elements(coalesce(p_state->'assignments','[]')) a
   where a->>'id'=e->>'atribuicao_id' and a->>'caso_id'=e->>'caso_id'
    and a->>'concessionaria_id'=e->>'concessionaria_id' and a->>'encerrada_em' is null));
 return jsonb_build_object('blockers',b,'impact',jsonb_build_object(
  'state_preserved',t->>'estado','current_relationship_id',v_relation::text,
  'complete',p_state->'bounded',
  'change_relationship',change_link,'revoke_exception_ids',revoke_ids,
  'grant_count',case when p_state->>'bounded'='true' then jsonb_array_length(coalesce(p_state->'grants','[]')) else null end,
  'assignment_count',case when p_state->>'bounded'='true' then jsonb_array_length(coalesce(p_state->'assignments','[]')) else null end,
  'case_count',case when p_state->>'bounded'='true' then jsonb_array_length(coalesce(p_state->'cases','[]')) else null end,
  'intake_paused',p_state->'intake'->'pausado'));
end $$;

create function prumo_private.s1_i80_locks(p_actor uuid,p_target uuid,p_manager uuid)
returns void language plpgsql security invoker set search_path='' as $$
begin
 -- Strong actor fence prevents FK phantoms. Existing writers can take team
 -- before their FK checks: NOWAIT on ALL domain rows forbids a reverse wait.
 perform 1 from public.atores a where a.id in(p_actor,p_target,p_manager) order by a.id for update nowait;
 perform 1 from public.equipe_prumo_s1 e where e.ator_id in(p_actor,p_target,p_manager)
  or exists(select 1 from prumo_private.s1_gestor_operadores g where
   (g.operador_id=p_target and g.gestor_id=e.ator_id) or (g.gestor_id=p_target and g.operador_id=e.ator_id))
  order by e.ator_id for update nowait;
 perform 1 from prumo_private.s1_gestor_operadores g where g.operador_id=p_target or g.gestor_id=p_target order by g.id for update nowait;
 perform 1 from public.vinculos_papel_escopo g where g.ator_id=p_target order by g.id for share nowait;
 perform 1 from prumo_private.s1_intake_estado d where d.operador_id=p_target for share nowait;
 perform 1 from public.atribuicoes_humanas a where a.operador_id=p_target order by a.id for share nowait;
 perform 1 from public.casos_humanos h where exists(select 1 from public.atribuicoes_humanas a
  where a.operador_id=p_target and a.caso_id=h.id) order by h.id for share nowait;
 perform 1 from prumo_private.s1_excecoes_caso_i61 x where x.operador_id=p_target or x.gestor_id=p_target order by x.id for update nowait;
 perform 1 from prumo_private.s1_responsaveis_plataforma r where r.ator_id in(p_actor,p_target) order by r.ator_id for share nowait;
end $$;

create function prumo_private.s1_i80_preview_result(p_id uuid)
returns jsonb language sql stable security invoker set search_path='' set timezone='UTC' as $$
 select jsonb_build_object('outcome',case when p.blockers='[]'::jsonb then 'READY' else 'BLOCKED' end,
  'preview_id',p.id,'target_id',p.target_id,'cargo',p.cargo,'manager_id',p.manager_id,
  'inventory_sha256',p.inventory_sha256,'snapshot_sha256',p.snapshot_sha256,
  'blockers',p.blockers,'impact',p.impact,'expires_at',p.expires_at) from prumo_private.s1_i80_previews p where p.id=p_id
$$;

create function prumo_private.s1_i80_bridge(
 p_actor uuid,p_session uuid,p_action text,p_target uuid,p_cargo text,p_manager uuid,
 p_expected text,p_preview uuid,p_cursor uuid,p_limit integer,p_request text,p_nonce uuid)
returns jsonb language plpgsql security definer set search_path='' set timezone='UTC' as $$
declare s jsonb;d text;pl jsonb;p record;r record;result jsonb;rows jsonb:='[]';entry record;
 more boolean;last_id uuid;v_preview uuid;relation_id bigint;revoked integer:=0;x jsonb;request_id uuid;
begin
 if session_user<>'prumo_cfi01_pgtest_login' or not prumo_private.cfi01_session_valid_local(p_actor,p_session)
 then raise exception 'I80_SESSION_REQUIRED' using errcode='42501';end if;
 -- Same-key calls wait BEFORE acquiring domain locks. Other disputes fail fast.
 perform pg_advisory_xact_lock(hashtextextended('s1-i80:'||p_actor::text||':'||p_action||':'||p_request,0));
 if p_action='INVENTORY' then
  perform 1 from public.equipe_prumo_s1 e where e.ator_id=p_actor for share;
  perform 1 from prumo_private.s1_responsaveis_plataforma a where a.ator_id=p_actor for share;
 else
  perform prumo_private.s1_i80_locks(p_actor,p_target,p_manager);
 end if;
 if not exists(select 1 from public.equipe_prumo_s1 e join prumo_private.s1_responsaveis_plataforma a on a.ator_id=e.ator_id
  where e.ator_id=p_actor and e.cargo='diretor' and e.estado='ativo' and a.ativo)
 or not prumo_private.cfi01_session_valid_local(p_actor,p_session)
 then raise exception 'I80_DIRECTOR_REQUIRED' using errcode='42501';end if;
 if p_action='INVENTORY' then
  for entry in select a.id from public.atores a left join public.equipe_prumo_s1 e on e.ator_id=a.id
   where (p_cursor is null or a.id>p_cursor) and (e.cargo is null or
    (e.cargo='consultor' and e.estado='ativo' and not exists(select 1 from prumo_private.s1_gestor_operadores g
     join public.equipe_prumo_s1 m on m.ator_id=g.gestor_id and m.cargo='gestor' and m.estado='ativo'
     where g.operador_id=a.id and g.encerrado_em is null))
    or (e.cargo in('gestor','diretor') and exists(select 1 from prumo_private.s1_gestor_operadores g where g.operador_id=a.id and g.encerrado_em is null))
    or (e.cargo='consultor' and exists(select 1 from prumo_private.s1_gestor_operadores g where g.gestor_id=a.id and g.encerrado_em is null))) order by a.id limit p_limit+1
  loop
   if jsonb_array_length(rows)=p_limit then more:=true;exit;end if;
   s:=prumo_private.s1_i80_snapshot(entry.id,null);last_id:=entry.id;
   rows:=rows||jsonb_build_array(jsonb_build_object('target_id',entry.id,'cargo',s->'team'->'cargo',
    'estado',s->'team'->'estado','bounded',s->'bounded','inventory_sha256',prumo_private.s1_i80_digest(s)));
  end loop;
  result:=jsonb_build_object('outcome','INVENTORY','items',rows,'has_more',coalesce(more,false),
   'next_cursor',case when more then last_id else null end);
 else
  if p_target=p_actor then raise exception 'I80_SELF_ADMINISTRATION_DENIED' using errcode='42501';end if;
  if p_action='PREVIEW' then
   s:=prumo_private.s1_i80_snapshot(p_target,null);
   if prumo_private.s1_i80_digest(s)<>p_expected then raise exception 'I80_STALE_INVENTORY' using errcode='40001';end if;
   s:=prumo_private.s1_i80_snapshot(p_target,p_manager);d:=prumo_private.s1_i80_digest(s);
   select * into p from prumo_private.s1_i80_previews where diretor_id=p_actor and request_key=p_request;
   if found then
    if p.target_id<>p_target or p.cargo<>p_cargo or p.manager_id is distinct from p_manager or p.inventory_sha256<>p_expected
    then raise exception 'I80_PREVIEW_KEY_CONFLICT' using errcode='23505';end if;
    if p.session_id<>p_session then raise exception 'I80_PREVIEW_SESSION_CHANGED' using errcode='42501';end if;
    if p.expires_at<=clock_timestamp() then raise exception 'I80_PREVIEW_EXPIRED' using errcode='P3180';end if;
    if p.snapshot_sha256<>d then raise exception 'I80_STALE_PREVIEW' using errcode='40001';end if;
    v_preview:=p.id;
   else
    pl:=prumo_private.s1_i80_plan(s,p_cargo,p_manager);
    insert into prumo_private.s1_i80_previews(diretor_id,session_id,request_key,target_id,cargo,manager_id,inventory_sha256,snapshot,snapshot_sha256,blockers,impact)
    values(p_actor,p_session,p_request,p_target,p_cargo,p_manager,p_expected,s,d,pl->'blockers',pl->'impact') returning id into v_preview;
   end if;
   result:=prumo_private.s1_i80_preview_result(v_preview);
  else
   select * into p from prumo_private.s1_i80_previews where id=p_preview;
   if not found or p.diretor_id<>p_actor or p.session_id<>p_session
   then raise exception 'I80_PREVIEW_AUTHORITY_MISMATCH' using errcode='42501';end if;
   if p.target_id<>p_target or p.cargo<>p_cargo or p.manager_id is distinct from p_manager or p.snapshot_sha256<>p_expected
   then raise exception 'I80_PREVIEW_BINDING_MISMATCH' using errcode='40001';end if;
   select * into r from prumo_private.s1_i80_applications where diretor_id=p_actor and request_key=p_request;
   s:=prumo_private.s1_i80_snapshot(p_target,p_manager);d:=prumo_private.s1_i80_digest(s);
   if found then
    if r.preview_id<>p_preview then raise exception 'I80_APPLICATION_KEY_CONFLICT' using errcode='23505';end if;
    if r.receipt->>'after_sha256'<>d then raise exception 'I80_REPLAY_STATE_CHANGED' using errcode='40001';end if;
    result:=r.receipt||jsonb_build_object('outcome','ALREADY_APPLIED');
   else
    if exists(select 1 from prumo_private.s1_i80_applications where preview_id=p_preview)
    then raise exception 'I80_PREVIEW_ALREADY_CONSUMED' using errcode='23505';end if;
    if p.expires_at<=clock_timestamp() then raise exception 'I80_PREVIEW_EXPIRED' using errcode='P3180';end if;
    if p.blockers<>'[]'::jsonb then raise exception 'I80_PREVIEW_BLOCKED' using errcode='P3181';end if;
    if d<>p.snapshot_sha256 then raise exception 'I80_STALE_APPLICATION' using errcode='40001';end if;
    pl:=prumo_private.s1_i80_plan(s,p_cargo,p_manager);
    if pl->'blockers'<>'[]'::jsonb or pl->'impact'<>p.impact
    then raise exception 'I80_CHANGED_PLAN' using errcode='40001';end if;
    for x in select value from jsonb_array_elements(p.impact->'revoke_exception_ids')
    loop
     update prumo_private.s1_excecoes_caso_i61 set revogada_em=greatest(criada_em,clock_timestamp()) where id=(x#>>'{}')::uuid;
     insert into prumo_private.s1_excecoes_caso_eventos_i61(excecao_id,evento,solicitante_id) values((x#>>'{}')::uuid,'REVOGADA',p_actor);
     revoked:=revoked+1;
    end loop;
    relation_id:=(p.impact->>'current_relationship_id')::bigint;
    if (p.impact->>'change_relationship')::boolean then
     if relation_id is not null then update prumo_private.s1_gestor_operadores set encerrado_em=greatest(atribuido_em,clock_timestamp()) where id=relation_id;end if;
     relation_id:=null;
     if p_manager is not null then insert into prumo_private.s1_gestor_operadores(gestor_id,operador_id) values(p_manager,p_target) returning id into relation_id;end if;
    end if;
    update public.equipe_prumo_s1 set cargo=p_cargo where ator_id=p_target and cargo is null;
    perform prumo_private.s1_i79_validar_profissional(p_target);
    request_id:=gen_random_uuid();d:=prumo_private.s1_i80_digest(prumo_private.s1_i80_snapshot(p_target,p_manager));
    result:=jsonb_build_object('outcome','APPLIED','request_id',request_id,'preview_id',p_preview,'target_id',p_target,
     'cargo',p_cargo,'estado',p.impact->>'state_preserved','manager_id',p_manager,'relationship_id',relation_id::text,
     'revoked_exception_count',revoked,'before_sha256',p.snapshot_sha256,'after_sha256',d);
    insert into prumo_private.s1_i80_applications(id,preview_id,diretor_id,request_key,receipt) values(request_id,p_preview,p_actor,p_request,result);
   end if;
   v_preview:=p_preview;
  end if;
 end if;
 insert into prumo_private.s1_i80_audit(nonce,diretor_id,session_id,action,target_id,preview_id,outcome)
 values(p_nonce,p_actor,p_session,p_action,p_target,v_preview,result->>'outcome');
 return result;
end $$;
revoke all on function prumo_private.s1_i80_bridge(uuid,uuid,text,uuid,text,uuid,text,uuid,uuid,integer,text,uuid)
 from public,anon,authenticated,service_role,prumo_cfi01_pgtest_login;
grant execute on function prumo_private.s1_i80_bridge(uuid,uuid,text,uuid,text,uuid,text,uuid,uuid,integer,text,uuid) to prumo_s0_g1_executor_local;

create function prumo_private.s1_i80_signed(
 p_actor uuid,p_session uuid,p_action text,p_target uuid,p_cargo text,p_manager uuid,p_expected text,p_preview uuid,
 p_cursor uuid,p_limit integer,p_request text,p_key uuid,p_issued bigint,p_nonce uuid,p_mac text)
returns jsonb language plpgsql security definer set search_path='' as $$
declare secret_value bytea;s name;material text;expected_mac bytea;n uuid;r jsonb;
begin
 if session_user<>'prumo_cfi01_pgtest_login' or p_actor is null or p_session is null or p_action is null
 or p_action not in('INVENTORY','PREVIEW','APPLY') or p_limit is null
 or (p_action='INVENTORY' and (p_target is not null or p_cargo is not null or p_manager is not null or p_expected is not null or p_preview is not null or p_limit<1 or p_limit>50))
 or (p_action in('PREVIEW','APPLY') and (p_target is null or p_cargo is null or p_cargo not in('gestor','consultor')
  or (p_cargo='gestor' and p_manager is not null) or p_expected is null or p_expected !~ '^[0-9a-f]{64}$' or p_cursor is not null or p_limit<>0))
 or (p_action='PREVIEW' and p_preview is not null) or (p_action='APPLY' and p_preview is null)
 or p_request is null or p_request !~ '^[A-Za-z0-9._:-]{8,128}$' or p_key is null or p_nonce is null
 or p_mac is null or p_mac !~ '^[0-9a-f]{64}$' or p_issued is null
 or p_issued<extract(epoch from clock_timestamp())::bigint-30 or p_issued>extract(epoch from clock_timestamp())::bigint+5
 then raise exception 'I80_PROOF_INVALID' using errcode='42501';end if;
 select secret into secret_value from prumo_private.cfi01_signing_keys_local where key_id=p_key and active for share;
 if secret_value is null then raise exception 'I80_KEY_REVOKED' using errcode='42501';end if;
 select ns.nspname into s from pg_extension e join pg_namespace ns on ns.oid=e.extnamespace where e.extname='pgcrypto';
 material:=concat_ws('|','s0-s1-i80-regularization-v1',p_actor::text,p_session::text,p_action,coalesce(p_target::text,'-'),
  coalesce(p_cargo,'-'),coalesce(p_manager::text,'-'),coalesce(p_expected,'-'),coalesce(p_preview::text,'-'),
  coalesce(p_cursor::text,'-'),p_limit::text,p_request,p_key::text,p_issued::text,p_nonce::text);
 execute format('select %I.hmac($1,$2,''sha256'')',s) into expected_mac using convert_to(material,'UTF8'),secret_value;
 if expected_mac is distinct from decode(p_mac,'hex') then raise exception 'I80_BAD_MAC' using errcode='42501';end if;
 insert into prumo_private.cfi01_consumed_nonces_local(nonce,key_id) values(p_nonce,p_key)
 on conflict do nothing returning nonce into n;
 if n is null then raise exception 'I80_NONCE_REPLAY' using errcode='42501';end if;
 r:=prumo_private.s1_i80_bridge(p_actor,p_session,p_action,p_target,p_cargo,p_manager,p_expected,p_preview,p_cursor,p_limit,p_request,p_nonce);
 if p_issued<extract(epoch from clock_timestamp())::bigint-30 then raise exception 'I80_PROOF_EXPIRED_AFTER_WAIT' using errcode='42501';end if;
 return r;
end $$;
revoke all on function prumo_private.s1_i80_signed(uuid,uuid,text,uuid,text,uuid,text,uuid,uuid,integer,text,uuid,bigint,uuid,text)
 from public,anon,authenticated,service_role;
grant execute on function prumo_private.s1_i80_signed(uuid,uuid,text,uuid,text,uuid,text,uuid,uuid,integer,text,uuid,bigint,uuid,text) to prumo_cfi01_pgtest_login;
grant create on schema prumo_private to prumo_s0_g1_executor_local;
grant prumo_s0_g1_executor_local to postgres with inherit false,set true;
alter function prumo_private.s1_i80_signed(uuid,uuid,text,uuid,text,uuid,text,uuid,uuid,integer,text,uuid,bigint,uuid,text) owner to prumo_s0_g1_executor_local;
revoke prumo_s0_g1_executor_local from postgres;
revoke create on schema prumo_private from prumo_s0_g1_executor_local;
revoke all on function prumo_private.s1_i80_digest(jsonb),prumo_private.s1_i80_snapshot(uuid,uuid),
 prumo_private.s1_i80_plan(jsonb,text,uuid),prumo_private.s1_i80_locks(uuid,uuid,uuid),prumo_private.s1_i80_preview_result(uuid)
 from public,anon,authenticated,service_role,prumo_cfi01_pgtest_login;
commit;
