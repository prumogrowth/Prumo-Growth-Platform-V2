\set ON_ERROR_STOP on
-- S1E-01..07: dados sintéticos, cada escrita integralmente revertida.
begin;
insert into auth.users(id) values
 ('51020000-0000-4000-8000-000000000001'),
 ('51020000-0000-4000-8000-000000000002'),
 ('51020000-0000-4000-8000-000000000003');
insert into public.atores(id) select id from auth.users where id::text like '51020000-%';
insert into public.concessionarias(id,nome_operacional) values
 ('52020000-0000-4000-8000-000000000001','S1 A ficticia'),
 ('52020000-0000-4000-8000-000000000002','S1 B ficticia'),
 ('52020000-0000-4000-8000-000000000003','S1 C ficticia');
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel) values
 ('51020000-0000-4000-8000-000000000001','52020000-0000-4000-8000-000000000001','gestor'),
 ('51020000-0000-4000-8000-000000000001','52020000-0000-4000-8000-000000000002','gestor'),
 ('51020000-0000-4000-8000-000000000002','52020000-0000-4000-8000-000000000001','operador'),
 ('51020000-0000-4000-8000-000000000002','52020000-0000-4000-8000-000000000002','operador'),
 ('51020000-0000-4000-8000-000000000003','52020000-0000-4000-8000-000000000001','gestor');
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado) values
 ('53020000-0000-4000-8000-000000000001','52020000-0000-4000-8000-000000000001','+5581000002001'),
 ('53020000-0000-4000-8000-000000000002','52020000-0000-4000-8000-000000000002','+5581000002001'),
 ('53020000-0000-4000-8000-000000000003','52020000-0000-4000-8000-000000000003','+5581000002001');
insert into public.ciclos_comerciais(id,concessionaria_id,lead_id) values
 ('54020000-0000-4000-8000-000000000001','52020000-0000-4000-8000-000000000001','53020000-0000-4000-8000-000000000001'),
 ('54020000-0000-4000-8000-000000000002','52020000-0000-4000-8000-000000000002','53020000-0000-4000-8000-000000000002');
insert into public.casos_humanos(id,concessionaria_id,lead_id,ciclo_id) values
 ('55020000-0000-4000-8000-000000000001','52020000-0000-4000-8000-000000000001','53020000-0000-4000-8000-000000000001','54020000-0000-4000-8000-000000000001'),
 ('55020000-0000-4000-8000-000000000002','52020000-0000-4000-8000-000000000002','53020000-0000-4000-8000-000000000002','54020000-0000-4000-8000-000000000002');
insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id) values
 ('52020000-0000-4000-8000-000000000001','55020000-0000-4000-8000-000000000001','51020000-0000-4000-8000-000000000002'),
 ('52020000-0000-4000-8000-000000000002','55020000-0000-4000-8000-000000000002','51020000-0000-4000-8000-000000000002');
insert into public.canais_loja(id,concessionaria_id,identificador_emissor)
 values('56020000-0000-4000-8000-000000000001','52020000-0000-4000-8000-000000000001','S1-002-EMISSOR-A');
insert into public.conversas(id,concessionaria_id,lead_id,canal_id,caso_id)
 values('57020000-0000-4000-8000-000000000001','52020000-0000-4000-8000-000000000001',
 '53020000-0000-4000-8000-000000000001','56020000-0000-4000-8000-000000000001','55020000-0000-4000-8000-000000000001');
insert into public.equipe_prumo_s1(ator_id,estado) values
 ('51020000-0000-4000-8000-000000000001','ativo'),
 ('51020000-0000-4000-8000-000000000002','ativo');
do $$
declare n integer; gated integer;
begin
 select count(*) into n from pg_catalog.pg_class c
 join pg_catalog.pg_namespace s on s.oid=c.relnamespace
 where s.nspname='public' and c.relkind in ('r','p') and c.relrowsecurity
 and c.relname not in ('equipe_prumo_s1','equipe_prumo_eventos_s1');
 select count(*) into gated from pg_catalog.pg_policies
 where schemaname='public' and policyname='s1_equipe_ativa_gate';
 if n<>gated or n<10 then raise exception 'S1E-01 gate %/%',gated,n;end if;
 if (select count(*) from public.equipe_prumo_eventos_s1)<>2 then
 raise exception 'S1E-01 missing event audit';end if;
