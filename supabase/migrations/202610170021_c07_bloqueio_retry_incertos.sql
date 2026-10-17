-- C07 fail-closed: failed or uncertain callbacks cannot become blind retries.
-- Even after a review is closed WITHOUT real proof, no further reservation.
-- Future provider recovery requires explicit DEC-13/14/15 and redesign.
create or replace function prumo_private.agendar_recontatos_sinteticos(
 p_ator uuid,p_loja uuid,p_ciclo uuid,p_canal uuid,p_chave text,p_tentativas jsonb
) returns jsonb language plpgsql security invoker set search_path=''
as $guard$
declare v_lead uuid; v_status text; v_plano uuid; v_hash text; v_prev text;
 v_ordem int:=0; v_tentativa jsonb; v_template uuid; v_hora timestamptz; v_prev_hora timestamptz; v_plano_estado text;
begin
 if current_user<>'postgres' then raise exception 'INTERNAL_ONLY' using errcode='42501'; end if;
 if p_chave is null or length(btrim(p_chave)) not between 1 and 160
 or jsonb_typeof(p_tentativas) is distinct from 'array'
 or jsonb_array_length(p_tentativas) not between 1 and 5
 then raise exception 'INVALID_PLAN' using errcode='22023'; end if;
 if not exists(select 1 from public.vinculos_papel_escopo v
  where v.ator_id=p_ator and v.concessionaria_id=p_loja and v.papel='gestor'
  and v.valido_desde<=statement_timestamp()
  and (v.valido_ate is null or v.valido_ate>statement_timestamp()))
 then raise exception 'FORBIDDEN_SCOPE' using errcode='42501'; end if;
 select c.lead_id into v_lead from public.ciclos_comerciais c
  where c.id=p_ciclo and c.concessionaria_id=p_loja;
 if v_lead is null then raise exception 'UNKNOWN_CYCLE_SCOPE' using errcode='42501'; end if;
 perform 1 from public.leads_loja
  where concessionaria_id=p_loja and id=v_lead for update;
 v_hash:=encode(sha256(convert_to(jsonb_build_object('ciclo_id',p_ciclo,'canal_id',p_canal,'tentativas',p_tentativas)::text,'UTF8')),'hex');
 select id,fingerprint,estado into v_plano,v_prev,v_plano_estado from public.planos_recontato_sinteticos
  where concessionaria_id=p_loja and chave_idempotencia=p_chave;
 if found then
  if v_prev is distinct from v_hash then
   raise exception 'CONFLICT_IDEMPOTENCY_KEY' using errcode='23505'; end if;
  return jsonb_build_object('outcome','ALREADY_APPLIED','plano_id',v_plano,
   'estado_plano',v_plano_estado,'executavel_simulacao',v_plano_estado='ativo',
   'transmissao_externa','DESABILITADA'); end if;
 select status_comercial into v_status from public.ciclos_comerciais
  where concessionaria_id=p_loja and id=p_ciclo for update;
 if not exists(
  select 1 from public.evidencias_elegibilidade_sinteticas ev
  where ev.concessionaria_id=p_loja and ev.lead_id=v_lead
    and ev.canal_id=p_canal and ev.finalidade='recontato_comercial_sintetico'
    and ev.estado='verificada_simulada'
 ) or exists(
  select 1 from public.supressoes_contato_sinteticas sp
  where sp.concessionaria_id=p_loja and sp.lead_id=v_lead
    and sp.canal_id=p_canal and sp.finalidade='recontato_comercial_sintetico'
 )
 then raise exception 'ELIGIBILITY_NOT_DEMONSTRATED' using errcode='22023'; end if;
 if exists(
  select 1 from public.planos_recontato_sinteticos p
  join public.envios_template_sinteticos e
   on e.concessionaria_id=p.concessionaria_id and e.plano_id=p.id
  join public.eventos_callback_sinteticos cb
   on cb.concessionaria_id=e.concessionaria_id
   and cb.estado_reportado in ('FALHOU_SIMULADO','INCERTO_SIMULADO')
   and (cb.envio_id=e.id or exists(
    select 1 from public.associacoes_callback_c07_sinteticas a
    where a.concessionaria_id=cb.concessionaria_id
     and a.evento_id=cb.id and a.envio_id=e.id))
  where p.concessionaria_id=p_loja and p.ciclo_id=p_ciclo
 ) then raise exception 'C07_REVIEW_REQUIRED_NO_AUTOMATIC_RETRY'
 using errcode='22023';end if;
 if v_status not in ('aguardando primeiro disparo','primeiro disparo enviado','em atendimento pela IA')
  or exists(select 1 from public.casos_humanos h where h.concessionaria_id=p_loja and h.ciclo_id=p_ciclo)
  or exists(select 1 from public.planos_recontato_sinteticos p
    where p.concessionaria_id=p_loja and p.ciclo_id=p_ciclo and p.estado='ativo')
  or not exists(select 1 from public.canais_loja ch
    where ch.concessionaria_id=p_loja and ch.id=p_canal and ch.modo='simulado')
 then raise exception 'NOT_ELIGIBLE_SIMULATION' using errcode='22023'; end if;
 -- Synthetic-only: no real consent, Meta approval, timezone or opt-out proof asserted.
 insert into public.planos_recontato_sinteticos(
 concessionaria_id,lead_id,ciclo_id,canal_id,chave_idempotencia,fingerprint)
 values(p_loja,v_lead,p_ciclo,p_canal,p_chave,v_hash) returning id into v_plano;
 for v_tentativa in select value from jsonb_array_elements(p_tentativas) loop
  v_ordem:=v_ordem+1;
  if jsonb_typeof(v_tentativa) is distinct from 'object'
     or jsonb_typeof(v_tentativa->'template_id') is distinct from 'string'
     or jsonb_typeof(v_tentativa->'agendado_em') is distinct from 'string'
  then raise exception 'INVALID_PLAN_ITEM' using errcode='22023'; end if;
  begin
   v_template:=(v_tentativa->>'template_id')::uuid;
   v_hora:=(v_tentativa->>'agendado_em')::timestamptz;
  exception when others then raise exception 'INVALID_PLAN_ITEM' using errcode='22023'; end;
  if v_hora <= statement_timestamp() or (v_prev_hora is not null and v_hora <= v_prev_hora) or not exists(
   select 1 from public.catalogo_templates_sinteticos t
   where t.id=v_template and t.concessionaria_id=p_loja and t.aprovado_simulacao)
  then raise exception 'UNAPPROVED_OR_PAST_TEMPLATE' using errcode='22023'; end if;
  insert into public.envios_template_sinteticos(
    concessionaria_id,plano_id,template_id,ordem,agendado_em,chave_idempotencia)
  values(p_loja,v_plano,v_template,v_ordem,v_hora,p_chave||':'||v_ordem);
  v_prev_hora:=v_hora;
 end loop;
 return jsonb_build_object('outcome','APPLIED','plano_id',v_plano,'envios',v_ordem,
   'estado_plano','ativo','executavel_simulacao',true,
   'transmissao_externa','DESABILITADA');
