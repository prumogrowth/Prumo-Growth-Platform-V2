-- I61: canonical S0/S1 case-scoped exception in disposable PG17 ONLY.
-- No RLS grants, no public RPC, no hosted operation or impersonable client action.
begin;
create table prumo_private.s1_excecoes_caso_i61 (
 id uuid primary key default gen_random_uuid(),
 concessionaria_id uuid not null,
 caso_id uuid not null,
 atribuicao_id uuid not null unique,
 operador_id uuid not null references public.atores(id),
 gestor_id uuid not null references public.atores(id),
 criada_em timestamptz not null default pg_catalog.clock_timestamp(),
 revogada_em timestamptz,
 foreign key(concessionaria_id,caso_id)
  references public.casos_humanos(concessionaria_id,id),
 foreign key(atribuicao_id) references public.atribuicoes_humanas(id)
  deferrable initially deferred,
 check(revogada_em is null or revogada_em>=criada_em)
);
create table prumo_private.s1_excecoes_caso_eventos_i61 (
 id bigint generated always as identity primary key,
 excecao_id uuid not null references prumo_private.s1_excecoes_caso_i61(id),
 evento text not null check(evento in ('CRIADA','REVOGADA')),
 solicitante_id uuid not null references public.atores(id),
 criado_em timestamptz not null default pg_catalog.clock_timestamp()
);
alter table prumo_private.s1_excecoes_caso_i61 enable row level security;
alter table prumo_private.s1_excecoes_caso_eventos_i61 enable row level security;
revoke all on prumo_private.s1_excecoes_caso_i61,
 prumo_private.s1_excecoes_caso_eventos_i61
 from public,anon,authenticated,service_role;
revoke all on sequence prumo_private.s1_excecoes_caso_eventos_i61_id_seq
 from public,anon,authenticated,service_role;
create trigger s1_excecao_i61_eventos_imutaveis
 before update or delete on prumo_private.s1_excecoes_caso_eventos_i61
 for each row execute function prumo_private.s1_proibir_alteracao_historico();
create trigger s1_excecao_i61_eventos_no_truncate
 before truncate on prumo_private.s1_excecoes_caso_eventos_i61
 for each statement execute function prumo_private.s1_proibir_alteracao_historico();

-- Internal eligibility proof is scoped to a single assignment UUID. No
-- caller-supplied JWT is accepted and the private table is inaccessible to REST.
create function prumo_private.s1_prova_excecao_i61(
 p_loja uuid,p_caso uuid,p_atr uuid,p_operador uuid)
returns boolean language sql stable security invoker set search_path='' as $f$
 select current_user='postgres' and p_loja is not null and p_caso is not null
 and p_atr is not null and p_operador is not null
 and exists(select 1 from prumo_private.s1_excecoes_caso_i61 x
  join public.equipe_prumo_s1 e on e.ator_id=x.operador_id and e.estado='ativo'
  join public.equipe_prumo_s1 g on g.ator_id=x.gestor_id and g.estado='ativo'
  join prumo_private.s1_gestor_operadores go on go.gestor_id=x.gestor_id
   and go.operador_id=x.operador_id and go.encerrado_em is null
  join public.concessionarias loja on loja.id=x.concessionaria_id and loja.ativo
  where x.concessionaria_id=p_loja and x.caso_id=p_caso
   and x.atribuicao_id=p_atr and x.operador_id=p_operador
   and x.revogada_em is null);
$f$;

