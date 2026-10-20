-- S1-002 / issue #10 — nova pausa so novos leads, fase 1 fail-closed.
-- FIXTURE ISOLADA PG17: sem migration comercial operacional ou deploy.
-- Aplicar APOS testes historicos I11/I12. Nenhuma API aberta.
create table prumo_private.s1_disponibilidade_leads_10(
 operador_id uuid primary key references public.equipe_prumo_s1(ator_id),
 pausado boolean not null default false,
 versao bigint not null default 1 check(versao>0),
 atualizado_em timestamptz not null default pg_catalog.statement_timestamp()
);
create table prumo_private.s1_eventos_disponibilidade_10(
 id bigint generated always as identity primary key,
 solicitante_id uuid not null references public.atores(id),
 operador_id uuid not null references public.atores(id),
 versao_anterior bigint not null,
 versao_nova bigint not null,
 pausado boolean not null,
 ocorrido_em timestamptz not null default pg_catalog.statement_timestamp(),
 check(versao_nova=versao_anterior+1)
);
alter table prumo_private.s1_disponibilidade_leads_10 enable row level security;
alter table prumo_private.s1_eventos_disponibilidade_10 enable row level security;
revoke all on prumo_private.s1_disponibilidade_leads_10,prumo_private.s1_eventos_disponibilidade_10
 from public,anon,authenticated,service_role;
revoke all on sequence prumo_private.s1_eventos_disponibilidade_10_id_seq
 from public,anon,authenticated,service_role;
create trigger s1_10_eventos_immutable before update or delete on
 prumo_private.s1_eventos_disponibilidade_10 for each row
 execute function prumo_private.s1_proibir_alteracao_historico();
create trigger s1_10_eventos_no_truncate before truncate on
 prumo_private.s1_eventos_disponibilidade_10 for each statement
 execute function prumo_private.s1_proibir_alteracao_historico();

-- Tabela de excecao somente de PREPARACAO: a autorizacao S0/RLS continua
-- NEGADA enquanto o nucleo nao homologar acesso restrito por caso.
create table prumo_private.s1_excecoes_caso_preparacao_10(
 id uuid primary key default gen_random_uuid(),
 concessionaria_id uuid not null,
 caso_id uuid not null,
 atribuicao_id uuid not null unique references public.atribuicoes_humanas(id),
 operador_id uuid not null references public.atores(id),
 autorizado_por uuid not null references public.atores(id),
 criado_em timestamptz not null default pg_catalog.statement_timestamp(),
 revogado_em timestamptz,
 check(revogado_em is null or revogado_em>=criado_em),
 foreign key(concessionaria_id,caso_id)
  references public.casos_humanos(concessionaria_id,id)
);
alter table prumo_private.s1_excecoes_caso_preparacao_10 enable row level security;
revoke all on prumo_private.s1_excecoes_caso_preparacao_10
 from public,anon,authenticated,service_role;
-- Importante: NAO criar permissao SELECT/RLS por meio desta tabela.
-- Isto e PREPARACAO nao uma capacidade operacional.

create function prumo_private.s1_definir_disponibilidade_leads_10(
 p_gestor uuid,p_operador uuid,p_pausar boolean,p_versao_esperada bigint)
returns jsonb language plpgsql security invoker set search_path='' as $fn$
declare
 v_versao bigint;
 v_atual boolean;
 v_conta text;
