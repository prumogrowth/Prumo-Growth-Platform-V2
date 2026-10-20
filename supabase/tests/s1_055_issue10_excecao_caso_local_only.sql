-- ISSUE #10 / I35. Exceção estritamente por CASO, fixture local descartável.
-- Executar apos s1_053 e s1_054. NAO E UMA MIGRATION OPERACIONAL.
-- RLS para casos, atribuicoes, conversas e mensagens, SEM grant de loja.
create table prumo_private.s1_excecoes_55 (
 id uuid primary key default gen_random_uuid(),
 concessionaria_id uuid not null,
 caso_id uuid not null,
 atribuicao_id uuid not null unique,
 operador_id uuid not null references public.atores(id),
 gestor_id uuid not null references public.atores(id),
 criada_em timestamptz not null default pg_catalog.statement_timestamp(),
 revogada_em timestamptz,
 foreign key(concessionaria_id,caso_id)
  references public.casos_humanos(concessionaria_id,id),
 foreign key(atribuicao_id) references public.atribuicoes_humanas(id)
  deferrable initially deferred,
 check(revogada_em is null or revogada_em>=criada_em)
);
create table prumo_private.s1_excecoes_eventos_55 (
 id bigint generated always as identity primary key,
 excecao_id uuid not null references prumo_private.s1_excecoes_55(id),
 tipo text not null check(tipo in ('CRIADA','REVOGADA')),
 ator_id uuid not null references public.atores(id),
 registrado_em timestamptz not null default pg_catalog.statement_timestamp()
);
alter table prumo_private.s1_excecoes_55 enable row level security;
alter table prumo_private.s1_excecoes_eventos_55 enable row level security;
revoke all on prumo_private.s1_excecoes_55,prumo_private.s1_excecoes_eventos_55
 from public,anon,authenticated,service_role;
revoke all on sequence prumo_private.s1_excecoes_eventos_55_id_seq
 from public,anon,authenticated,service_role;
create trigger s1_55_hist_immutable before update or delete on
 prumo_private.s1_excecoes_eventos_55 for each row
 execute function prumo_private.s1_proibir_alteracao_historico();
create trigger s1_55_hist_no_truncate before truncate on
 prumo_private.s1_excecoes_eventos_55 for each statement
 execute function prumo_private.s1_proibir_alteracao_historico();

-- O predicado e PUBLICAVEL apenas como booleano, nunca lista de casos.
-- SECURITY DEFINER sobre funcao fixa, auth.uid() do JWT, revogacao e
-- atribuicao corrente verificadas em toda leitura.
create function prumo_private.s1_caso_excepcional_autorizado_55(
 p_loja uuid,p_caso uuid)
returns boolean language sql stable security definer set search_path='' as $fn$
 select p_loja is not null and p_caso is not null
 and (select auth.uid()) is not null
 and exists(
   select 1 from prumo_private.s1_excecoes_55 e
   join public.atribuicoes_humanas a on a.id=e.atribuicao_id
      and a.concessionaria_id=e.concessionaria_id
      and a.caso_id=e.caso_id and a.operador_id=e.operador_id
      and a.encerrada_em is null
   join public.equipe_prumo_s1 op on op.ator_id=e.operador_id and op.estado='ativo'
   join public.equipe_prumo_s1 g on g.ator_id=e.gestor_id and g.estado='ativo'
   join prumo_private.s1_gestor_operadores chefe
      on chefe.gestor_id=e.gestor_id and chefe.operador_id=e.operador_id
      and chefe.encerrado_em is null
   join public.concessionarias loja
      on loja.id=e.concessionaria_id and loja.ativo
   where e.concessionaria_id=p_loja and e.caso_id=p_caso
      and e.revogada_em is null
      and e.operador_id=(select auth.uid())
 );
$fn$;
revoke all on function
 prumo_private.s1_caso_excepcional_autorizado_55(uuid,uuid)
 from public,anon,service_role;
grant execute on function
 prumo_private.s1_caso_excepcional_autorizado_55(uuid,uuid)
 to authenticated;
-- Em tabelas public, a policy S1 restritiva 'equipe ativo' segue obrigatoria.
create policy s1_55_caso_select on public.casos_humanos
 for select to authenticated using (
  prumo_private.s1_caso_excepcional_autorizado_55(concessionaria_id,id));
create policy s1_55_atribuicao_select on public.atribuicoes_humanas
 for select to authenticated using (
  encerrada_em is null and
  prumo_private.s1_caso_excepcional_autorizado_55(concessionaria_id,caso_id));
