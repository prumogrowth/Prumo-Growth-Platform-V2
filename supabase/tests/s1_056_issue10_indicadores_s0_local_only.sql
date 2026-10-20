-- S0 / issue10 / I36: UNICO indicador visual - somento fixture PG17.
-- Leitura de operador e visita de supervisor sao estados separados.
-- Numerador: entrada SEM marcador de leitura da atribuicao corrente.
-- Quando zero e entrada lida ainda sem saida humana POSTERIOR: bolinha.
create table prumo_private.s0_ordem_mensagem_56(
 mensagem_id uuid primary key,
 concessionaria_id uuid not null,
 conversa_id uuid not null,
 caso_id uuid,
 ordem bigint not null check(ordem>0),
 unique(concessionaria_id,conversa_id,ordem),
 foreign key(concessionaria_id,mensagem_id)
  references public.mensagens(concessionaria_id,id)
);
create table prumo_private.s0_leituras_operador_56(
 atribuicao_id uuid not null references public.atribuicoes_humanas(id),
 mensagem_id uuid not null references public.mensagens(id),
 operador_id uuid not null references public.atores(id),
 lida_em timestamptz not null default pg_catalog.statement_timestamp(),
 primary key(atribuicao_id,mensagem_id)
);
create table prumo_private.s0_visitas_supervisor_56(
 id bigint generated always as identity primary key,
 gestor_id uuid not null references public.atores(id),
 concessionaria_id uuid not null,
 caso_id uuid not null,
 conversa_id uuid not null,
 atribuicao_id uuid not null references public.atribuicoes_humanas(id),
 visto_em timestamptz not null default pg_catalog.statement_timestamp(),
 foreign key(concessionaria_id,caso_id)
  references public.casos_humanos(concessionaria_id,id)
);
alter table prumo_private.s0_ordem_mensagem_56 enable row level security;
alter table prumo_private.s0_leituras_operador_56 enable row level security;
alter table prumo_private.s0_visitas_supervisor_56 enable row level security;
revoke all on prumo_private.s0_ordem_mensagem_56,
 prumo_private.s0_leituras_operador_56,prumo_private.s0_visitas_supervisor_56
 from public,anon,authenticated,service_role;
revoke all on sequence prumo_private.s0_visitas_supervisor_56_id_seq
 from public,anon,authenticated,service_role;
create trigger s0_56_read_immutable before update or delete on
 prumo_private.s0_leituras_operador_56 for each row
 execute function prumo_private.s1_proibir_alteracao_historico();
create trigger s0_56_visita_immutable before update or delete on
 prumo_private.s0_visitas_supervisor_56 for each row
 execute function prumo_private.s1_proibir_alteracao_historico();

-- Ordenacao tecnica total POR CONVERSA, serializada por lock da conversa.
-- Quando eventuais mensagens forem enviadas via Meta, isso exigira outro
-- contrato de order/idempotency/confirmacao, NAO reusar cegamente.
create function prumo_private.s0_anotar_ordem_mensagem_56()
returns trigger language plpgsql security definer set search_path='' as $fn$
declare v_ultima bigint;
begin
 perform 1 from public.conversas c
 where c.id=new.conversa_id and c.concessionaria_id=new.concessionaria_id
 for update of c;
 if not found then raise exception 'CONVERSA_INVALIDA' using errcode='23503';end if;
 select pg_catalog.coalesce(pg_catalog.max(o.ordem),0)
 into v_ultima
 from prumo_private.s0_ordem_mensagem_56 o
 where o.concessionaria_id=new.concessionaria_id and o.conversa_id=new.conversa_id;
 insert into prumo_private.s0_ordem_mensagem_56(
  mensagem_id,concessionaria_id,conversa_id,caso_id,ordem)
 values(new.id,new.concessionaria_id,new.conversa_id,new.caso_id,v_ultima+1);
 return new;
end $fn$;
create trigger s0_56_ordem_after_insert
 after insert on public.mensagens for each row
 execute function prumo_private.s0_anotar_ordem_mensagem_56();

create function prumo_private.s0_marcar_leitura_operador_fixture_56(
 p_loja uuid,p_caso uuid,p_conversa uuid,p_operador uuid,p_ultima_entrada uuid)
returns jsonb language plpgsql security invoker set search_path='' as $fn$
declare v_atr uuid;v_ordem bigint;v_inseridas integer;
begin
 if current_user<>'postgres' then
  raise exception 'LEITURA_INTERNA_APENAS' using errcode='42501';end if;
 -- Trava caso para concorrer com reatribuicao.
 perform 1 from public.casos_humanos h where h.concessionaria_id=p_loja and h.id=p_caso
 for share of h;
 select a.id into v_atr from public.atribuicoes_humanas a
 where a.concessionaria_id=p_loja and a.caso_id=p_caso
  and a.operador_id=p_operador and a.encerrada_em is null
 for share of a;
 if v_atr is null then raise exception 'OPERADOR_NAO_TITULAR' using errcode='42501';end if;
 select o.ordem into v_ordem from prumo_private.s0_ordem_mensagem_56 o
 join public.mensagens m on m.id=o.mensagem_id
 where o.concessionaria_id=p_loja and o.conversa_id=p_conversa
  and o.caso_id=p_caso and o.mensagem_id=p_ultima_entrada
  and m.direcao='entrada';
 if v_ordem is null then raise exception 'MENSAGEM_INBOUND_INVALIDA' using errcode='22023';end if;
 insert into prumo_private.s0_leituras_operador_56(atribuicao_id,mensagem_id,operador_id)
 select v_atr,o.mensagem_id,p_operador from prumo_private.s0_ordem_mensagem_56 o
 join public.mensagens m on m.id=o.mensagem_id
 where o.concessionaria_id=p_loja and o.conversa_id=p_conversa
  and o.caso_id=p_caso and o.ordem<=v_ordem and m.direcao='entrada'
 on conflict(atribuicao_id,mensagem_id) do nothing;
 get diagnostics v_inseridas=row_count;
 return pg_catalog.jsonb_build_object('outcome','READ_RECORDED','read_added',v_inseridas,
   'assignment_id',v_atr);