end $guard$;
create or replace function prumo_private.reservar_envio_sintetico(
 p_loja uuid,p_envio uuid,p_referencia timestamptz
) returns jsonb language plpgsql security invoker set search_path=''
as $guard$
declare v_lead uuid; v_plan uuid; v_state text; v_status text; v_hora timestamptz;
begin
 if current_user<>'postgres' then raise exception 'INTERNAL_ONLY' using errcode='42501'; end if;
 select p.lead_id,p.id into v_lead,v_plan
 from public.envios_template_sinteticos e join public.planos_recontato_sinteticos p
 on p.id=e.plano_id and p.concessionaria_id=e.concessionaria_id
 where e.concessionaria_id=p_loja and e.id=p_envio;
 if v_lead is null then raise exception 'UNKNOWN_SEND_SCOPE' using errcode='42501'; end if;
 perform 1 from public.leads_loja
 where concessionaria_id=p_loja and id=v_lead for update;
 perform 1 from public.planos_recontato_sinteticos
 where concessionaria_id=p_loja and id=v_plan for update;
 select e.estado,e.agendado_em,c.status_comercial into v_state,v_hora,v_status
 from public.envios_template_sinteticos e
 join public.planos_recontato_sinteticos p on p.id=e.plano_id and p.concessionaria_id=e.concessionaria_id
 join public.ciclos_comerciais c on c.id=p.ciclo_id and c.concessionaria_id=p.concessionaria_id
 where e.concessionaria_id=p_loja and e.id=p_envio
 and p.estado='ativo' for update of e;
 if not exists(
  select 1 from public.planos_recontato_sinteticos p
  join public.evidencias_elegibilidade_sinteticas ev
    on ev.concessionaria_id=p.concessionaria_id
   and ev.lead_id=p.lead_id and ev.canal_id=p.canal_id and ev.finalidade=p.finalidade
  where p.id=v_plan and p.concessionaria_id=p_loja
    and ev.estado='verificada_simulada'
 ) or exists(
  select 1 from public.planos_recontato_sinteticos p
  join public.supressoes_contato_sinteticas sp
    on sp.concessionaria_id=p.concessionaria_id
   and sp.lead_id=p.lead_id and sp.canal_id=p.canal_id and sp.finalidade=p.finalidade
  where p.id=v_plan and p.concessionaria_id=p_loja
 ) then return jsonb_build_object('outcome','NOT_ELIGIBLE','reason','C04_BLOCKED',
   'transmissao_externa','DESABILITADA'); end if;
 if exists(
  select 1 from public.envios_template_sinteticos e
  join public.eventos_callback_sinteticos cb
   on cb.concessionaria_id=e.concessionaria_id
   and cb.estado_reportado in ('FALHOU_SIMULADO','INCERTO_SIMULADO')
   and (cb.envio_id=e.id or exists(
    select 1 from public.associacoes_callback_c07_sinteticas a
    where a.concessionaria_id=cb.concessionaria_id
      and a.evento_id=cb.id and a.envio_id=e.id))
  where e.concessionaria_id=p_loja and e.plano_id=v_plan
 ) then return jsonb_build_object('outcome','NOT_ELIGIBLE',
    'reason','C07_REVIEW_REQUIRED_NO_AUTOMATIC_RETRY',
    'transmissao_externa','DESABILITADA');end if;
 if not found or v_state<>'programado'
 or v_hora>p_referencia or v_status not in
 ('aguardando primeiro disparo','primeiro disparo enviado','em atendimento pela IA')
 or exists(select 1 from public.casos_humanos h
    join public.planos_recontato_sinteticos p on p.ciclo_id=h.ciclo_id
    and p.concessionaria_id=h.concessionaria_id
    where p.concessionaria_id=p_loja and p.id=v_plan)
 or not exists (select 1 from public.envios_template_sinteticos e
    join public.catalogo_templates_sinteticos t
      on t.id=e.template_id and t.concessionaria_id=e.concessionaria_id
    join public.planos_recontato_sinteticos p
      on p.id=e.plano_id and p.concessionaria_id=e.concessionaria_id
    join public.canais_loja ch
      on ch.id=p.canal_id and ch.concessionaria_id=p.concessionaria_id
    where e.concessionaria_id=p_loja and e.id=p_envio
      and t.aprovado_simulacao and ch.modo='simulado')
 then return jsonb_build_object('outcome','NOT_ELIGIBLE','transmissao_externa','DESABILITADA'); end if;
 update public.envios_template_sinteticos
 set estado='reservado',reservado_em=statement_timestamp()
 where concessionaria_id=p_loja and id=p_envio;
 insert into public.eventos_envio_template_sinteticos(
 concessionaria_id,envio_id,estado_anterior,estado_posterior,motivo)
 values(p_loja,p_envio,'programado','reservado','ensaio_reserva');
 return jsonb_build_object('outcome','RESERVED_SIMULATED','transmissao_externa','DESABILITADA');