create policy s1_55_conversa_select on public.conversas
 for select to authenticated using (
  caso_id is not null and
  prumo_private.s1_caso_excepcional_autorizado_55(concessionaria_id,caso_id));
-- O S0 original autoriza mensagens pelo SELECT de conversa visivel.
-- Para quem NAO possui grant da loja, limitar ainda mais ao caso do corpo,
-- nunca liberar mensagens caso_id NULL ou de um caso de outra conversa.
create policy s1_55_mensagens_restrict as restrictive on public.mensagens
 for select to authenticated using (
  exists(select 1 from public.vinculos_papel_escopo v
    where v.ator_id=(select auth.uid())
      and v.concessionaria_id=mensagens.concessionaria_id
      and v.papel in ('gestor','operador','responsavel')
      and v.valido_desde<=pg_catalog.statement_timestamp()
      and (v.valido_ate is null or v.valido_ate>pg_catalog.statement_timestamp())
  ) or (
   caso_id is not null
   and prumo_private.s1_caso_excepcional_autorizado_55(concessionaria_id,caso_id)
   and exists(select 1 from public.conversas co
    where co.concessionaria_id=mensagens.concessionaria_id
      and co.id=mensagens.conversa_id and co.caso_id=mensagens.caso_id)
  )
 );
-- Politica de envio da excecao ainda exige ID atribuido atual, evento
-- simulado, autoria JWT e conversa do MESMO caso. Sem grant amplo.
create policy s1_55_msg_insert_exception on public.mensagens
 for insert to authenticated with check(
  direcao='saida' and origem='simulado' and id_externo is null
  and enviada_por=(select auth.uid()) and caso_id is not null
  and prumo_private.s1_caso_excepcional_autorizado_55(concessionaria_id,caso_id)
  and exists(select 1 from public.conversas co
   where co.concessionaria_id=mensagens.concessionaria_id
      and co.id=mensagens.conversa_id
      and co.canal_id=mensagens.canal_id
      and co.caso_id=mensagens.caso_id)
 );

-- S0 exige grant por concessionaria para INSERT de atribuicao. Esta
-- excecao e verificada pelo id exato da futura atribuicao, preparado
-- dentro da mesma transacao, FK deferrable e acionamento privado.
create or replace function public.s0_verificar_atribuicao()
returns trigger language plpgsql security invoker set search_path='' as $fn$
begin
 if exists(select 1 from public.vinculos_papel_escopo v
  where v.ator_id=new.operador_id and v.concessionaria_id=new.concessionaria_id
  and v.papel in ('gestor','operador')
  and v.valido_desde<=pg_catalog.statement_timestamp()
  and (v.valido_ate is null or v.valido_ate>pg_catalog.statement_timestamp())
 ) then return new;end if;
 if current_user='postgres' and exists(
   select 1 from prumo_private.s1_excecoes_55 x
   where x.atribuicao_id=new.id and x.concessionaria_id=new.concessionaria_id
     and x.caso_id=new.caso_id and x.operador_id=new.operador_id
     and x.revogada_em is null
 ) then return new;end if;
 raise exception 'operador sem concessao ativa na loja ou excecao ao caso'
 using errcode='23514';
end $fn$;
revoke all on function public.s0_verificar_atribuicao()
 from public,anon,authenticated,service_role;

-- Encerramento de atribuicao elimina automaticamente entitlement anterior.
create function prumo_private.s1_revogar_excecao_atribuicao_55()
returns trigger language plpgsql security invoker set search_path='' as $fn$
declare x record;
begin
 if old.encerrada_em is null and new.encerrada_em is not null then
  for x in update prumo_private.s1_excecoes_55
    set revogada_em=pg_catalog.statement_timestamp()
    where atribuicao_id=old.id and revogada_em is null
    returning id,gestor_id loop
   insert into prumo_private.s1_excecoes_eventos_55(excecao_id,tipo,ator_id)
   values(x.id,'REVOGADA',x.gestor_id);
  end loop;
 end if;
 return new;
end $fn$;
create trigger s1_55_revogar_ao_encerrar
 after update of encerrada_em on public.atribuicoes_humanas for each row
 execute function prumo_private.s1_revogar_excecao_atribuicao_55();

-- Novo contrato independente do I12. So gestor da MESMA equipe do
-- titular e destino; gestor nao ganha poder sobre concesao A/B/C.
create function prumo_private.s1_mover_excecao_caso_55(
 p_gestor uuid,p_loja uuid,p_caso uuid,p_atribuicao_esperada uuid,p_destino uuid)
returns jsonb language plpgsql security invoker set search_path='' as $fn$
declare
 v_origem uuid;v_achado uuid;v_data timestamptz;v_novo uuid;v_excecao uuid;
 v_motivo text;v_status text;v_chefias integer;
