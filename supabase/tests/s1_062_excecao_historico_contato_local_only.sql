\set ON_ERROR_STOP on
-- S1-002 I42: contrato S1-D12/D13/D18 + isolamento da mesma loja.
-- Preparacao I53/I54/I55 dentro da MESMA transacao, sem migrations de produto.
-- Apenas PostgreSQL 17 descartavel, auth.uid simulada e dados sinteticos.
begin;
\ir s1_053_issue10_disponibilidade_local_only.sql
\ir s1_054_issue10_s0_prova_redistribuicao_local_only.sql
\ir s1_055_issue10_excecao_caso_local_only.sql

insert into auth.users(id)
 select ('62110000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid
 from generate_series(1,5) i;
insert into public.atores(id)
 select id from auth.users where id::text like '62110000-%';
insert into public.equipe_prumo_s1(ator_id,estado)
 select id,'ativo' from public.atores where id::text like '62110000-%';
-- M1 => origem C2 (grant A/B) + destino C3 (sem grant geral).
-- M4 => C5 de outra equipe com grant A.
insert into prumo_private.s1_gestor_operadores(gestor_id,operador_id) values
 ('62110000-0000-4000-8000-000000000001','62110000-0000-4000-8000-000000000002'),
 ('62110000-0000-4000-8000-000000000001','62110000-0000-4000-8000-000000000003'),
 ('62110000-0000-4000-8000-000000000004','62110000-0000-4000-8000-000000000005');
insert into public.concessionarias(id,nome_operacional) values
 ('62220000-0000-4000-8000-000000000001','I42 ficticia A'),
 ('62220000-0000-4000-8000-000000000002','I42 ficticia B');
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel) values
 ('62110000-0000-4000-8000-000000000002','62220000-0000-4000-8000-000000000001','operador'),
 ('62110000-0000-4000-8000-000000000002','62220000-0000-4000-8000-000000000002','operador'),
 ('62110000-0000-4000-8000-000000000005','62220000-0000-4000-8000-000000000001','operador');
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado) values
 ('62330000-0000-4000-8000-000000000001','62220000-0000-4000-8000-000000000001','+5581888804242'),
 ('62330000-0000-4000-8000-000000000002','62220000-0000-4000-8000-000000000001','+5581888804243'),
 ('62330000-0000-4000-8000-000000000003','62220000-0000-4000-8000-000000000002','+5581888804242');
