-- I39/I40 — prototype setup shared by sequential and real-concurrent PG17 tests.
-- ONLY disposable local PG, never run against hosted Supabase or promote as migration.
-- Caller must manage transaction isolation/cleanup; creates prototype tables/functions.
\ir s1_053_issue10_disponibilidade_local_only.sql

-- Tabela laboratorial. A fila so expõe PENDENTE sem titular; nunca o
-- historico de casos atribuidos de outra equipe.
create table public.s1_fila_novos_59(
 concessionaria_id uuid not null,
 caso_id uuid not null,
 estado text not null default 'PENDENTE'
  check(estado in ('PENDENTE','ATRIBUIDO')),
 versao bigint not null default 1 check(versao>=1),
 atribuicao_id uuid references public.atribuicoes_humanas(id),
 criado_em timestamptz not null default pg_catalog.statement_timestamp(),
 atualizado_em timestamptz not null default pg_catalog.statement_timestamp(),
 primary key(concessionaria_id,caso_id),
 foreign key(concessionaria_id,caso_id)
  references public.casos_humanos(concessionaria_id,id),
 check((estado='PENDENTE' and atribuicao_id is null) or
       (estado='ATRIBUIDO' and atribuicao_id is not null))
);
alter table public.s1_fila_novos_59 enable row level security;
revoke all on public.s1_fila_novos_59 from public,anon,authenticated,service_role;
grant select(concessionaria_id,caso_id,estado,versao,criado_em)
 on public.s1_fila_novos_59 to authenticated;
create policy s1_59_fila_gestor_autorizado
 on public.s1_fila_novos_59 for select to authenticated using (
  estado='PENDENTE'
  and exists(select 1 from public.equipe_prumo_s1 e
   where e.ator_id=(select auth.uid()) and e.estado='ativo')
  and exists(select 1 from public.vinculos_papel_escopo v
   where v.ator_id=(select auth.uid())
    and v.concessionaria_id=s1_fila_novos_59.concessionaria_id
    and v.papel='gestor'
    and v.valido_desde<=pg_catalog.statement_timestamp()
    and (v.valido_ate is null or v.valido_ate>pg_catalog.statement_timestamp()))
 );

-- Acesso INTERNAL_ONLY, nenhum parametro p_gestor vindo do frontend.
-- Ordem de lock S0: caso ANTES da atribuicao/fila.
-- Em produção S0 precisara fornecer evento e versao/canal de handoff.
create function prumo_private.s1_59_tentar_novo(p_loja uuid,p_caso uuid)
returns jsonb language plpgsql security invoker set search_path='' as $fn$
declare v_destino uuid;v_atr uuid;v_estado text;v_existente uuid;
begin
 if current_user<>'postgres' then
  raise exception 'INTERNAL_ONLY' using errcode='42501';end if;
 if p_loja is null or p_caso is null then
  raise exception 'NOVO_INVALIDO' using errcode='22023';end if;
 perform 1 from public.casos_humanos h
  where h.concessionaria_id=p_loja and h.id=p_caso for update of h;
 if not found then raise exception 'CASO_S0_DESCONHECIDO' using errcode='22023';end if;
 select a.id into v_existente from public.atribuicoes_humanas a
  where a.concessionaria_id=p_loja and a.caso_id=p_caso
    and a.encerrada_em is null for update of a;
 select f.estado into v_estado from public.s1_fila_novos_59 f
  where f.concessionaria_id=p_loja and f.caso_id=p_caso for update of f;
 if v_existente is not null then
  if v_estado='PENDENTE' then
   raise exception 'FILA_TITULARIDADE_DIVERGENTE' using errcode='40001';end if;
  return pg_catalog.jsonb_build_object('outcome','ALREADY_OWNED');
 end if;
 if v_estado='ATRIBUIDO' then
  raise exception 'FILA_TITULARIDADE_DIVERGENTE' using errcode='40001';end if;
 -- Nao filtrar pela equipe do Gestor da loja nem pelo time de origem.
 -- Locks de equipe e grant impedem mudanca de elegibilidade ate o commit.
 select e.ator_id into v_destino from public.equipe_prumo_s1 e
 join prumo_private.s1_gestor_operadores g on
  g.operador_id=e.ator_id and g.encerrado_em is null
 join public.equipe_prumo_s1 chefe on
  chefe.ator_id=g.gestor_id and chefe.estado='ativo'
 join public.vinculos_papel_escopo v on
  v.ator_id=e.ator_id and v.concessionaria_id=p_loja
  and v.papel='operador'
  and v.valido_desde<=pg_catalog.statement_timestamp()
  and (v.valido_ate is null or v.valido_ate>pg_catalog.statement_timestamp())
 join public.concessionarias l on l.id=p_loja and l.ativo
 left join prumo_private.s1_disponibilidade_leads_10 d
  on d.operador_id=e.ator_id
 where e.estado='ativo' and coalesce(d.pausado,false)=false
 order by (select count(*) from public.atribuicoes_humanas a
            where a.operador_id=e.ator_id and a.encerrada_em is null),
          e.ator_id
 limit 1 for share of e,g,chefe,v,l;
 if v_destino is null then
  insert into public.s1_fila_novos_59(concessionaria_id,caso_id)
   values(p_loja,p_caso) on conflict(concessionaria_id,caso_id) do nothing;
  return pg_catalog.jsonb_build_object('outcome','QUEUED_UNOWNED');
 end if;
 -- Indice unico parcial S0 impede duas atribuicoes ativas (ultimo gate).
 insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id)
  values(p_loja,p_caso,v_destino) returning id into v_atr;
 if v_estado='PENDENTE' then
  update public.s1_fila_novos_59 set estado='ATRIBUIDO',
   atribuicao_id=v_atr,versao=versao+1,
   atualizado_em=pg_catalog.statement_timestamp()
   where concessionaria_id=p_loja and caso_id=p_caso;
 end if;
 return pg_catalog.jsonb_build_object('outcome','ASSIGNED_NEW',
  'operator_id',v_destino,'assignment_id',v_atr);