-- Preserve I57 grant locks/revalidation for normal assignments. The only
-- new no-grant path requires a matching, unrevoked exception and trusted S0
-- executor. I52 intake and account-state trigger is not modified.
create or replace function public.s0_verificar_atribuicao()
returns trigger language plpgsql security invoker set search_path='' as $f$
declare v_grant boolean;
begin
 if tg_op='UPDATE' and new.operador_id is not distinct from old.operador_id
 and new.caso_id is not distinct from old.caso_id
 and new.concessionaria_id is not distinct from old.concessionaria_id
 then return new;end if;
 perform 1 from public.vinculos_papel_escopo v
 where v.ator_id=new.operador_id and v.concessionaria_id=new.concessionaria_id
 and v.papel in ('operador','gestor')
 order by v.papel,v.valido_desde for share of v;
 -- Preserve I57 protection against dealership closure while assignment waits.
 perform 1 from public.concessionarias l
 where l.id=new.concessionaria_id for share of l;
 select exists(select 1 from public.vinculos_papel_escopo v
 join public.concessionarias l on l.id=v.concessionaria_id
 where v.ator_id=new.operador_id and v.concessionaria_id=new.concessionaria_id
 and v.papel in ('operador','gestor') and l.ativo
 and v.valido_desde<=pg_catalog.clock_timestamp()
 and (v.valido_ate is null or v.valido_ate>pg_catalog.clock_timestamp()))
 into v_grant;
 if v_grant then return new;end if;
 if prumo_private.s1_prova_excecao_i61(
  new.concessionaria_id,new.caso_id,new.id,new.operador_id)
 then return new;end if;
 raise exception 'S0_DESTINO_SEM_CONCESSAO_ATIVA' using errcode='23514';
end $f$;

create or replace function prumo_private.s1_validar_nova_atribuicao()
returns trigger language plpgsql security invoker set search_path='' as $f$
begin
 if current_user<>'postgres' then
  raise exception 'INTERNAL_ONLY' using errcode='42501';end if;
 if tg_op='UPDATE' and new.operador_id is not distinct from old.operador_id
 and new.caso_id is not distinct from old.caso_id
 and new.concessionaria_id is not distinct from old.concessionaria_id
 then return new;end if;
 perform 1 from public.equipe_prumo_s1 e
 where e.ator_id=new.operador_id for share of e;
 if exists(select 1 from public.equipe_prumo_s1 e
  join public.vinculos_papel_escopo v on v.ator_id=e.ator_id
  join public.concessionarias l on l.id=v.concessionaria_id
  where e.ator_id=new.operador_id and e.estado='ativo' and l.ativo
  and v.concessionaria_id=new.concessionaria_id
  and v.papel in ('operador','gestor')
  and v.valido_desde<=pg_catalog.clock_timestamp()
  and (v.valido_ate is null or v.valido_ate>pg_catalog.clock_timestamp()))
 then return new;end if;
 if prumo_private.s1_prova_excecao_i61(
  new.concessionaria_id,new.caso_id,new.id,new.operador_id)
 then return new;end if;
 raise exception 'PROFISSIONAL_PRUMO_INELEGIVEL' using errcode='23514';
end $f$;

-- Closing an assignment irrevocably closes its case exception as well.
create function prumo_private.s1_excecao_encerrar_i61()
returns trigger language plpgsql security invoker set search_path='' as $f$
declare v record;
begin
 if old.encerrada_em is null and new.encerrada_em is not null then
  for v in
   update prumo_private.s1_excecoes_caso_i61
    set revogada_em=greatest(criada_em,pg_catalog.clock_timestamp())
   where atribuicao_id=old.id and revogada_em is null
   returning id,gestor_id
  loop
   insert into prumo_private.s1_excecoes_caso_eventos_i61(
    excecao_id,evento,solicitante_id) values(v.id,'REVOGADA',v.gestor_id);
  end loop;
 end if;
 return new;
end $f$;
create trigger s1_excecao_encerrar_i61
 after update of encerrada_em on public.atribuicoes_humanas
 for each row execute function prumo_private.s1_excecao_encerrar_i61();

-- Same-case transfer: only current manager of both actors, both active,
-- canonical lead/case and assignment; destination WITHOUT a store-wide grant.
-- Locks serialize with I52 intake, relationship changes and competing claims.
create function prumo_private.s1_mover_excecao_caso_i61(
 p_gestor uuid,p_loja uuid,p_caso uuid,p_atr_esperada uuid,p_destino uuid)
returns jsonb language plpgsql security invoker set search_path='' as $f$
declare v_origem uuid;v_ant uuid;v_nova uuid;v_x uuid;
 v_data timestamptz;v_n int;v_status text;