insert into public.ciclos_comerciais(id,concessionaria_id,lead_id,status_comercial)
 select ('62440000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 case when i=4 then '62220000-0000-4000-8000-000000000002'::uuid
 else '62220000-0000-4000-8000-000000000001'::uuid end,
 case when i in (1,2) then '62330000-0000-4000-8000-000000000001'::uuid
 when i=3 then '62330000-0000-4000-8000-000000000002'::uuid
 else '62330000-0000-4000-8000-000000000003'::uuid end,
 'em atendimento pelo operador' from generate_series(1,4) i;
insert into public.casos_humanos(id,concessionaria_id,lead_id,ciclo_id)
 select ('62550000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 c.concessionaria_id,c.lead_id,c.id
 from generate_series(1,4) i
 join public.ciclos_comerciais c
 on c.id=('62440000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid;
insert into public.canais_loja(id,concessionaria_id,identificador_emissor) values
 ('62660000-0000-4000-8000-000000000001','62220000-0000-4000-8000-000000000001','S1-I42-A'),
 ('62660000-0000-4000-8000-000000000002','62220000-0000-4000-8000-000000000002','S1-I42-B');
insert into public.conversas(id,concessionaria_id,lead_id,canal_id,caso_id)
 select ('62770000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 h.concessionaria_id,h.lead_id,
 ('62660000-0000-4000-8000-'||lpad((case when i=4 then 2 else 1 end)::text,12,'0'))::uuid,
 h.id
 from generate_series(1,4) i
 join public.casos_humanos h
 on h.id=('62550000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid;
insert into public.mensagens(concessionaria_id,conversa_id,canal_id,caso_id,
 direcao,origem,conteudo_sintetico,id_externo)
 select co.concessionaria_id,co.id,co.canal_id,co.caso_id,
 'entrada','simulado','I42 mensagem historica '||i,'i42-ext-'||i
 from generate_series(1,4) i
 join public.conversas co
 on co.id=('62770000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid;
-- Caso 1: historico ENCERRADO do mesmo contato A.
-- Caso 2: titular atual C2, a transferir a C3 sem grant.
-- Caso 3: outro contato e outra equipe. Caso 4: outra loja mesmo telefone.
insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id)
 select h.concessionaria_id,h.id,
 case when right(h.id::text,1)='3' then '62110000-0000-4000-8000-000000000005'::uuid
 else '62110000-0000-4000-8000-000000000002'::uuid end
 from public.casos_humanos h where h.id::text like '62550000-%';
update public.atribuicoes_humanas
 set encerrada_em=greatest(atribuida_em,pg_catalog.statement_timestamp())
 where caso_id='62550000-0000-4000-8000-000000000001';

do $t$ declare aid uuid; j jsonb;begin
 select id into aid from public.atribuicoes_humanas
 where caso_id='62550000-0000-4000-8000-000000000002' and encerrada_em is null;
 j:=prumo_private.s1_mover_excecao_caso_55(
 '62110000-0000-4000-8000-000000000001',
 '62220000-0000-4000-8000-000000000001',
 '62550000-0000-4000-8000-000000000002',
 aid,'62110000-0000-4000-8000-000000000003');
 if j->>'outcome'<>'MOVED_CASE_EXCEPTION' then
  raise exception 'I42-SETUP transfer exception failed %',j;end if;
end $t$;

-- Baseline I55: acerta caso atual, mas nao o passado do MESMO contato.
set local role authenticated;
select pg_catalog.set_config('request.jwt.claim.sub',
 '62110000-0000-4000-8000-000000000003',true);
do $t$ begin
 if (select count(*) from public.casos_humanos where id::text like '62550000-%')<>1
 or (select count(*) from public.conversas where id::text like '62770000-%')<>1
 or (select count(*) from public.mensagens where conteudo_sintetico like 'I42 mensagem historica %')<>1
 then raise exception 'I42-RED I55 baseline inesperado';end if;
end $t$;
\echo 'OBSERVED I42-RED: I55 autoriza apenas o caso corrente, nao historia do mesmo contato'
reset role;

-- Candidato puramente local: o entitlement de caso atual abre somente
-- a leitura contextual do lead em MESMA loja, nunca outro lead ou loja.
create schema prumo_s1_i42_test authorization postgres;
create function prumo_s1_i42_test.historico_autorizado(
 p_loja uuid,p_lead uuid)
returns boolean language sql stable security definer set search_path='' as $fn$
 select p_loja is not null and p_lead is not null and (select auth.uid()) is not null
 and exists (
  select 1 from public.casos_humanos h_cur
  join public.atribuicoes_humanas a
   on a.concessionaria_id=h_cur.concessionaria_id
    and a.caso_id=h_cur.id and a.encerrada_em is null
  join prumo_private.s1_excecoes_55 x on x.atribuicao_id=a.id
   and x.concessionaria_id=h_cur.concessionaria_id
   and x.caso_id=h_cur.id and x.operador_id=a.operador_id
   and x.revogada_em is null
  join public.equipe_prumo_s1 op on op.ator_id=a.operador_id
   and op.estado='ativo'
  join public.equipe_prumo_s1 mg on mg.ator_id=x.gestor_id
   and mg.estado='ativo'
  join prumo_private.s1_gestor_operadores go
   on go.gestor_id=x.gestor_id and go.operador_id=a.operador_id
    and go.encerrado_em is null
  join public.concessionarias l
   on l.id=h_cur.concessionaria_id and l.ativo
  where h_cur.concessionaria_id=p_loja and h_cur.lead_id=p_lead
   and a.operador_id=(select auth.uid())
 );
$fn$;
create function prumo_s1_i42_test.caso_historico_autorizado(
 p_loja uuid,p_caso uuid)
returns boolean language sql stable security definer set search_path='' as $fn$
 select exists(select 1 from public.casos_humanos h
  where h.concessionaria_id=p_loja and h.id=p_caso
   and prumo_s1_i42_test.historico_autorizado(p_loja,h.lead_id));
$fn$;
-- O gate de mensagens deve validar a pertença do corpo a conversa exata,
-- tanto para historico sem grant quanto para a excecao corrente.
create function prumo_s1_i42_test.msg_historico_autorizado(
 p_loja uuid,p_conversa uuid,p_caso uuid)
returns boolean language sql stable security definer set search_path='' as $fn$
 select p_loja is not null and p_conversa is not null and p_caso is not null
 and exists (select 1 from public.conversas co
  where co.concessionaria_id=p_loja and co.id=p_conversa
   and co.caso_id=p_caso
   and prumo_s1_i42_test.historico_autorizado(p_loja,co.lead_id));
$fn$;
revoke all on schema prumo_s1_i42_test from public,anon,service_role;
grant usage on schema prumo_s1_i42_test to authenticated;
revoke all on function
 prumo_s1_i42_test.historico_autorizado(uuid,uuid),
 prumo_s1_i42_test.caso_historico_autorizado(uuid,uuid),
 prumo_s1_i42_test.msg_historico_autorizado(uuid,uuid,uuid)
 from public,anon,service_role;
grant execute on function
 prumo_s1_i42_test.historico_autorizado(uuid,uuid),
 prumo_s1_i42_test.caso_historico_autorizado(uuid,uuid),
 prumo_s1_i42_test.msg_historico_autorizado(uuid,uuid,uuid)
 to authenticated;

create policy s1_62_caso_historico on public.casos_humanos
 for select to authenticated using (
 prumo_s1_i42_test.historico_autorizado(concessionaria_id,lead_id));
create policy s1_62_conversa_historico on public.conversas
 for select to authenticated using (
 caso_id is not null
 and prumo_s1_i42_test.historico_autorizado(concessionaria_id,lead_id));
-- Revisor S0 precisa consolidar policies finais: I55 restritiva original
-- nao admitia historico. Aqui se substitui somente DENTRO do rollback.
drop policy s1_55_mensagens_restrict on public.mensagens;
create policy s1_62_mensagens_restrict on public.mensagens as restrictive
 for select to authenticated using (
 (
  exists(select 1 from public.vinculos_papel_escopo v
   where v.ator_id=(select auth.uid())
    and v.concessionaria_id=mensagens.concessionaria_id
    and v.papel in ('gestor','operador','responsavel')
    and v.valido_desde<=pg_catalog.statement_timestamp()
    and (v.valido_ate is null or v.valido_ate>pg_catalog.statement_timestamp()))
 ) or (
  caso_id is not null
  and prumo_s1_i42_test.msg_historico_autorizado(
      concessionaria_id,conversa_id,caso_id)
 )
);
-- Visao de escopo minimo: contextualiza ciclo sem SELECT bruto dos demais.
-- Usa owner no LAB sob predicado JWT+excecao valido de cada contato.
create view public.s1_62_historico_contato_resumo with (security_barrier=true) as
 select h.concessionaria_id,h.id as caso_id,h.lead_id,h.ciclo_id,
        c.status_comercial,l.telefone_cliente_normalizado
 from public.casos_humanos h
 join public.ciclos_comerciais c
  on c.concessionaria_id=h.concessionaria_id and c.id=h.ciclo_id
 join public.leads_loja l
  on l.concessionaria_id=h.concessionaria_id and l.id=h.lead_id
 where prumo_s1_i42_test.historico_autorizado(h.concessionaria_id,h.lead_id);
revoke all on public.s1_62_historico_contato_resumo from public,anon,service_role;
grant select on public.s1_62_historico_contato_resumo to authenticated;

set local role authenticated;
select pg_catalog.set_config('request.jwt.claim.sub',
 '62110000-0000-4000-8000-000000000003',true);
do $t$ begin
 if (select count(*) from public.casos_humanos where id::text like '62550000-%')<>2
 or (select count(*) from public.conversas where id::text like '62770000-%')<>2
 or (select count(*) from public.mensagens
     where conteudo_sintetico like 'I42 mensagem historica %')<>2
 or (select count(*) from public.s1_62_historico_contato_resumo)<>2
 or (select count(*) from public.s1_55_resumo_caso)<>1
 then raise exception 'I42-01 nao delimitou mesmo contato com historico';end if;
 if exists(select 1 from public.casos_humanos
     where id in ('62550000-0000-4000-8000-000000000003',
                  '62550000-0000-4000-8000-000000000004'))
 or exists(select 1 from public.leads_loja where id::text like '62330000-%')
 or exists(select 1 from public.ciclos_comerciais where id::text like '62440000-%')
 or exists(select 1 from public.concessionarias where id::text like '62220000-%')
 or exists(select 1 from public.canais_loja where id::text like '62660000-%')
 or exists(select 1 from public.lotes_importacao)
 or exists(select 1 from public.eventos_status_comercial)
 then raise exception 'I42-02 acesso a outros casos ou colecoes S0';end if;
end $t$;
\echo 'PASS I42-01/02: caso excepcional e historia mesmo contato/loja; zero colecoes brutas S0'

do $t$ begin
 begin
  insert into public.mensagens(concessionaria_id,conversa_id,canal_id,caso_id,
   direcao,origem,conteudo_sintetico,enviada_por)
  values('62220000-0000-4000-8000-000000000001',
   '62770000-0000-4000-8000-000000000001',
   '62660000-0000-4000-8000-000000000001',
   '62550000-0000-4000-8000-000000000001',
   'saida','simulado','I42 tentativa de escrita historica',
   '62110000-0000-4000-8000-000000000003');
  raise exception 'I42-03 escreveu em caso antigo';
 exception when insufficient_privilege or check_violation then null;end;
 insert into public.mensagens(concessionaria_id,conversa_id,canal_id,caso_id,
  direcao,origem,conteudo_sintetico,enviada_por)
 values('62220000-0000-4000-8000-000000000001',
  '62770000-0000-4000-8000-000000000002',
  '62660000-0000-4000-8000-000000000001',
  '62550000-0000-4000-8000-000000000002',
  'saida','simulado','I42 resposta corrente excepcional',
  '62110000-0000-4000-8000-000000000003');
 if (select count(*) from public.mensagens
  where conteudo_sintetico='I42 resposta corrente excepcional')<>1 then
  raise exception 'I42-03 nao enviou caso corrente';end if;
end $t$;
\echo 'PASS I42-03: historico somente leitura; escrita exclusivamente no caso atual'

reset role;
do $t$ declare x uuid; j jsonb; begin
 select id into x from prumo_private.s1_excecoes_55
 where caso_id='62550000-0000-4000-8000-000000000002'
   and operador_id='62110000-0000-4000-8000-000000000003'
   and revogada_em is null;
 j:=prumo_private.s1_revogar_excecao_55(
 '62110000-0000-4000-8000-000000000001',x);
 if j->>'outcome'<>'REVOKED_CASE_ACCESS'
 or (select count(*) from public.atribuicoes_humanas
     where caso_id='62550000-0000-4000-8000-000000000002'
      and operador_id='62110000-0000-4000-8000-000000000003'
      and encerrada_em is null)<>1
 then raise exception 'I42-04 revogacao/titularidade errada %',j;end if;
end $t$;
set local role authenticated;
select pg_catalog.set_config('request.jwt.claim.sub',
 '62110000-0000-4000-8000-000000000003',true);
do $t$ begin
 if exists(select 1 from public.casos_humanos where id::text like '62550000-%')
 or exists(select 1 from public.conversas where id::text like '62770000-%')
 or exists(select 1 from public.mensagens where conteudo_sintetico like 'I42 mensagem historica %')
 or exists(select 1 from public.s1_62_historico_contato_resumo)
 or exists(select 1 from public.s1_55_resumo_caso)
 then raise exception 'I42-04 revogacao nao cortou historico';end if;
 begin
  insert into public.mensagens(concessionaria_id,conversa_id,canal_id,caso_id,
   direcao,origem,conteudo_sintetico,enviada_por)
  values('62220000-0000-4000-8000-000000000001',
   '62770000-0000-4000-8000-000000000002',
   '62660000-0000-4000-8000-000000000001',
   '62550000-0000-4000-8000-000000000002',
   'saida','simulado','I42 resposta apos revogacao',
   '62110000-0000-4000-8000-000000000003');
  raise exception 'I42-05 escrita apos revogacao';
 exception when insufficient_privilege or check_violation then null;end;
end $t$;
\echo 'PASS I42-04/05: revogacao corta leitura do caso, historico e envio; atribuicao S0 permanece'

reset role;
do $t$ begin
 if (select count(*) from public.vinculos_papel_escopo
  where ator_id='62110000-0000-4000-8000-000000000003')<>0
 or (select count(*) from prumo_private.s1_excecoes_eventos_55
  where tipo='CRIADA')<>1
 or (select count(*) from prumo_private.s1_excecoes_eventos_55
  where tipo='REVOGADA')<>1
 then raise exception 'I42-06 acesso generalizado ou auditoria inconsistente';end if;
end $t$;
rollback;
\echo 'PASS I42-06/ROLLBACK: zero grant de loja e trilha de revogacao, todas alteracoes removidas'
