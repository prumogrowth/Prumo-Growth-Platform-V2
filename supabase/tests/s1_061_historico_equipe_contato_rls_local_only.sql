\set ON_ERROR_STOP on
-- S1-002 I41: ponte de leitura S0/S1 (supervisao historica vs contato proprio).
-- Dados ficticios, BEGIN/ROLLBACK, sem migration e sem alterar contrato S0.
-- NAO promove policy: case-only exceptions I55, docs D3/D4, Diretor,
-- mensagens sem case_id e funcoes definer externas ainda nao cobertos.
begin;
insert into auth.users(id)
select ('61110000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid
from generate_series(1,7) i;
insert into public.atores(id)
select id from auth.users where id::text like '61110000-%';
insert into public.equipe_prumo_s1(ator_id,estado)
select id,'ativo' from public.atores where id::text like '61110000-%';
-- M1->C4, M2->C5, M3->C6 e C7. M3 nao possui grant de nenhuma loja.
insert into prumo_private.s1_gestor_operadores(gestor_id,operador_id) values
 ('61110000-0000-4000-8000-000000000001','61110000-0000-4000-8000-000000000004'),
 ('61110000-0000-4000-8000-000000000002','61110000-0000-4000-8000-000000000005'),
 ('61110000-0000-4000-8000-000000000003','61110000-0000-4000-8000-000000000006'),
 ('61110000-0000-4000-8000-000000000003','61110000-0000-4000-8000-000000000007');
insert into public.concessionarias(id,nome_operacional) values
 ('61220000-0000-4000-8000-000000000001','S1 I41 Loja A ficticia'),
 ('61220000-0000-4000-8000-000000000002','S1 I41 Loja B ficticia');
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel) values
 ('61110000-0000-4000-8000-000000000001','61220000-0000-4000-8000-000000000001','gestor'),
 ('61110000-0000-4000-8000-000000000002','61220000-0000-4000-8000-000000000001','gestor'),
 ('61110000-0000-4000-8000-000000000004','61220000-0000-4000-8000-000000000001','operador'),
 ('61110000-0000-4000-8000-000000000005','61220000-0000-4000-8000-000000000001','operador'),
 ('61110000-0000-4000-8000-000000000006','61220000-0000-4000-8000-000000000001','operador'),
 ('61110000-0000-4000-8000-000000000007','61220000-0000-4000-8000-000000000002','operador');
-- Contato L1 tem C1 antigo (C5 antiga titular) + C2 atual (C4 titular).
-- L2 pertence C5; L3 pertence C6; L4 na loja B usa MESMO telefone L1.
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado) values
 ('61330000-0000-4000-8000-000000000001','61220000-0000-4000-8000-000000000001','+5581888814111'),
 ('61330000-0000-4000-8000-000000000002','61220000-0000-4000-8000-000000000001','+5581888814222'),
 ('61330000-0000-4000-8000-000000000003','61220000-0000-4000-8000-000000000001','+5581888814333'),
 ('61330000-0000-4000-8000-000000000004','61220000-0000-4000-8000-000000000002','+5581888814111');