end $$;
\echo 'PASS S1E-01 coverage RLS + audit'
set local role authenticated;
select set_config('request.jwt.claim.sub','51020000-0000-4000-8000-000000000001',true);
do $$
begin
 if (select count(*) from public.leads_loja)<>2
 or (select count(*) from public.concessionarias)<>2
 or (select count(*) from public.equipe_prumo_s1)<>1 then
 raise exception 'S1E-02 manager scope';end if;
end $$;
\echo 'PASS S1E-02 gestor Prumo A+B, nao C'
select set_config('request.jwt.claim.sub','51020000-0000-4000-8000-000000000002',true);
do $$
begin
 if (select count(*) from public.casos_humanos)<>2
 or (select count(*) from public.leads_loja)<>2 then
 raise exception 'S1E-03 assigned cases';end if;
 begin
  update public.equipe_prumo_s1 set estado='ativo';
  raise exception 'S1E-03 team self-grant';
 exception when insufficient_privilege then null;end;
 begin
  insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel)
   values('51020000-0000-4000-8000-000000000002','52020000-0000-4000-8000-000000000003','gestor');
  raise exception 'S1E-03 shop self-grant';
 exception when insufficient_privilege then null;end;
end $$;
\echo 'PASS S1E-03 operador A+B so casos; sem autoconcessao'
select set_config('request.jwt.claim.sub','51020000-0000-4000-8000-000000000003',true);
do $$
begin
 if exists(select 1 from public.leads_loja)
 or exists(select 1 from public.concessionarias) then
 raise exception 'S1E-04 grant without team';end if;
end $$;
\echo 'PASS S1E-04 concessao sem equipe nao libera'
reset role;
update public.equipe_prumo_s1 set estado='suspenso'
 where ator_id='51020000-0000-4000-8000-000000000002';
set local role authenticated;
select set_config('request.jwt.claim.sub','51020000-0000-4000-8000-000000000002',true);
do $$
begin
 if exists(select 1 from public.leads_loja) or exists(select 1 from public.casos_humanos)
 or exists(select 1 from public.atribuicoes_humanas) then
 raise exception 'S1E-05 suspended operator read D2';end if;
 begin
  insert into public.mensagens(concessionaria_id,conversa_id,canal_id,caso_id,direcao,origem,conteudo_sintetico,enviada_por)
  values('52020000-0000-4000-8000-000000000001','57020000-0000-4000-8000-000000000001',
  '56020000-0000-4000-8000-000000000001','55020000-0000-4000-8000-000000000001',
  'saida','simulado','mensagem ficticia bloqueada','51020000-0000-4000-8000-000000000002');
  raise exception 'S1E-05 suspended operator wrote';
 exception when insufficient_privilege or check_violation then null;end;
end $$;
\echo 'PASS S1E-05 suspensao bloqueia D2 e mensagem'
reset role;
update public.equipe_prumo_s1 set estado='suspenso'
 where ator_id='51020000-0000-4000-8000-000000000001';
set local role authenticated;
select set_config('request.jwt.claim.sub','51020000-0000-4000-8000-000000000001',true);
do $$
begin
 if exists(select 1 from public.leads_loja) or exists(select 1 from public.conversas)
 then raise exception 'S1E-06 manager suspended';end if;
end $$;
\echo 'PASS S1E-06 gestor suspenso perde A+B'
reset role;
update public.equipe_prumo_s1 set estado='desligado'
 where ator_id='51020000-0000-4000-8000-000000000002';
do $$
begin
 if (select count(*) from public.equipe_prumo_eventos_s1)<>5
 or (select count(*) from public.atribuicoes_humanas
     where operador_id='51020000-0000-4000-8000-000000000002' and encerrada_em is null)<>2
 then raise exception 'S1E-07 events or stale assignment observation';end if;
end $$;
\echo 'PASS S1E-07 auditado; 2 atribuicoes ainda ativas = lacuna pendente'
rollback;