begin
 if current_user<>'postgres' then
  raise exception 'INTERNAL_ONLY' using errcode='42501';end if;
 if p_gestor is null or p_loja is null or p_caso is null
 or p_atribuicao_esperada is null or p_destino is null
 or p_gestor=p_destino then
  raise exception 'PARAMETROS_EXCECAO_INVALIDOS' using errcode='22023';end if;
 select a.operador_id into v_origem
 from public.atribuicoes_humanas a
 where a.id=p_atribuicao_esperada and a.caso_id=p_caso
   and a.concessionaria_id=p_loja and a.encerrada_em is null;
 if v_origem is null or v_origem=p_destino then
  raise exception 'ATRIBUICAO_ESPERADA_INVALIDA' using errcode='22023';end if;

 -- Ordem de locks da equipe antes de caso/atribuicao = I13.
 perform 1 from public.equipe_prumo_s1 e
 where e.ator_id in (p_gestor,v_origem,p_destino)
 order by e.ator_id for share of e;
 if (select count(*) from public.equipe_prumo_s1
      where ator_id in (p_gestor,v_origem,p_destino) and estado='ativo')<>3 then
  raise exception 'EQUIPE_NAO_ATIVA' using errcode='42501';end if;
 select count(*) into v_chefias from (
  select g.operador_id from prumo_private.s1_gestor_operadores g
   where g.gestor_id=p_gestor and g.encerrado_em is null
    and g.operador_id in (v_origem,p_destino)
   order by g.operador_id for share of g
 ) chefias;
 if v_chefias<>2 then
  raise exception 'GESTOR_FORA_DA_EQUIPE' using errcode='42501';end if;
 -- Origem precisa deter o caso e permissao de loja vigente; destino NAO.
 perform 1 from public.vinculos_papel_escopo v
 where v.ator_id=v_origem and v.concessionaria_id=p_loja and v.papel='operador'
   and v.valido_desde<=pg_catalog.statement_timestamp()
   and (v.valido_ate is null or v.valido_ate>pg_catalog.statement_timestamp())
 for share of v;
 if not found and not exists(
  select 1 from prumo_private.s1_excecoes_55 x
  where x.atribuicao_id=p_atribuicao_esperada and x.revogada_em is null
    and x.operador_id=v_origem and x.concessionaria_id=p_loja and x.caso_id=p_caso
 ) then raise exception 'ORIGEM_SEM_TITULARIDADE_AUTORIZADA' using errcode='42501';end if;
 -- Até a decisão de produto sobre transferência manual para operador
 -- pausado, negar como opção conservadora na exceção.
 if exists(select 1 from prumo_private.s1_disponibilidade_leads_10 d
   where d.operador_id=p_destino and d.pausado)
 then raise exception 'DESTINO_COM_INTAKE_PAUSADO' using errcode='42501';end if;
 -- Excepcao nao se aplica se destino ja tem grant da loja.
 if exists(select 1 from public.vinculos_papel_escopo v
  where v.ator_id=p_destino and v.concessionaria_id=p_loja
    and v.papel in ('responsavel','gestor','operador')
    and v.valido_desde<=pg_catalog.statement_timestamp()
    and (v.valido_ate is null or v.valido_ate>pg_catalog.statement_timestamp())
 ) then
  raise exception 'USAR_CAMINHO_NORMAL_COM_GRANT' using errcode='22023';end if;
 perform 1 from public.concessionarias l where l.id=p_loja and l.ativo for share of l;
 if not found then raise exception 'LOJA_INATIVA' using errcode='42501';end if;
 select h.motivo_simulado,c.status_comercial into v_motivo,v_status
 from public.casos_humanos h
 join public.ciclos_comerciais c on c.id=h.ciclo_id
   and c.concessionaria_id=h.concessionaria_id
 where h.id=p_caso and h.concessionaria_id=p_loja for update of h,c;
 if not found then raise exception 'CASO_FORA_DA_LOJA' using errcode='22023';end if;
 if (v_status='vendido' and v_motivo is distinct from 'retorno_pos_venda')
 or (v_status='perdido' and v_motivo is distinct from 'revisao_humana') then
  raise exception 'CICLO_TERMINAL_SEM_NOVO_CASO' using errcode='23514';end if;
 select a.id,a.operador_id,a.atribuida_em into v_achado,v_origem,v_data
 from public.atribuicoes_humanas a
 where a.concessionaria_id=p_loja and a.caso_id=p_caso and a.encerrada_em is null
 for update of a;
 if v_achado is distinct from p_atribuicao_esperada then
  raise exception 'ATRIBUICAO_ESPERADA_DESATUALIZADA' using errcode='22023';end if;
 -- Revalidar revogacao concorrente de chefia e desativacao de equipe.
 if (select count(*) from prumo_private.s1_gestor_operadores g
     where g.gestor_id=p_gestor and g.operador_id in (v_origem,p_destino)
       and g.encerrado_em is null)<>2 then
  raise exception 'GESTOR_REVOGADO' using errcode='42501';end if;
 v_novo:=gen_random_uuid();
 -- Insere entitlement SEM grant global e somente para nova atribuicao.
 insert into prumo_private.s1_excecoes_55(
  concessionaria_id,caso_id,atribuicao_id,operador_id,gestor_id)
 values(p_loja,p_caso,v_novo,p_destino,p_gestor)
 returning id into v_excecao;
 update public.atribuicoes_humanas
 set encerrada_em=greatest(v_data,pg_catalog.statement_timestamp())
 where id=v_achado and encerrada_em is null;
 insert into public.atribuicoes_humanas(id,concessionaria_id,caso_id,operador_id)
 values(v_novo,p_loja,p_caso,p_destino);
 insert into prumo_private.s1_excecoes_eventos_55(excecao_id,tipo,ator_id)
 values(v_excecao,'CRIADA',p_gestor);
 insert into prumo_private.s1_movimentos_manuais_historico(
  solicitante_id,concessionaria_id,caso_id,atribuicao_anterior_id,
  atribuicao_nova_id,operador_anterior,operador_novo)
 values(p_gestor,p_loja,p_caso,v_achado,v_novo,v_origem,p_destino);
 return pg_catalog.jsonb_build_object(
  'outcome','MOVED_CASE_EXCEPTION','case_id',p_caso,
  'assignment_id',v_novo,'exception_id',v_excecao);