begin
 if current_user<>'postgres' then
  raise exception 'EXCECAO_EXECUTOR_INTERNO' using errcode='42501';end if;
 if p_gestor is null or p_loja is null or p_caso is null
 or p_atr_esperada is null or p_destino is null or p_gestor=p_destino
 then raise exception 'EXCECAO_PARAMETROS_INVALIDOS' using errcode='22023';end if;
 select operador_id into v_origem from public.atribuicoes_humanas
 where id=p_atr_esperada and concessionaria_id=p_loja
 and caso_id=p_caso and encerrada_em is null;
 if v_origem is null or v_origem=p_destino then
  raise exception 'EXCECAO_ATRIBUICAO_DESATUALIZADA' using errcode='22023';end if;
 select count(*) into v_n from (select ator_id from public.equipe_prumo_s1
 where ator_id in (p_gestor,v_origem,p_destino)
 order by ator_id for share) q;
 if v_n<>3 or (select count(*) from public.equipe_prumo_s1
  where ator_id in (p_gestor,v_origem,p_destino) and estado='ativo')<>3
 then raise exception 'EXCECAO_EQUIPE_INATIVA' using errcode='42501';end if;
 select count(*) into v_n from (
  select operador_id from prumo_private.s1_gestor_operadores
  where gestor_id=p_gestor and operador_id in (v_origem,p_destino)
  order by operador_id for share
 ) q;
 if v_n<>2 or (select count(*) from prumo_private.s1_gestor_operadores
  where gestor_id=p_gestor and operador_id in (v_origem,p_destino)
   and encerrado_em is null)<>2
 then raise exception 'EXCECAO_GESTOR_FORA_DA_EQUIPE' using errcode='42501';end if;
 perform 1 from public.concessionarias
 where id=p_loja and ativo for share;
 if not found then raise exception 'EXCECAO_LOJA_INATIVA' using errcode='42501';end if;
 -- Lock source grant rows before case/assignment rows to avoid stale
 -- authority if a simultaneous grant update attempts redistribution.
 perform 1 from public.vinculos_papel_escopo v
 where v.ator_id=v_origem and v.concessionaria_id=p_loja
 order by v.papel,v.valido_desde for share of v;
 -- Lock destination's grants WITHOUT time predicate before read. Any current
 -- store role (including manager/responsavel) forces the normal path.
 perform 1 from public.vinculos_papel_escopo v
 where v.ator_id=p_destino and v.concessionaria_id=p_loja
 order by v.papel,v.valido_desde for share of v;
 if exists(select 1 from public.vinculos_papel_escopo v
  where v.ator_id=p_destino and v.concessionaria_id=p_loja
  and v.papel in ('operador','gestor','responsavel')
  and v.valido_desde<=pg_catalog.clock_timestamp()
  and (v.valido_ate is null or v.valido_ate>pg_catalog.clock_timestamp()))
 then raise exception 'EXCECAO_DESTINO_JA_TEM_LOJA' using errcode='22023';end if;
 -- Same serialization lock as s1_definir_intake; A2 checked again post-lock.
 if exists(select 1 from prumo_private.s1_intake_estado
  where operador_id=p_destino and pausado)
 then raise exception 'DESTINO_COM_INTAKE_PAUSADO' using errcode='23514';end if;
 select c.status_comercial into v_status
 from public.casos_humanos h
 join public.ciclos_comerciais c
  on c.concessionaria_id=h.concessionaria_id and c.id=h.ciclo_id
 where h.concessionaria_id=p_loja and h.id=p_caso
 for update of h,c;
 if not found then raise exception 'EXCECAO_CASO_FORA_LOJA'
  using errcode='22023';end if;
 if v_status in ('vendido','perdido') then
  raise exception 'EXCECAO_CICLO_TERMINAL' using errcode='23514';end if;
 select id,operador_id,atribuida_em into v_ant,v_origem,v_data
 from public.atribuicoes_humanas
 where concessionaria_id=p_loja and caso_id=p_caso and encerrada_em is null
 for update;
 if v_ant is distinct from p_atr_esperada then
  raise exception 'EXCECAO_ATRIBUICAO_DESATUALIZADA' using errcode='22023';end if;
 -- Recheck authority and source grant after all locks.
 if (select count(*) from prumo_private.s1_gestor_operadores
  where gestor_id=p_gestor and operador_id in (v_origem,p_destino)
  and encerrado_em is null)<>2
 then raise exception 'EXCECAO_CHEFIA_REVOGADA' using errcode='42501';end if;
 if not exists(select 1 from public.vinculos_papel_escopo v
  where v.ator_id=v_origem and v.concessionaria_id=p_loja
  and v.papel in ('operador','gestor')
  and v.valido_desde<=pg_catalog.clock_timestamp()
  and (v.valido_ate is null or v.valido_ate>pg_catalog.clock_timestamp()))
 and not exists(select 1 from prumo_private.s1_excecoes_caso_i61 x
  where x.atribuicao_id=v_ant and x.operador_id=v_origem
   and x.caso_id=p_caso and x.concessionaria_id=p_loja
   and x.revogada_em is null)
 then raise exception 'EXCECAO_ORIGEM_SEM_AUTORIDADE' using errcode='42501';end if;
 v_nova:=gen_random_uuid();
 insert into prumo_private.s1_excecoes_caso_i61(
  concessionaria_id,caso_id,atribuicao_id,operador_id,gestor_id)
 values(p_loja,p_caso,v_nova,p_destino,p_gestor) returning id into v_x;
 update public.atribuicoes_humanas
  set encerrada_em=greatest(v_data,pg_catalog.clock_timestamp())
  where id=v_ant and encerrada_em is null;
 insert into public.atribuicoes_humanas(
  id,concessionaria_id,caso_id,operador_id)
 values(v_nova,p_loja,p_caso,p_destino);
 insert into prumo_private.s1_excecoes_caso_eventos_i61(
  excecao_id,evento,solicitante_id) values(v_x,'CRIADA',p_gestor);
 return pg_catalog.jsonb_build_object('outcome','MOVED_CASE_EXCEPTION',
  'case_id',p_caso,'assignment_id',v_nova,'exception_id',v_x);