end $fn$;

-- Assuncao por Gestor: autorizacao somente da loja daquela fila,
-- CAS versionado, S0 case lock + um titular por caso. Nunca concede loja.
create function prumo_private.s1_59_assumir(
 p_gestor uuid,p_loja uuid,p_caso uuid,p_versao_esperada bigint)
returns jsonb language plpgsql security invoker set search_path='' as $fn$
declare v_estado text;v_versao bigint;v_atr uuid;
begin
 if current_user<>'postgres' then
  raise exception 'INTERNAL_ONLY' using errcode='42501';end if;
 if p_gestor is null or p_loja is null or p_caso is null
  or p_versao_esperada is null or p_versao_esperada<1 then
  raise exception 'ASSUNCAO_INVALIDA' using errcode='22023';end if;
 perform 1 from public.casos_humanos h
  where h.concessionaria_id=p_loja and h.id=p_caso for update of h;
 if not found then raise exception 'CASO_DESCONHECIDO' using errcode='22023';end if;
 select f.estado,f.versao into v_estado,v_versao
  from public.s1_fila_novos_59 f
  where f.concessionaria_id=p_loja and f.caso_id=p_caso for update of f;
 if v_estado is distinct from 'PENDENTE' or v_versao<>p_versao_esperada then
  raise exception 'FILA_CAS_OBSOLETO' using errcode='40001';end if;
 -- Revalidar alçada sob locks de conta, loja e vinculo.
 perform 1 from public.equipe_prumo_s1 e
  join public.vinculos_papel_escopo v
   on v.ator_id=e.ator_id and v.concessionaria_id=p_loja
    and v.papel='gestor'
    and v.valido_desde<=pg_catalog.statement_timestamp()
    and (v.valido_ate is null or v.valido_ate>pg_catalog.statement_timestamp())
  join public.concessionarias l on l.id=p_loja and l.ativo
  where e.ator_id=p_gestor and e.estado='ativo'
  for share of e,v,l;
 if not found then
  raise exception 'GESTOR_SEM_AUTORIZACAO_LOJA' using errcode='42501';end if;
 if exists(select 1 from public.atribuicoes_humanas a
  where a.concessionaria_id=p_loja and a.caso_id=p_caso
    and a.encerrada_em is null) then
  raise exception 'CASO_JA_POSSUI_TITULAR' using errcode='40001';end if;
 insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id)
  values(p_loja,p_caso,p_gestor) returning id into v_atr;
 update public.s1_fila_novos_59 set estado='ATRIBUIDO',
  versao=versao+1,atribuicao_id=v_atr,
  atualizado_em=pg_catalog.statement_timestamp()
  where concessionaria_id=p_loja and caso_id=p_caso and estado='PENDENTE';
 return pg_catalog.jsonb_build_object('outcome','CLAIMED_BY_MANAGER',
  'operator_id',p_gestor,'assignment_id',v_atr);
end $fn$;
revoke all on function prumo_private.s1_59_tentar_novo(uuid,uuid),
 prumo_private.s1_59_assumir(uuid,uuid,uuid,bigint)
 from public,anon,authenticated,service_role;
