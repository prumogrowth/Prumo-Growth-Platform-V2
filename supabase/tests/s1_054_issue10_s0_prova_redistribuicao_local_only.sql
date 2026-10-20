-- S0/S1 issue #10 - I33: prova de inicio humano e remanejamento seletivo,
-- somente no PG17 CI; S0 real/Meta/REST ainda NAO possuem produtor confiavel.
-- Segrega uma EVIDENCIA SIMULADA gerada por fixture S0, nunca por gestor.
create table prumo_private.s0_contato_humano_prova_10 (
 concessionaria_id uuid not null,
 caso_id uuid not null,
 atribuicao_id uuid not null references public.atribuicoes_humanas(id),
 estado text not null check (estado in ('SEM_INICIO_CONFIRMADO','INICIADO')),
 versao bigint not null default 1 check(versao>=1),
 fonte_evento text not null check(length(fonte_evento) between 8 and 100),
 atualizado_em timestamptz not null default pg_catalog.statement_timestamp(),
 primary key(concessionaria_id,caso_id),
 foreign key(concessionaria_id,caso_id) references public.casos_humanos(concessionaria_id,id)
);
create table prumo_private.s0_contato_humano_eventos_10 (
 id bigint generated always as identity primary key,
 concessionaria_id uuid not null,
 caso_id uuid not null,
 atribuicao_id uuid not null,
 estado text not null check(estado in ('SEM_INICIO_CONFIRMADO','INICIADO')),
 fonte_evento text not null,
 versao bigint not null,
 registrado_em timestamptz not null default pg_catalog.statement_timestamp(),
 unique(concessionaria_id,fonte_evento),
 foreign key(concessionaria_id,caso_id)
  references public.casos_humanos(concessionaria_id,id)
);
alter table prumo_private.s0_contato_humano_prova_10 enable row level security;
alter table prumo_private.s0_contato_humano_eventos_10 enable row level security;
revoke all on prumo_private.s0_contato_humano_prova_10,
 prumo_private.s0_contato_humano_eventos_10
 from public,anon,authenticated,service_role;
revoke all on sequence prumo_private.s0_contato_humano_eventos_10_id_seq
 from public,anon,authenticated,service_role;
create trigger s0_10_contato_hist_immutable before update or delete
 on prumo_private.s0_contato_humano_eventos_10 for each row
 execute function prumo_private.s1_proibir_alteracao_historico();
create trigger s0_10_contato_hist_no_truncate before truncate
 on prumo_private.s0_contato_humano_eventos_10 for each statement
 execute function prumo_private.s1_proibir_alteracao_historico();

-- Este simulador S0 recebe evidência confiada ao fixture PostgreSQL
-- NAO demonstra assinatura da Meta nem entrega humana real. A fonte negativa
-- teria de ser produzida pelo núcleo sob o MESMO lock do evento positivo.
create function prumo_private.s0_registrar_contato_humano_fixture_10(
 p_loja uuid,p_caso uuid,p_atribuicao uuid,p_estado text,p_fonte text)
returns jsonb language plpgsql security invoker set search_path='' as $fn$
declare v_id uuid;v_estado text;v_versao bigint;v_ref uuid;v_nova bigint;
begin
 if current_user<>'postgres' then
  raise exception 'S0_FIXTURE_INTERNA' using errcode='42501';end if;
 if p_loja is null or p_caso is null or p_atribuicao is null
 or p_estado not in ('SEM_INICIO_CONFIRMADO','INICIADO')
 or p_estado is null or p_fonte is null
 or length(p_fonte) not between 8 and 100 then
  raise exception 'EVIDENCIA_INVALIDA' using errcode='22023';end if;

 -- Sempre primeiro trava o CASO, depois a ATRIBUICAO: mesma ordem da
 -- redistribuicao S1, impedindo resposta humana e movimento concorrente.
 select h.id into v_id from public.casos_humanos h
 where h.concessionaria_id=p_loja and h.id=p_caso for update of h;
 if v_id is null then raise exception 'CASO_DESCONHECIDO' using errcode='42501';end if;
 select a.id into v_ref from public.atribuicoes_humanas a
 where a.concessionaria_id=p_loja and a.caso_id=p_caso
   and a.id=p_atribuicao and a.encerrada_em is null
 for update of a;
 if v_ref is null then
  raise exception 'ATRIBUICAO_NAO_ATUAL' using errcode='40001';end if;

 select e.estado,e.versao into v_estado,v_versao
 from prumo_private.s0_contato_humano_prova_10 e
 where e.concessionaria_id=p_loja and e.caso_id=p_caso for update;
 if v_estado='INICIADO' then
  if p_estado='INICIADO' then
   return pg_catalog.jsonb_build_object('outcome','ALREADY_STARTED',
     'version',v_versao);end if;
  raise exception 'INICIO_HUMANO_IRREVERSIVEL' using errcode='42501';
 end if;
 if v_estado='SEM_INICIO_CONFIRMADO' and p_estado='SEM_INICIO_CONFIRMADO' then
  if exists(select 1 from prumo_private.s0_contato_humano_eventos_10 ev
            where ev.concessionaria_id=p_loja and ev.caso_id=p_caso
            and ev.fonte_evento=p_fonte) then
   return pg_catalog.jsonb_build_object('outcome','ALREADY_CONFIRMED',
     'version',v_versao);end if;
  raise exception 'EVIDENCIA_NEGATIVA_DUPLICADA' using errcode='23505';
 end if;
 if v_estado is null then
  v_nova:=1;
  insert into prumo_private.s0_contato_humano_prova_10(
   concessionaria_id,caso_id,atribuicao_id,estado,versao,fonte_evento)
  values(p_loja,p_caso,p_atribuicao,p_estado,1,p_fonte);
 else
  v_nova:=v_versao+1;
  update prumo_private.s0_contato_humano_prova_10
  set estado=p_estado,versao=v_nova,fonte_evento=p_fonte,
      atualizado_em=pg_catalog.statement_timestamp()
  where concessionaria_id=p_loja and caso_id=p_caso;
 end if;
 insert into prumo_private.s0_contato_humano_eventos_10(
  concessionaria_id,caso_id,atribuicao_id,estado,fonte_evento,versao)
 values(p_loja,p_caso,p_atribuicao,p_estado,p_fonte,v_nova);
 return pg_catalog.jsonb_build_object('outcome',
  case when p_estado='INICIADO' then 'HUMAN_STARTED' else 'NOT_STARTED_PROVEN' end,
  'version',v_nova);
