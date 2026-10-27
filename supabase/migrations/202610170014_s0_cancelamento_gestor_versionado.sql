-- C08 simulated explicit manager cancellation with authorization and expected_version.
-- Does not send/undo real WhatsApp messages. Cancels only the selected plan.
create function prumo_private.cancelar_plano_gestor_sintetico(
 p_ator uuid,p_loja uuid,p_plano uuid,p_versao bigint
) returns jsonb language plpgsql security invoker set search_path=''
as $$
declare v_lead uuid; v_p record; v_env record; v_count int:=0;
begin
 if current_user<>'postgres' then raise exception 'INTERNAL_ONLY' using errcode='42501'; end if;
 if not exists(select 1 from public.vinculos_papel_escopo v
 where v.ator_id=p_ator and v.concessionaria_id=p_loja and v.papel='gestor'
 and v.valido_desde<=statement_timestamp()
 and (v.valido_ate is null or v.valido_ate>statement_timestamp()))
 then raise exception 'FORBIDDEN_SCOPE' using errcode='42501'; end if;
 select lead_id into v_lead from public.planos_recontato_sinteticos
 where concessionaria_id=p_loja and id=p_plano;
 if v_lead is null then raise exception 'FORBIDDEN_SCOPE' using errcode='42501'; end if;
 perform 1 from public.leads_loja
 where concessionaria_id=p_loja and id=v_lead for update;
 select id,estado,versao,motivo_cancelamento into v_p
 from public.planos_recontato_sinteticos
 where concessionaria_id=p_loja and id=p_plano for update;
 if v_p.estado='cancelado' then
  if v_p.motivo_cancelamento='cancelamento_gestor' and p_versao=v_p.versao-1
  then return jsonb_build_object('outcome','ALREADY_APPLIED','plano_id',p_plano); end if;
  raise exception 'CONFLICT_VERSION' using errcode='40001';
 end if;
 if p_versao is distinct from v_p.versao then
  raise exception 'CONFLICT_VERSION' using errcode='40001'; end if;
 for v_env in select id,estado from public.envios_template_sinteticos
  where concessionaria_id=p_loja and plano_id=p_plano
    and estado in ('programado','reservado') order by id for update
 loop
  update public.envios_template_sinteticos set
  estado='cancelado',cancelado_em=statement_timestamp()
  where concessionaria_id=p_loja and id=v_env.id;
  insert into public.eventos_envio_template_sinteticos(
    concessionaria_id,envio_id,estado_anterior,estado_posterior,motivo)
  values(p_loja,v_env.id,v_env.estado,'cancelado','cancelamento_gestor');
  v_count:=v_count+1;
 end loop;
 update public.planos_recontato_sinteticos set
 estado='cancelado',versao=versao+1,motivo_cancelamento='cancelamento_gestor',
 cancelado_em=statement_timestamp()
 where concessionaria_id=p_loja and id=p_plano;
 return jsonb_build_object('outcome','APPLIED','plano_id',p_plano,
   'envios_cancelados',v_count,'nova_versao',p_versao+1,
   'transmissao_externa','DESABILITADA');
end $$;
revoke all on function prumo_private.cancelar_plano_gestor_sintetico(uuid,uuid,uuid,bigint)
 from public,anon,authenticated,service_role;