end $f$;

create function prumo_private.s1_revogar_excecao_i61(p_gestor uuid,p_id uuid)
returns jsonb language plpgsql security invoker set search_path='' as $f$
declare v record;
begin
 if current_user<>'postgres' then
  raise exception 'EXCECAO_EXECUTOR_INTERNO' using errcode='42501';end if;
 if p_gestor is null or p_id is null then
  raise exception 'EXCECAO_PARAMETROS_INVALIDOS' using errcode='22023';end if;
 select * into v from prumo_private.s1_excecoes_caso_i61
 where id=p_id for update;
 if not found then raise exception 'EXCECAO_INEXISTENTE' using errcode='22023';end if;
 perform 1 from public.equipe_prumo_s1 e
  where e.ator_id in (p_gestor,v.operador_id)
  order by e.ator_id for share of e;
 if p_gestor is distinct from v.gestor_id
 or (select count(*) from public.equipe_prumo_s1
    where ator_id in (p_gestor,v.operador_id) and estado='ativo')<>2
 or not exists(select 1 from prumo_private.s1_gestor_operadores go
    where go.gestor_id=p_gestor and go.operador_id=v.operador_id
     and go.encerrado_em is null)
 then raise exception 'EXCECAO_SEM_AUTORIDADE_REVOGACAO'
 using errcode='42501';end if;
 if v.revogada_em is not null then
  return pg_catalog.jsonb_build_object('outcome','ALREADY_REVOKED');end if;
 update prumo_private.s1_excecoes_caso_i61
  set revogada_em=greatest(criada_em,pg_catalog.clock_timestamp())
  where id=p_id;
 insert into prumo_private.s1_excecoes_caso_eventos_i61(
  excecao_id,evento,solicitante_id) values(p_id,'REVOGADA',p_gestor);
 return pg_catalog.jsonb_build_object('outcome','REVOKED_CASE_ACCESS');
end $f$;

revoke all on function
 prumo_private.s1_prova_excecao_i61(uuid,uuid,uuid,uuid),
 prumo_private.s1_excecao_encerrar_i61(),
 prumo_private.s1_mover_excecao_caso_i61(uuid,uuid,uuid,uuid,uuid),
 prumo_private.s1_revogar_excecao_i61(uuid,uuid)
 from public,anon,authenticated,service_role;
revoke all on function
 public.s0_verificar_atribuicao(),prumo_private.s1_validar_nova_atribuicao()
 from public,anon,authenticated,service_role;
commit;