end $fn$;

create function prumo_private.s0_visita_supervisor_fixture_56(
 p_loja uuid,p_caso uuid,p_conversa uuid,p_gestor uuid)
returns jsonb language plpgsql security invoker set search_path='' as $fn$
declare v_atr uuid;
begin
 if current_user<>'postgres' then
  raise exception 'SUPERVISAO_INTERNA_APENAS' using errcode='42501';end if;
 select a.id into v_atr
 from public.atribuicoes_humanas a
 join public.conversas c
 on c.concessionaria_id=a.concessionaria_id and c.caso_id=a.caso_id
 join prumo_private.s1_gestor_operadores g
 on g.gestor_id=p_gestor and g.operador_id=a.operador_id
  and g.encerrado_em is null
 where a.concessionaria_id=p_loja and a.caso_id=p_caso
   and a.encerrada_em is null and c.id=p_conversa;
 if v_atr is null then raise exception 'GESTOR_SEM_CASO' using errcode='42501';end if;
 insert into prumo_private.s0_visitas_supervisor_56(
  gestor_id,concessionaria_id,caso_id,conversa_id,atribuicao_id)
 values(p_gestor,p_loja,p_caso,p_conversa,v_atr);
 return pg_catalog.jsonb_build_object('outcome','SUPERVISOR_VIEWED');
end $fn$;

create function prumo_private.s0_indicador_operador_fixture_56(
 p_loja uuid,p_caso uuid,p_conversa uuid,p_operador uuid)
returns jsonb language plpgsql security invoker set search_path='' as $fn$
declare v_atr uuid;v_unread integer;v_pendente boolean;
begin
 if current_user<>'postgres' then
  raise exception 'PROJECAO_INTERNA_APENAS' using errcode='42501';end if;
 select a.id into v_atr from public.atribuicoes_humanas a
 join public.conversas c on c.concessionaria_id=a.concessionaria_id
  and c.caso_id=a.caso_id
 where a.concessionaria_id=p_loja and a.caso_id=p_caso
  and a.operador_id=p_operador and a.encerrada_em is null
  and c.id=p_conversa;
 if v_atr is null then raise exception 'OPERADOR_NAO_TITULAR' using errcode='42501';end if;
 select pg_catalog.count(*) into v_unread
 from prumo_private.s0_ordem_mensagem_56 o
 join public.mensagens m on m.id=o.mensagem_id
 where o.concessionaria_id=p_loja and o.conversa_id=p_conversa
  and o.caso_id=p_caso and m.direcao='entrada'
  and not exists(select 1 from prumo_private.s0_leituras_operador_56 le
   where le.atribuicao_id=v_atr and le.mensagem_id=o.mensagem_id);
 select exists(
 select 1 from prumo_private.s0_leituras_operador_56 le
 join prumo_private.s0_ordem_mensagem_56 inbound on inbound.mensagem_id=le.mensagem_id
 where le.atribuicao_id=v_atr
   and inbound.concessionaria_id=p_loja and inbound.conversa_id=p_conversa
   and inbound.caso_id=p_caso
   and not exists (
     select 1 from prumo_private.s0_ordem_mensagem_56 outbound
     join public.mensagens m on m.id=outbound.mensagem_id
     where outbound.concessionaria_id=p_loja and outbound.conversa_id=p_conversa
       and outbound.caso_id=p_caso and outbound.ordem>inbound.ordem
       and m.direcao='saida' and m.enviada_por=p_operador)
 ) into v_pendente;
 return pg_catalog.jsonb_build_object(
  'state',case when v_unread>0 then 'COUNT'
    when v_pendente then 'DOT' else 'NONE' end,
  'unread_count',v_unread,
  'requires_operator_reply',coalesce(v_pendente,false),
  'assignment_id',v_atr);
end $fn$;
revoke all on function
 prumo_private.s0_anotar_ordem_mensagem_56(),
 prumo_private.s0_marcar_leitura_operador_fixture_56(uuid,uuid,uuid,uuid,uuid),
 prumo_private.s0_visita_supervisor_fixture_56(uuid,uuid,uuid,uuid),
 prumo_private.s0_indicador_operador_fixture_56(uuid,uuid,uuid,uuid)
 from public,anon,authenticated,service_role;