end $guard$;
create or replace function prumo_private.diagnosticar_falhas_c07_sintetico(
 p_loja uuid,p_ciclo uuid
) returns jsonb language plpgsql security invoker set search_path='' as $fn$
declare v_falhas bigint;v_incerto bigint;v_ambiguas bigint;
begin
 if current_user<>'postgres' then raise exception 'INTERNAL_ONLY' using errcode='42501';end if;
 if not exists(select 1 from public.ciclos_comerciais c
   where c.concessionaria_id=p_loja and c.id=p_ciclo)
 then raise exception 'FORBIDDEN_SCOPE' using errcode='42501';end if;
 select count(distinct e.id) filter(where cb.estado_reportado='FALHOU_SIMULADO'),
   count(distinct e.id) filter(where cb.estado_reportado='INCERTO_SIMULADO')
 into v_falhas,v_incerto
 from public.planos_recontato_sinteticos p
 join public.envios_template_sinteticos e
  on e.concessionaria_id=p.concessionaria_id and e.plano_id=p.id
 join public.eventos_callback_sinteticos cb
  on cb.concessionaria_id=e.concessionaria_id
  and (cb.envio_id=e.id or exists(
   select 1 from public.associacoes_callback_c07_sinteticas a
   where a.concessionaria_id=cb.concessionaria_id
    and a.evento_id=cb.id and a.envio_id=e.id))
 where p.concessionaria_id=p_loja and p.ciclo_id=p_ciclo;
 select count(*) into v_ambiguas from public.pendencias_reconciliacao_c07_sinteticas pr
 join public.eventos_callback_sinteticos cb
  on cb.concessionaria_id=pr.concessionaria_id and cb.id=pr.evento_id
 join public.envios_template_sinteticos e
  on e.concessionaria_id=cb.concessionaria_id and e.id=cb.envio_id
 join public.planos_recontato_sinteticos p
  on p.concessionaria_id=e.concessionaria_id and p.id=e.plano_id
 where p.concessionaria_id=p_loja and p.ciclo_id=p_ciclo
  and pr.estado='pendente';
 return jsonb_build_object('falhas_reportadas_tentativas_distintas',v_falhas,
  'tentativas_com_incerteza',v_incerto,'pendencias_em_aberto',v_ambiguas,
  'falhas_qualificadas','NAO_AVALIADAS_DEC_15',
  'acao','SOMENTE_DIAGNOSTICO','reenvio_automatico','PROIBIDO');
end $fn$;
revoke all on function prumo_private.agendar_recontatos_sinteticos(uuid,uuid,uuid,uuid,text,jsonb)
 from public,anon,authenticated,service_role;
revoke all on function prumo_private.reservar_envio_sintetico(uuid,uuid,timestamptz)
 from public,anon,authenticated,service_role;
revoke all on function prumo_private.diagnosticar_falhas_c07_sintetico(uuid,uuid)
 from public,anon,authenticated,service_role;
