-- S0 simulated transaction services, private namespace; never expose to PostgREST.
-- Based on normative 13A and proposals 25/26(C01,C02)/38/39.
create schema if not exists prumo_private;
revoke all on schema prumo_private from public, anon, authenticated, service_role;

alter table public.lotes_importacao add column payload_fingerprint text;
alter table public.itens_lote alter column lead_id drop not null;
alter table public.itens_lote
 add column resultado text not null default 'aceito' check(resultado in ('aceito','rejeitado')),
 add column motivo_rejeicao text,
 add constraint item_resultado_check check(
   (resultado='aceito' and lead_id is not null and motivo_rejeicao is null)
   or (resultado='rejeitado' and lead_id is null and motivo_rejeicao is not null)
 );
alter table public.mensagens add constraint mensagens_loja_id_unique unique(concessionaria_id,id);
alter table public.eventos_status_comercial
 add column mensagem_simulada_id uuid,
 add constraint evento_mensagem_loja_fk foreign key(concessionaria_id,mensagem_simulada_id)
 references public.mensagens(concessionaria_id,id) on delete restrict;
create unique index evento_mensagem_unica on public.eventos_status_comercial(concessionaria_id,mensagem_simulada_id)
 where mensagem_simulada_id is not null;

create function prumo_private.importar_lote_sintetico(
 p_ator uuid, p_loja uuid, p_chave text, p_linhas jsonb
) returns jsonb
language plpgsql security invoker set search_path=''
as $$
declare
 v_hash text; v_id uuid; v_anterior text; v_row jsonb; v_tel text; v_lead uuid;
 v_n integer:=0; v_ok integer:=0; v_bad integer:=0; v_novo boolean;
begin
 if current_user <> 'postgres' then raise exception 'INTERNAL_ONLY' using errcode='42501'; end if;
 if not exists(
   select 1 from public.concessionarias c join public.vinculos_papel_escopo v
     on v.concessionaria_id=c.id
   where c.id=p_loja and c.ativo and v.ator_id=p_ator and v.papel='gestor'
   and v.valido_desde<=statement_timestamp()
   and (v.valido_ate is null or v.valido_ate>statement_timestamp())
 ) then raise exception 'FORBIDDEN_SCOPE' using errcode='42501'; end if;
 if p_chave is null or length(btrim(p_chave)) not between 1 and 160
    or jsonb_typeof(p_linhas) is distinct from 'array'
 then raise exception 'INVALID_BATCH' using errcode='22023'; end if;
 if jsonb_array_length(p_linhas) not between 1 and 100
 then raise exception 'INVALID_BATCH_SIZE' using errcode='22023'; end if;
 v_hash:=encode(sha256(convert_to(p_linhas::text,'UTF8')),'hex');
 perform pg_advisory_xact_lock(hashtextextended(p_loja::text||':'||p_chave,0));
 select id,payload_fingerprint into v_id,v_anterior from public.lotes_importacao
 where concessionaria_id=p_loja and chave_importacao=p_chave;
 if found then
   if v_anterior is distinct from v_hash then
      raise exception 'CONFLICT_IDEMPOTENCY_KEY' using errcode='23505';
   end if;
   return jsonb_build_object('outcome','ALREADY_APPLIED','lote_id',v_id);
 end if;
 insert into public.lotes_importacao(concessionaria_id,chave_importacao,payload_fingerprint)
 values(p_loja,p_chave,v_hash) returning id into v_id;
 for v_row in select value from jsonb_array_elements(p_linhas) loop
   v_n:=v_n+1; v_tel:=null;
   if jsonb_typeof(v_row)='object' and jsonb_typeof(v_row->'telefone')='string'
   then v_tel:=v_row->>'telefone'; end if;
   if v_tel is null or v_tel !~ '^\+[1-9][0-9]{9,14}$' then
     insert into public.itens_lote(concessionaria_id,lote_id,ordinal_linha,resultado,motivo_rejeicao)
     values(p_loja,v_id,v_n,'rejeitado','TELEFONE_INVALIDO');
     v_bad:=v_bad+1; continue;
   end if;
   v_lead:=null;
   insert into public.leads_loja(concessionaria_id,telefone_cliente_normalizado)
      values(p_loja,v_tel)
      on conflict(concessionaria_id,telefone_cliente_normalizado) do nothing
      returning id into v_lead;
   v_novo:=v_lead is not null;
   if not v_novo then
     select id into v_lead from public.leads_loja
     where concessionaria_id=p_loja and telefone_cliente_normalizado=v_tel;
     if v_lead is null then
       raise exception 'CONFLICT_CONCURRENT_LEAD' using errcode='40001';
     end if;
   end if;
   insert into public.itens_lote(concessionaria_id,lote_id,ordinal_linha,lead_id)
      values(p_loja,v_id,v_n,v_lead);
   if v_novo then
     insert into public.ciclos_comerciais(concessionaria_id,lead_id) values(p_loja,v_lead);
   else
     insert into public.reencontros_lote(concessionaria_id,lote_id,lead_id)
     values(p_loja,v_id,v_lead) on conflict do nothing;
   end if;
   v_ok:=v_ok+1;
 end loop;
 return jsonb_build_object('outcome','APPLIED','lote_id',v_id,'aceitos',v_ok,'rejeitados',v_bad);
