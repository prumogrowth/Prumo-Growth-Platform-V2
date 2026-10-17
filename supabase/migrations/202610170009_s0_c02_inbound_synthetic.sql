-- Prumo S0 / C02 parcial: ingesta interna de mensagens ficticias, SEM webhook Meta.
-- A identificacao da loja deriva EXCLUSIVAMENTE do canal de atendimento da Prumo.
-- Um telefone de cliente pode existir em concessionarias distintas.
-- C02 ainda nao conecta provedores nem executa cancelamento de recontatos.
alter table public.mensagens
 add column roteamento_simulado text
 check(roteamento_simulado in ('IA_PENDENTE','HUMANO_PENDENTE'));
alter table public.casos_humanos
 add column motivo_simulado text
 check(motivo_simulado in ('retorno_pos_venda','retorno_pos_remessa',
   'manter_humano','revisao_humana'));
create index conversas_escopo_retorno_idx
 on public.conversas(concessionaria_id,lead_id,canal_id,criada_em);
create index casos_humanos_motivo_simulado_idx
 on public.casos_humanos(concessionaria_id,ciclo_id,motivo_simulado,criado_em);

create function prumo_private.receber_mensagem_sintetica(
 p_canal uuid, p_telefone text, p_id_externo text, p_texto text
) returns jsonb
language plpgsql security invoker set search_path=''
as $$
declare
 v_loja uuid; v_lead uuid; v_ciclo uuid; v_versao bigint; v_status text;
 v_conversa uuid; v_caso uuid; v_msg uuid; v_novo boolean;
 v_tel_antigo text; v_texto_antigo text; v_rota text;
 v_motivo text; v_num_ciclos integer;
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
   'recontatos','CANCELAMENTO_PENDENTE');
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
  -- Nao escolher um ciclo arbitrario sem regra de reabertura aprovada.
  raise exception 'AMBIGUOUS_CYCLE_REQUIRES_HUMAN' using errcode='22023';
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
  'recontatos','CANCELAMENTO_PENDENTE');
end $$;

revoke all on function prumo_private.receber_mensagem_sintetica(uuid,text,text,text)
 from public,anon,authenticated,service_role;
-- No GRANT: supabase Data API never calls this function.