begin
 if current_user<>'postgres' then
  raise exception 'INTERNAL_ONLY' using errcode='42501';end if;
 if p_gestor is null or p_operador is null or p_pausar is null
 or p_versao_esperada is null or p_versao_esperada<1 then
  raise exception 'PARAMETROS_DISPONIBILIDADE_INVALIDOS' using errcode='22023';end if;

 -- Serializar chefia/conta e verificar novamente sob lock.
 perform 1 from public.equipe_prumo_s1 e
  where e.ator_id in (p_gestor,p_operador)
  order by e.ator_id for update of e;
 select e.estado into v_conta from public.equipe_prumo_s1 e
 where e.ator_id=p_operador;
 if v_conta is distinct from 'ativo' then
  raise exception 'CONTA_NAO_ATIVA' using errcode='42501';end if;
 perform 1 from prumo_private.s1_gestor_operadores g
 where g.gestor_id=p_gestor and g.operador_id=p_operador
  and g.encerrado_em is null for share of g;
 if not found or not prumo_private.s1_pode_administrar_operador(
   p_gestor,null,'suspender_temporariamente',p_operador) then
  raise exception 'GESTOR_SEM_ALCADA' using errcode='42501';end if;
 insert into prumo_private.s1_disponibilidade_leads_10(operador_id)
 values(p_operador) on conflict(operador_id) do nothing;
 select pausado,versao into v_atual,v_versao
 from prumo_private.s1_disponibilidade_leads_10
 where operador_id=p_operador for update;
 if v_versao<>p_versao_esperada then
  raise exception 'DISPONIBILIDADE_VERSAO_OBSOLETA' using errcode='22023';end if;
 if v_atual=p_pausar then
  return pg_catalog.jsonb_build_object(
   'outcome','ALREADY_APPLIED','operator_id',p_operador,
   'intake_paused',v_atual,'version',v_versao,
   'redistribution','DEFERRED_S0_PROOF');
 end if;
 update prumo_private.s1_disponibilidade_leads_10
 set pausado=p_pausar,versao=v_versao+1,atualizado_em=pg_catalog.statement_timestamp()
 where operador_id=p_operador;
 insert into prumo_private.s1_eventos_disponibilidade_10(
  solicitante_id,operador_id,versao_anterior,versao_nova,pausado)
 values(p_gestor,p_operador,v_versao,v_versao+1,p_pausar);
 -- S0 ainda nao entregou evento provado, com lock serializado, de que
 -- houve ou nao inicio humano. NENHUMA atribuicao e fechada automaticamente.
 return pg_catalog.jsonb_build_object(
  'outcome',case when p_pausar then 'INTAKE_PAUSED' else 'INTAKE_RESUMED' end,
  'operator_id',p_operador,'intake_paused',p_pausar,'version',v_versao+1,
  'redistribution','DEFERRED_S0_PROOF');
end $fn$;

-- Bloquear novas atribuicoes a quem tem intake pausado. Casos com atribuicao
-- JA EXISTENTE continuam no titular e sob a RLS historica da conta ATIVA.
create function prumo_private.s1_guard_entrada_pausada_10()
returns trigger language plpgsql security invoker set search_path='' as $fn$
begin
 if current_user<>'postgres' then
  raise exception 'INTERNAL_ONLY' using errcode='42501';end if;
 perform 1 from public.equipe_prumo_s1 e where e.ator_id=new.operador_id
  for share of e;
 if exists(select 1 from prumo_private.s1_disponibilidade_leads_10 d
   where d.operador_id=new.operador_id and d.pausado) then
  raise exception 'NOVOS_LEADS_PAUSADOS' using errcode='23514';end if;
 return new;
end $fn$;
create trigger s1_10_guard_novos_leads
 before insert or update of operador_id on public.atribuicoes_humanas
 for each row execute function prumo_private.s1_guard_entrada_pausada_10();

-- OBSOLESCENCIA DEFENSIVA. O gateway I20-I30 ainda oferece funcoes
-- antigas perigosas: elas nao podem voltar a suspender a conta neste
-- estado de teste. A nova assinatura tem CAS e autor confiavel.
create or replace function prumo_private.s1_pausar_operador_da_equipe(
 p_solicitante uuid,p_operador uuid,p_motivo_codigo text)
returns jsonb language plpgsql security invoker set search_path='' as $fn$
begin
 raise exception 'PAUSA_LEGADA_DESABILITADA_USAR_INTK10'
 using errcode='42501';
end $fn$;
create or replace function prumo_private.s1_reativar_operador_da_equipe(
 p_solicitante uuid,p_operador uuid)
returns jsonb language plpgsql security invoker set search_path='' as $fn$
begin
 raise exception 'RETOMADA_LEGADA_DESABILITADA_USAR_INTK10'
 using errcode='42501';
end $fn$;
revoke all on function
 prumo_private.s1_definir_disponibilidade_leads_10(uuid,uuid,boolean,bigint),
 prumo_private.s1_guard_entrada_pausada_10(),
 prumo_private.s1_pausar_operador_da_equipe(uuid,uuid,text),
 prumo_private.s1_reativar_operador_da_equipe(uuid,uuid)
 from public,anon,authenticated,service_role;