insert into public.ciclos_comerciais(id,concessionaria_id,lead_id,status_comercial)
select ('61440000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 case when i=5 then '61220000-0000-4000-8000-000000000002'::uuid
      else '61220000-0000-4000-8000-000000000001'::uuid end,
 case i when 1 then '61330000-0000-4000-8000-000000000001'::uuid
        when 2 then '61330000-0000-4000-8000-000000000001'::uuid
        when 3 then '61330000-0000-4000-8000-000000000002'::uuid
        when 4 then '61330000-0000-4000-8000-000000000003'::uuid
        else '61330000-0000-4000-8000-000000000004'::uuid end,
 'em atendimento pelo operador'
 from generate_series(1,5) i;
insert into public.casos_humanos(id,concessionaria_id,lead_id,ciclo_id)
select ('61550000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 case when i=5 then '61220000-0000-4000-8000-000000000002'::uuid
      else '61220000-0000-4000-8000-000000000001'::uuid end,
 case i when 1 then '61330000-0000-4000-8000-000000000001'::uuid
        when 2 then '61330000-0000-4000-8000-000000000001'::uuid
        when 3 then '61330000-0000-4000-8000-000000000002'::uuid
        when 4 then '61330000-0000-4000-8000-000000000003'::uuid
        else '61330000-0000-4000-8000-000000000004'::uuid end,
 ('61440000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid
 from generate_series(1,5) i;
insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id)
 select '61220000-0000-4000-8000-000000000001',
 '61550000-0000-4000-8000-000000000001',
 '61110000-0000-4000-8000-000000000005';
-- Encerrado: Consultor C5 nao deve recuperar acesso pelo caso antigo.
update public.atribuicoes_humanas set encerrada_em=greatest(atribuida_em,pg_catalog.statement_timestamp())
 where caso_id='61550000-0000-4000-8000-000000000001';
insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id)
 select h.concessionaria_id,h.id,
 case right(h.id::text,1)
  when '2' then '61110000-0000-4000-8000-000000000004'::uuid
  when '3' then '61110000-0000-4000-8000-000000000005'::uuid
  when '4' then '61110000-0000-4000-8000-000000000006'::uuid
  else '61110000-0000-4000-8000-000000000007'::uuid end
 from public.casos_humanos h
 where h.id::text like '61550000-%' and h.id<>'61550000-0000-4000-8000-000000000001';
insert into public.canais_loja(id,concessionaria_id,identificador_emissor) values
 ('61660000-0000-4000-8000-000000000001','61220000-0000-4000-8000-000000000001','S1-I41-A'),
 ('61660000-0000-4000-8000-000000000002','61220000-0000-4000-8000-000000000002','S1-I41-B');
insert into public.conversas(id,concessionaria_id,lead_id,canal_id,caso_id)
select ('61770000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 case when i=5 then '61220000-0000-4000-8000-000000000002'::uuid
      else '61220000-0000-4000-8000-000000000001'::uuid end,
 case i when 1 then '61330000-0000-4000-8000-000000000001'::uuid
        when 2 then '61330000-0000-4000-8000-000000000001'::uuid
        when 3 then '61330000-0000-4000-8000-000000000002'::uuid
        when 4 then '61330000-0000-4000-8000-000000000003'::uuid
        else '61330000-0000-4000-8000-000000000004'::uuid end,
 case when i=5 then '61660000-0000-4000-8000-000000000002'::uuid
      else '61660000-0000-4000-8000-000000000001'::uuid end,
 ('61550000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid
 from generate_series(1,5) i;
insert into public.mensagens(concessionaria_id,conversa_id,canal_id,caso_id,
direcao,origem,conteudo_sintetico,id_externo)
select case when i=5 then '61220000-0000-4000-8000-000000000002'::uuid
            else '61220000-0000-4000-8000-000000000001'::uuid end,
 ('61770000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 case when i=5 then '61660000-0000-4000-8000-000000000002'::uuid
      else '61660000-0000-4000-8000-000000000001'::uuid end,
 ('61550000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 'entrada','simulado','I41 msg ficticia '||i,'i41-ext-'||i
 from generate_series(1,5) i;

-- Baseline S0: manager com grant ve qualquer caso daquela loja,
-- enquanto chefia SEM grant nao enxerga caso proprio da equipe.
set local role authenticated;
select pg_catalog.set_config('request.jwt.claim.sub',
 '61110000-0000-4000-8000-000000000001',true);
do $t$ begin
 if (select count(*) from public.casos_humanos where id::text like '61550000-%')<>4
 then raise exception 'I41-RED01 nao reproduziu exposicao interequipes';end if;
end $t$;
select pg_catalog.set_config('request.jwt.claim.sub',
 '61110000-0000-4000-8000-000000000003',true);
do $t$ begin
 if exists(select 1 from public.casos_humanos where id::text like '61550000-%')
 then raise exception 'I41-RED02 nao reproduziu falta de supervisao sem loja';end if;
end $t$;
reset role;
\echo 'OBSERVED I41-RED: policies S0 por loja expõem outros times e negam chefia sem grant'

\ir s1_061_proto_rls_equipe_local_only.sql

-- Isolamento por equipe, inclusive historial e mensagens por caso.
set local role authenticated;
select pg_catalog.set_config('request.jwt.claim.sub',
 '61110000-0000-4000-8000-000000000001',true);
do $t$ begin
 if (select count(*) from public.casos_humanos where id::text like '61550000-%')<>1
 or (select count(*) from public.atribuicoes_humanas
     where caso_id::text like '61550000-%')<>1
 or (select count(*) from public.conversas where id::text like '61770000-%')<>1
 or (select count(*) from public.mensagens
     where conteudo_sintetico like 'I41 msg ficticia %')<>1
 then raise exception 'I41-GREEN01 gestor M1 viu outra equipe';end if;
end $t$;
\echo 'PASS I41-01: Gestor M1 com grant ve SOMENTE casos atuais/passados da sua equipe'
select pg_catalog.set_config('request.jwt.claim.sub',
 '61110000-0000-4000-8000-000000000002',true);
do $t$ begin
 if (select count(*) from public.casos_humanos where id::text like '61550000-%')<>2
 or (select count(*) from public.atribuicoes_humanas
     where caso_id::text like '61550000-%')<>2
 or (select count(*) from public.mensagens
     where conteudo_sintetico like 'I41 msg ficticia %')<>2
 then raise exception 'I41-GREEN02 gestor M2 perdeu historico ou vazou equipe';end if;
end $t$;
\echo 'PASS I41-02: Gestor M2 ve caso antigo da propria equipe, nao outro time'
select pg_catalog.set_config('request.jwt.claim.sub',
 '61110000-0000-4000-8000-000000000003',true);
do $t$ begin
 if (select count(*) from public.casos_humanos where id::text like '61550000-%')<>2
 or (select count(*) from public.mensagens
     where conteudo_sintetico like 'I41 msg ficticia %')<>2
 then raise exception 'I41-GREEN03 gestor sem loja perdeu equipe';end if;
end $t$;
\echo 'PASS I41-03: Gestor M3 sem grant ve atendimentos da propria equipe em A e B'
select pg_catalog.set_config('request.jwt.claim.sub',
 '61110000-0000-4000-8000-000000000004',true);
do $t$ begin
 if (select count(*) from public.casos_humanos where id::text like '61550000-%')<>2
 or (select count(*) from public.conversas where id::text like '61770000-%')<>2
 or (select count(*) from public.mensagens
     where conteudo_sintetico like 'I41 msg ficticia %')<>2
 or (select count(*) from public.atribuicoes_humanas
     where caso_id::text like '61550000-%')<>1
 then raise exception 'I41-GREEN04 Consultor sem historico do contato ou acessou equipe';end if;
 begin
  insert into public.mensagens(concessionaria_id,conversa_id,canal_id,caso_id,
   direcao,origem,conteudo_sintetico,enviada_por)
  values('61220000-0000-4000-8000-000000000001',
   '61770000-0000-4000-8000-000000000001',
   '61660000-0000-4000-8000-000000000001',
   '61550000-0000-4000-8000-000000000001',
   'saida','simulado','I41 tentativa indevida de resposta em historico',
   '61110000-0000-4000-8000-000000000004');
  raise exception 'I41-GREEN04 escreveu caso historico';
 exception when insufficient_privilege or check_violation then null;end;
end $t$;
\echo 'PASS I41-04: Consultor C4 le historico do proprio contato A sem poder enviar no caso antigo'
select pg_catalog.set_config('request.jwt.claim.sub',
 '61110000-0000-4000-8000-000000000005',true);
do $t$ begin
 if (select count(*) from public.casos_humanos where id::text like '61550000-%')<>1
 or (select count(*) from public.mensagens
     where conteudo_sintetico like 'I41 msg ficticia %')<>1
 then raise exception 'I41-GREEN05 ex-titular ainda ve caso historico de outro time';end if;
end $t$;
\echo 'PASS I41-05: Consultor C5 ex-titular nao navega contato alheio sem caso atual'
select pg_catalog.set_config('request.jwt.claim.sub',
 '61110000-0000-4000-8000-000000000007',true);
do $t$ begin
 if (select count(*) from public.casos_humanos where id::text like '61550000-%')<>1
 or (select count(*) from public.mensagens
    where conteudo_sintetico like 'I41 msg ficticia %')<>1
 then raise exception 'I41-GREEN06 mesmo telefone cruzou lojas';end if;
end $t$;
\echo 'PASS I41-06: mesmo telefone em loja B nao libera historico da loja A'
-- Ler como Gestor nao permite enviar sem transferencia formal S0.
select pg_catalog.set_config('request.jwt.claim.sub',
 '61110000-0000-4000-8000-000000000001',true);
do $t$ begin
 begin
  insert into public.mensagens(concessionaria_id,conversa_id,canal_id,caso_id,
   direcao,origem,conteudo_sintetico,enviada_por)
  values('61220000-0000-4000-8000-000000000001',
   '61770000-0000-4000-8000-000000000002',
   '61660000-0000-4000-8000-000000000001',
   '61550000-0000-4000-8000-000000000002',
   'saida','simulado','I41 tentativa indevida de gestor observador',
   '61110000-0000-4000-8000-000000000001');
  raise exception 'I41-GREEN07 Gestor sem titularidade enviou';
 exception when insufficient_privilege or check_violation then null;end;
end $t$;
select pg_catalog.set_config('request.jwt.claim.sub',
 '61110000-0000-4000-8000-000000000004',true);
insert into public.mensagens(concessionaria_id,conversa_id,canal_id,caso_id,
 direcao,origem,conteudo_sintetico,enviada_por)
values('61220000-0000-4000-8000-000000000001',
 '61770000-0000-4000-8000-000000000002',
 '61660000-0000-4000-8000-000000000001',
 '61550000-0000-4000-8000-000000000002',
 'saida','simulado','I41 resposta simulada do titular atual',
 '61110000-0000-4000-8000-000000000004');
do $t$ begin
 if (select count(*) from public.mensagens
      where conteudo_sintetico='I41 resposta simulada do titular atual'
        and enviada_por='61110000-0000-4000-8000-000000000004')<>1
 then raise exception 'I41-GREEN07 Consultor titular nao conseguiu enviar';end if;
end $t$;
\echo 'PASS I41-07: Gestor observador nao envia; Consultor titular envia caso atual simulado'
reset role;
rollback;
\echo 'PASS I41-ROLLBACK: candidatura de policy e dados removidos; S0 inalterada'
