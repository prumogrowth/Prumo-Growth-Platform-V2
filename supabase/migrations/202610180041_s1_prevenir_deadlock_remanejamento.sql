-- S1-002/I5 sintético: impede deadlock ao suspender dois destinatários
-- simultaneamente. Adiciona SKIP LOCKED na seleção de substituto:
-- profissional com estado/concessao em mudanca fica INELEGIVEL naquele
-- instante. Se nenhum outro substituto elegivel e desbloqueado, caso vai
-- para fila protegida. Nao forcar atribuição nem reabrir status comercial.
-- Não muda contrato público, privilégio, S0, Meta ou produção.
create or replace function prumo_private.s1_remanejar_ator(p_ator uuid,p_loja uuid,p_motivo text)
returns integer language plpgsql security invoker set search_path='' as $fn$
declare a record; v_destino uuid; n integer:=0;
begin
 if current_user<>'postgres' then raise exception 'INTERNAL_ONLY' using errcode='42501';end if;
 if p_ator is null or p_motivo not in ('EQUIPE_INATIVA','ESCOPO_REVOGADO')
 then raise exception 'INVALID_REASSIGN_INPUT' using errcode='22023';end if;
 for a in
  select x.id,x.atribuida_em,x.caso_id,x.concessionaria_id,c.status_comercial
  from public.atribuicoes_humanas x
  join public.casos_humanos h on h.id=x.caso_id and h.concessionaria_id=x.concessionaria_id
  join public.ciclos_comerciais c on c.id=h.ciclo_id and c.concessionaria_id=h.concessionaria_id
  where x.operador_id=p_ator and x.encerrada_em is null
   and (p_loja is null or x.concessionaria_id=p_loja)
  order by x.concessionaria_id,x.caso_id for update of x
 loop
  update public.atribuicoes_humanas set
   encerrada_em=greatest(a.atribuida_em,statement_timestamp())
   where id=a.id and encerrada_em is null;
  if a.status_comercial in ('vendido','perdido') then
   insert into prumo_private.s1_remanejamento_historico(
    concessionaria_id,caso_id,atribuicao_anterior_id,operador_anterior,motivo,resultado)
   values(a.concessionaria_id,a.caso_id,a.id,p_ator,p_motivo,'ENCERRADO_HISTORICO');
   n:=n+1;continue;
  end if;
  v_destino:=null;
  select v.ator_id into v_destino
  from public.vinculos_papel_escopo v
  join public.equipe_prumo_s1 e on e.ator_id=v.ator_id
  join public.concessionarias l on l.id=v.concessionaria_id
  where v.concessionaria_id=a.concessionaria_id and v.ator_id<>p_ator
   and v.papel='operador' and e.estado='ativo' and l.ativo
   and v.valido_desde<=statement_timestamp()
   and (v.valido_ate is null or v.valido_ate>statement_timestamp())
  order by (select count(*) from public.atribuicoes_humanas z
   where z.operador_id=v.ator_id and z.concessionaria_id=a.concessionaria_id
   and z.encerrada_em is null),v.ator_id
  limit 1 for share of e,v,l skip locked;
  if v_destino is null then
   insert into prumo_private.s1_remanejamento_pendencias(
    concessionaria_id,caso_id,operador_anterior,motivo)
   values(a.concessionaria_id,a.caso_id,p_ator,p_motivo)
   on conflict(concessionaria_id,caso_id) do update
   set operador_anterior=excluded.operador_anterior,motivo=excluded.motivo,
       registrado_em=statement_timestamp();
  else
   insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id)
   values(a.concessionaria_id,a.caso_id,v_destino);
   delete from prumo_private.s1_remanejamento_pendencias
   where concessionaria_id=a.concessionaria_id and caso_id=a.caso_id;
  end if;
  insert into prumo_private.s1_remanejamento_historico(
   concessionaria_id,caso_id,atribuicao_anterior_id,operador_anterior,
   operador_novo,resultado,motivo)
  values(a.concessionaria_id,a.caso_id,a.id,p_ator,v_destino,
   case when v_destino is null then 'FILA_PROTEGIDA' else 'REDISTRIBUIDO' end,p_motivo);
  n:=n+1;
 end loop;
 return n;
end $fn$;