end $fn$;
create function prumo_private.s1_revogar_excecao_55(
 p_gestor uuid,p_excecao uuid)
returns jsonb language plpgsql security invoker set search_path='' as $fn$
declare v_reg record;
begin
 if current_user<>'postgres' then
  raise exception 'INTERNAL_ONLY' using errcode='42501';end if;
 select * into v_reg from prumo_private.s1_excecoes_55
 where id=p_excecao for update;
 if not found then raise exception 'EXCECAO_INEXISTENTE' using errcode='22023';end if;
 if p_gestor is distinct from v_reg.gestor_id
  or not exists(select 1 from prumo_private.s1_gestor_operadores g
   where g.gestor_id=p_gestor and g.operador_id=v_reg.operador_id
    and g.encerrado_em is null)
 then raise exception 'SEM_AUTORIDADE_REVOGACAO' using errcode='42501';end if;
 if v_reg.revogada_em is not null then
  return pg_catalog.jsonb_build_object('outcome','ALREADY_REVOKED');end if;
 update prumo_private.s1_excecoes_55
 set revogada_em=pg_catalog.statement_timestamp()
 where id=p_excecao;
 insert into prumo_private.s1_excecoes_eventos_55(excecao_id,tipo,ator_id)
 values(p_excecao,'REVOGADA',p_gestor);
 return pg_catalog.jsonb_build_object('outcome','REVOKED_CASE_ACCESS');
end $fn$;
revoke all on function
 prumo_private.s1_mover_excecao_caso_55(uuid,uuid,uuid,uuid,uuid),
 prumo_private.s1_revogar_excecao_55(uuid,uuid),
 prumo_private.s1_revogar_excecao_atribuicao_55()
 from public,anon,authenticated,service_role;

-- Projecao minima para que o excepcional veja o caso e somente os
-- campos de lead/ciclo indispensaveis, SEM grant SELECT em todas as lojas.
-- A view roda como owner no laboratorio e o predicado de per-case
-- exige JWT/conta/equipe/atribuicao/revogacao em toda consulta.
create view public.s1_55_resumo_caso with (security_barrier=true) as
select h.concessionaria_id,h.id as caso_id,h.ciclo_id,h.lead_id,
  l.telefone_cliente_normalizado,c.status_comercial
from public.casos_humanos h
join public.leads_loja l on l.concessionaria_id=h.concessionaria_id and l.id=h.lead_id
join public.ciclos_comerciais c on c.concessionaria_id=h.concessionaria_id and c.id=h.ciclo_id
where prumo_private.s1_caso_excepcional_autorizado_55(h.concessionaria_id,h.id);
revoke all on public.s1_55_resumo_caso from public,anon,service_role;
grant select on public.s1_55_resumo_caso to authenticated;