end $fn$;

create table prumo_private.s1_movimentos_pause_10 (
 id bigint generated always as identity primary key,
 gestor_id uuid not null references public.atores(id),
 concessionaria_id uuid not null,
 caso_id uuid not null,
 atribuicao_anterior_id uuid not null unique references public.atribuicoes_humanas(id),
 atribuicao_nova_id uuid not null unique references public.atribuicoes_humanas(id),
 origem_id uuid not null references public.atores(id),
 destino_id uuid not null references public.atores(id),
 versao_disponibilidade bigint not null,
 versao_prova bigint not null,
 registrado_em timestamptz not null default pg_catalog.statement_timestamp(),
 foreign key(concessionaria_id,caso_id) references public.casos_humanos(concessionaria_id,id),
 check(origem_id<>destino_id)
);
alter table prumo_private.s1_movimentos_pause_10 enable row level security;
revoke all on prumo_private.s1_movimentos_pause_10
 from public,anon,authenticated,service_role;
revoke all on sequence prumo_private.s1_movimentos_pause_10_id_seq
 from public,anon,authenticated,service_role;
create trigger s1_10_auto_hist_immutable before update or delete on
 prumo_private.s1_movimentos_pause_10 for each row
 execute function prumo_private.s1_proibir_alteracao_historico();
create trigger s1_10_auto_hist_no_truncate before truncate on
 prumo_private.s1_movimentos_pause_10 for each statement
 execute function prumo_private.s1_proibir_alteracao_historico();

create function prumo_private.s1_redistribuir_pausado_provas_10(
 p_gestor uuid,p_operador uuid,p_versao bigint)
returns jsonb language plpgsql security invoker set search_path='' as $fn$
declare
 v_estado text;v_disponivel boolean;v_versao bigint;
 v_atr record;v_prova record;v_destino uuid;v_nova uuid;
 v_movidos integer:=0;v_sem_elegivel integer:=0;
 v_iniciados integer:=0;v_sem_prova integer:=0;v_obsoletos integer:=0;