end $$;

create function prumo_private.transicao_inbound_sintetico(
 p_loja uuid,p_ciclo uuid,p_mensagem uuid,p_versao bigint
) returns jsonb
language plpgsql security invoker set search_path=''
as $$
declare
 v_c public.ciclos_comerciais%rowtype;
 v_evento uuid;
begin
 if current_user <> 'postgres' then raise exception 'INTERNAL_ONLY' using errcode='42501'; end if;
 select * into v_c from public.ciclos_comerciais
 where concessionaria_id=p_loja and id=p_ciclo for update;
 if not found then raise exception 'FORBIDDEN_SCOPE' using errcode='42501'; end if;
 select id into v_evento from public.eventos_status_comercial
 where concessionaria_id=p_loja and ciclo_id=p_ciclo and mensagem_simulada_id=p_mensagem;
 if v_evento is not null then
   return jsonb_build_object('outcome','ALREADY_APPLIED','evento_id',v_evento);
 end if;
 if p_versao is distinct from v_c.versao_registro then
   raise exception 'CONFLICT_VERSION' using errcode='40001';
 end if;
 if v_c.status_comercial<>'aguardando primeiro disparo' then
   raise exception 'INVALID_STATE_TRANSITION' using errcode='22023';
 end if;
 if not exists(
   select 1 from public.mensagens m
   join public.conversas c on c.concessionaria_id=m.concessionaria_id and c.id=m.conversa_id
   where m.id=p_mensagem and m.concessionaria_id=p_loja
     and m.direcao='entrada' and m.origem='simulado'
     and c.lead_id=v_c.lead_id and c.caso_id is null
 ) then raise exception 'INVALID_INBOUND_PROOF' using errcode='22023'; end if;
 update public.ciclos_comerciais set status_comercial='em atendimento pela IA',
    versao_registro=versao_registro+1,ultima_transicao_em=statement_timestamp()
 where id=p_ciclo and concessionaria_id=p_loja;
 insert into public.eventos_status_comercial(
   concessionaria_id,ciclo_id,versao_ciclo_apos,status_anterior,status_posterior,mensagem_simulada_id
 ) values(p_loja,p_ciclo,v_c.versao_registro+1,v_c.status_comercial,
    'em atendimento pela IA',p_mensagem) returning id into v_evento;
 return jsonb_build_object('outcome','APPLIED','evento_id',v_evento,'nova_versao',v_c.versao_registro+1);
end $$;
revoke all on all functions in schema prumo_private from public, anon, authenticated, service_role;
