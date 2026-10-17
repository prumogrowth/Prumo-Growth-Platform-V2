-- Auditoria C04 PB-11: inbound de cliente com opt-out nao religa IA por inferencia.
-- Atendimento espontaneo vira pendencia humana no ciclo existente (mock).
-- Sem retorno do opt-in, sem transporte externo e sem reversao comercial automatica.
create or replace function prumo_private.receber_mensagem_sintetica(
 p_canal uuid, p_telefone text, p_id_externo text, p_texto text
) returns jsonb
language plpgsql security invoker set search_path=''
as $$
declare
 v_loja uuid; v_lead uuid; v_ciclo uuid; v_versao bigint; v_status text;
 v_conversa uuid; v_caso uuid; v_msg uuid; v_novo boolean;
 v_tel_antigo text; v_texto_antigo text; v_rota text;
 v_motivo text; v_num_ciclos integer; v_cancel jsonb;
begin
 if current_user <> 'postgres' then
  raise exception 'INTERNAL_ONLY' using errcode='42501'; end if;
 if p_canal is null or p_telefone is null
    or p_telefone !~ '^\+[1-9][0-9]{9,14}$'
    or p_id_externo is null or p_id_externo !~ '^[A-Za-z0-9_.:-]{1,120}$'
    or p_texto is null or length(btrim(p_texto)) not between 1 and 1024
 then raise exception 'INVALID_INBOUND_SYNTHETIC' using errcode='22023'; end if;
 select ca.concessionaria_id into v_loja
 from public.canais_loja ca join public.concessionarias lo on lo.id=ca.concessionaria_id
 where ca.id=p_canal and ca.modo='simulado' and lo.ativo;
 if v_loja is null then raise exception 'UNKNOWN_CHANNEL' using errcode='22023'; end if;

 -- Mesmo ID de webhook => mesmo efeito, independentemente de quantas tentativas.
 perform pg_catalog.pg_advisory_xact_lock(
  pg_catalog.hashtextextended(p_canal::text||':'||p_id_externo,1702));
 select m.id, m.conversa_id, m.conteudo_sintetico, m.roteamento_simulado,
        l.telefone_cliente_normalizado
 into v_msg,v_conversa,v_texto_antigo,v_rota,v_tel_antigo
 from public.mensagens m
 join public.conversas co
   on co.id=m.conversa_id and co.concessionaria_id=m.concessionaria_id
 join public.leads_loja l
   on l.id=co.lead_id and l.concessionaria_id=co.concessionaria_id
 where m.concessionaria_id=v_loja and m.canal_id=p_canal
   and m.id_externo=p_id_externo and m.direcao='entrada';
 if found then
  if v_tel_antigo is distinct from p_telefone
     or v_texto_antigo is distinct from p_texto then
    raise exception 'CONFLICT_IDEMPOTENCY_KEY' using errcode='23505';
  end if;
  return pg_catalog.jsonb_build_object(
   'outcome','ALREADY_APPLIED','mensagem_id',v_msg,
   'conversa_id',v_conversa,'roteamento',v_rota,
   'recontatos','JA_PROCESSADO');
 end if;

 -- Chave comercial: concessionaria + telefone, jamais telefone global.
 insert into public.leads_loja(concessionaria_id,telefone_cliente_normalizado)
 values(v_loja,p_telefone)
 on conflict(concessionaria_id,telefone_cliente_normalizado) do nothing
 returning id into v_lead;
 v_novo:=(v_lead is not null);
 if not v_novo then
  select id into v_lead from public.leads_loja
   where concessionaria_id=v_loja and telefone_cliente_normalizado=p_telefone;
 end if;
 if v_lead is null then raise exception 'RETRY_LEAD' using errcode='40001'; end if;
 -- Serialize conversas para eventos distintos do MESMO cliente na MESMA loja.
 perform 1 from public.leads_loja
   where concessionaria_id=v_loja and id=v_lead for update;
 -- Atomic with inbound: no scheduled/reserved follow-up remains eligible.
 -- Cancellation is limited to this lead in this shop, never another shop.
 v_cancel:=prumo_private.cancelar_recontatos_sinteticos(
    v_loja,v_lead,'resposta_cliente');
 select count(*) into v_num_ciclos
 from public.ciclos_comerciais where concessionaria_id=v_loja and lead_id=v_lead;
 if v_num_ciclos=0 then
  insert into public.ciclos_comerciais(concessionaria_id,lead_id)
  values(v_loja,v_lead) returning id,status_comercial,versao_registro
   into v_ciclo,v_status,v_versao;
 elsif v_num_ciclos=1 then
  select id,status_comercial,versao_registro
   into v_ciclo,v_status,v_versao
   from public.ciclos_comerciais
   where concessionaria_id=v_loja and lead_id=v_lead for update;
 else
  -- Preservar mensagem valida em quarentena escopada, sem associar ciclo
  -- arbitrario, abrir caso falso ou provocar resposta da IA.
  select id into v_conversa from public.conversas
   where concessionaria_id=v_loja and lead_id=v_lead and canal_id=p_canal
     and caso_id is null
   order by criada_em desc,id desc limit 1;
  if v_conversa is null then
   insert into public.conversas(concessionaria_id,lead_id,canal_id)
   values(v_loja,v_lead,p_canal) returning id into v_conversa;
  end if;
  insert into public.mensagens(
     concessionaria_id,conversa_id,canal_id,caso_id,
     direcao,origem,conteudo_sintetico,id_externo,roteamento_simulado)
  values(v_loja,v_conversa,p_canal,null,
     'entrada','simulado',p_texto,p_id_externo,'HUMANO_PENDENTE')
  returning id into v_msg;
  insert into public.pendencias_inbound_simulado(
     concessionaria_id,canal_id,lead_id,mensagem_id,motivo)
  values(v_loja,p_canal,v_lead,v_msg,'MULTIPLOS_CICLOS');
  return pg_catalog.jsonb_build_object(
     'outcome','APPLIED','mensagem_id',v_msg,'conversa_id',v_conversa,
     'ciclo_id',null,'caso_id',null,
     'roteamento','HUMANO_PENDENTE','revisao','MULTIPLOS_CICLOS',
     'recontatos',v_cancel);
 end if;

 v_caso:=null;
 if v_status in ('cadastro enviado ao banco','vendido') then
  v_motivo:=case when v_status='vendido' then 'retorno_pos_venda'
       else 'retorno_pos_remessa' end;
  select id into v_caso from public.casos_humanos
   where concessionaria_id=v_loja and ciclo_id=v_ciclo
    and motivo_simulado=v_motivo
   order by criado_em desc,id desc limit 1;
  if v_caso is null then
   insert into public.casos_humanos(
      concessionaria_id,lead_id,ciclo_id,motivo_simulado)
   values(v_loja,v_lead,v_ciclo,v_motivo) returning id into v_caso;
  end if;
 elsif v_status in ('em atendimento pelo operador','cadastro enviado ao operador','perdido')
   or exists(select 1 from public.casos_humanos
      where concessionaria_id=v_loja and ciclo_id=v_ciclo)
 then
  select id into v_caso from public.casos_humanos
    where concessionaria_id=v_loja and ciclo_id=v_ciclo
    order by criado_em desc,id desc limit 1;
  if v_caso is null then
   insert into public.casos_humanos(
     concessionaria_id,lead_id,ciclo_id,motivo_simulado)
   values(v_loja,v_lead,v_ciclo,
       case when v_status='perdido' then 'revisao_humana'
            else 'manter_humano' end)
   returning id into v_caso;
  end if;
 end if;

 -- PB-11: inbound espontaneo apos opt-out NAO e reopt-in nem
 -- permissao para reativar IA. Encaminhar caso a revisao humana.
 if v_caso is null and exists(
    select 1 from public.supressoes_contato_sinteticas sp
    where sp.concessionaria_id=v_loja and sp.lead_id=v_lead
      and sp.canal_id=p_canal
      and sp.finalidade='recontato_comercial_sintetico'
 ) then
   insert into public.casos_humanos(
     concessionaria_id,lead_id,ciclo_id,motivo_simulado)
   values(v_loja,v_lead,v_ciclo,'revisao_humana')
   returning id into v_caso;
 end if;
 v_rota:=case when v_caso is null then 'IA_PENDENTE' else 'HUMANO_PENDENTE' end;
 select id into v_conversa from public.conversas
  where concessionaria_id=v_loja and lead_id=v_lead and canal_id=p_canal
    and caso_id is not distinct from v_caso
  order by criada_em desc,id desc limit 1;
 if v_conversa is null then
  insert into public.conversas(concessionaria_id,lead_id,canal_id,caso_id)
  values(v_loja,v_lead,p_canal,v_caso) returning id into v_conversa;
 end if;
 insert into public.mensagens(concessionaria_id,conversa_id,canal_id,caso_id,
    direcao,origem,conteudo_sintetico,id_externo,roteamento_simulado)
 values(v_loja,v_conversa,p_canal,v_caso,
    'entrada','simulado',p_texto,p_id_externo,v_rota)
 returning id into v_msg;

 -- Prova de inbound e evento de transicao comercial no mesmo commit apenas
 -- quando ainda NAO houve handoff humano. Nao significa resposta da IA.
 if v_rota='IA_PENDENTE'
  and v_status in ('aguardando primeiro disparo','primeiro disparo enviado') then
  perform prumo_private.transicao_inbound_sintetico(v_loja,v_ciclo,v_msg,v_versao);
 end if;
 return pg_catalog.jsonb_build_object(
  'outcome','APPLIED','mensagem_id',v_msg,'conversa_id',v_conversa,
  'ciclo_id',v_ciclo,'caso_id',v_caso,'roteamento',v_rota,
  'recontatos',v_cancel);
end $$;
revoke all on function prumo_private.receber_mensagem_sintetica(uuid,text,text,text)
 from public,anon,authenticated,service_role;