begin
 if current_user<>'postgres' then
  raise exception 'EXECUTOR_LOCAL_APENAS' using errcode='42501';end if;
 if p_gestor is null or p_operador is null or p_versao is null or p_versao<1
 then raise exception 'PARAMETROS_INVALIDOS' using errcode='22023';end if;
 perform 1 from public.equipe_prumo_s1 e where e.ator_id in
  (p_gestor,p_operador) order by e.ator_id for share of e;
 select d.pausado,d.versao into v_disponivel,v_versao
 from prumo_private.s1_disponibilidade_leads_10 d
 where d.operador_id=p_operador for share of d;
 if v_versao is distinct from p_versao or not coalesce(v_disponivel,false) then
  raise exception 'PAUSA_INATIVA_OU_VERSAO_OBSOLETA' using errcode='40001';end if;
 perform 1 from prumo_private.s1_gestor_operadores g
 where g.gestor_id=p_gestor and g.operador_id=p_operador
   and g.encerrado_em is null for share of g;
 if not found or not prumo_private.s1_pode_administrar_operador(
    p_gestor,null,'suspender_temporariamente',p_operador) then
  raise exception 'GESTOR_FORA_DA_EQUIPE' using errcode='42501';end if;

 for v_atr in
  select a.id,a.concessionaria_id,a.caso_id,a.operador_id,a.atribuida_em,
         c.status_comercial
  from public.atribuicoes_humanas a
  join public.casos_humanos h
   on h.concessionaria_id=a.concessionaria_id and h.id=a.caso_id
  join public.ciclos_comerciais c
   on c.concessionaria_id=h.concessionaria_id and c.id=h.ciclo_id
  where a.operador_id=p_operador and a.encerrada_em is null
  order by a.concessionaria_id,a.caso_id
 loop
  -- Trava CASO e ATRIBUICAO na mesma ordem de S0.
  perform 1 from public.casos_humanos h
  where h.concessionaria_id=v_atr.concessionaria_id and h.id=v_atr.caso_id
  for update of h;
  perform 1 from public.atribuicoes_humanas a
  where a.id=v_atr.id and a.encerrada_em is null for update of a;
  if not found then
   v_obsoletos:=v_obsoletos+1;continue;end if;
  if v_atr.status_comercial in ('vendido','perdido') then
   v_iniciados:=v_iniciados+1;continue;end if;
  select p.estado,p.versao,p.atribuicao_id into v_prova
  from prumo_private.s0_contato_humano_prova_10 p
  where p.concessionaria_id=v_atr.concessionaria_id
    and p.caso_id=v_atr.caso_id for update of p;
  if not found or v_prova.atribuicao_id<>v_atr.id then
   v_sem_prova:=v_sem_prova+1;continue;end if;
  if v_prova.estado='INICIADO' then
   v_iniciados:=v_iniciados+1;continue;end if;
  if v_prova.estado<>'SEM_INICIO_CONFIRMADO' then
   v_sem_prova:=v_sem_prova+1;continue;end if;
  v_destino:=null;
  -- Elegivel APENAS na mesma equipe, nao pausado, grant da LOJA valido.
  select dest.ator_id into v_destino from public.equipe_prumo_s1 dest
  join prumo_private.s1_gestor_operadores chefe
   on chefe.gestor_id=p_gestor and chefe.operador_id=dest.ator_id
    and chefe.encerrado_em is null
  join public.vinculos_papel_escopo grant_l
   on grant_l.ator_id=dest.ator_id
    and grant_l.concessionaria_id=v_atr.concessionaria_id
    and grant_l.papel='operador'
    and grant_l.valido_desde<=pg_catalog.statement_timestamp()
    and (grant_l.valido_ate is null or grant_l.valido_ate>pg_catalog.statement_timestamp())
  join public.concessionarias l on l.id=grant_l.concessionaria_id and l.ativo
  left join prumo_private.s1_disponibilidade_leads_10 disp
   on disp.operador_id=dest.ator_id
  where dest.ator_id<>p_operador and dest.estado='ativo'
   and coalesce(disp.pausado,false)=false
  order by (select pg_catalog.count(*) from public.atribuicoes_humanas z
    where z.operador_id=dest.ator_id and z.encerrada_em is null),dest.ator_id
  limit 1 for share of dest,chefe,grant_l,l;
  if v_destino is null then
   -- Fundamental: NAO encerra a atribuicao se nao ha substituto.
   v_sem_elegivel:=v_sem_elegivel+1;continue;
  end if;
  update public.atribuicoes_humanas
   set encerrada_em=greatest(v_atr.atribuida_em,pg_catalog.statement_timestamp())
   where id=v_atr.id and encerrada_em is null;
  insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id)
  values(v_atr.concessionaria_id,v_atr.caso_id,v_destino) returning id into v_nova;
  insert into prumo_private.s1_movimentos_pause_10(
   gestor_id,concessionaria_id,caso_id,atribuicao_anterior_id,
   atribuicao_nova_id,origem_id,destino_id,versao_disponibilidade,versao_prova)
  values(p_gestor,v_atr.concessionaria_id,v_atr.caso_id,v_atr.id,
   v_nova,p_operador,v_destino,p_versao,v_prova.versao);
  v_movidos:=v_movidos+1;
 end loop;
 return pg_catalog.jsonb_build_object('outcome','RECONCILED',
  'redistributed',v_movidos,'kept_no_eligible',v_sem_elegivel,
  'kept_started',v_iniciados,'kept_without_proof',v_sem_prova,
  'skipped_stale',v_obsoletos,'intake_version',v_versao);
end $fn$;
revoke all on function
 prumo_private.s0_registrar_contato_humano_fixture_10(uuid,uuid,uuid,text,text),
 prumo_private.s1_redistribuir_pausado_provas_10(uuid,uuid,bigint)
 from public,anon,authenticated,service_role;
