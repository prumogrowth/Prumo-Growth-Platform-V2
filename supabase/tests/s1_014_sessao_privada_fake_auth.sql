\set ON_ERROR_STOP on
-- I14: facade de sessao em schema PRUMO_PRIVATE, autenticação FAKE.
-- 2 lojas; gestores G1/G2; operadores O3/O4/O5. Tudo em ROLLBACK.
begin;
insert into auth.users(id)
 select ('e1120000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid
 from generate_series(1,6) i;
insert into public.atores(id) select id from auth.users where id::text like 'e1120000-%';
insert into public.equipe_prumo_s1(ator_id,estado)
 select id,'ativo' from public.atores where id::text like 'e1120000-%';
insert into prumo_private.s1_responsaveis_plataforma(ator_id)
 values('e1120000-0000-4000-8000-000000000006');
insert into prumo_private.s1_gestor_operadores(gestor_id,operador_id) values
 ('e1120000-0000-4000-8000-000000000001','e1120000-0000-4000-8000-000000000003'),
 ('e1120000-0000-4000-8000-000000000001','e1120000-0000-4000-8000-000000000004'),
 ('e1120000-0000-4000-8000-000000000002','e1120000-0000-4000-8000-000000000005');
insert into public.concessionarias(id,nome_operacional) values
 ('e2120000-0000-4000-8000-000000000001','S1S loja A'),
 ('e2120000-0000-4000-8000-000000000002','S1S loja B');
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel)
 select ('e1120000-0000-4000-8000-'||lpad(op::text,12,'0'))::uuid,
 ('e2120000-0000-4000-8000-'||lpad(loja::text,12,'0'))::uuid,'operador'
 from (values (3,1),(3,2),(4,1),(4,2),(5,1),(5,2)) a(op,loja);
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado)
 select ('e3120000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 ('e2120000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 '+5581981500'||lpad(i::text,4,'0')
 from generate_series(1,2) i;
insert into public.ciclos_comerciais(id,concessionaria_id,lead_id,status_comercial)
 select ('e4120000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 l.concessionaria_id,l.id,'em atendimento pelo operador'
 from generate_series(1,2) i
 join public.leads_loja l on l.id=('e3120000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid;
insert into public.casos_humanos(id,concessionaria_id,lead_id,ciclo_id)
 select ('e5120000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 c.concessionaria_id,c.lead_id,c.id
 from generate_series(1,2) i
 join public.ciclos_comerciais c on c.id=('e4120000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid;
insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id)
 select concessionaria_id,id,'e1120000-0000-4000-8000-000000000003'
 from public.casos_humanos where id::text like 'e5120000-%';
select id::text as prev_a from public.atribuicoes_humanas
 where caso_id='e5120000-0000-4000-8000-000000000001'
 and encerrada_em is null \gset
select id::text as prev_b from public.atribuicoes_humanas
 where caso_id='e5120000-0000-4000-8000-000000000002'
 and encerrada_em is null \gset
select pg_catalog.set_config('s1.test.prev_a', :'prev_a',true);
select pg_catalog.set_config('s1.test.prev_b', :'prev_b',true);
\echo 'PASS S1S-01: fixtures de duas lojas e duas equipes criadas'

do $t$ begin
 if not pg_catalog.has_function_privilege(
  'authenticated','prumo_private.s1_mover_atendimento_sessao(uuid,uuid,uuid,uuid)','EXECUTE')
 or not pg_catalog.has_function_privilege(
  'authenticated','prumo_private.s1_pausar_operador_sessao(uuid,text)','EXECUTE')
 or not pg_catalog.has_function_privilege(
  'authenticated','prumo_private.s1_reativar_operador_sessao(uuid)','EXECUTE')
 or pg_catalog.has_function_privilege(
  'anon','prumo_private.s1_mover_atendimento_sessao(uuid,uuid,uuid,uuid)','EXECUTE')
 or pg_catalog.has_function_privilege(
  'service_role','prumo_private.s1_pausar_operador_sessao(uuid,text)','EXECUTE')
 then raise exception 'S1S-02 grants errados';end if;
end $t$;
\echo 'PASS S1S-02: somente authenticated pode chamar as 3 fachadas privadas'

set local role authenticated;
do $t$ begin
 begin
  perform prumo_private.s1_pausar_operador_sessao(
    'e1120000-0000-4000-8000-000000000003','AUSENCIA_TEMPORARIA');
  raise exception 'S1S-03 sem JWT role aceito';
 exception when insufficient_privilege then null;end;
end $t$;
\echo 'PASS S1S-03: ausencia do papel da sessao e rejeitada'

select pg_catalog.set_config('request.jwt.claim.role','authenticated',true);
do $t$ begin
 begin
  perform prumo_private.s1_pausar_operador_sessao(
    'e1120000-0000-4000-8000-000000000003','AUSENCIA_TEMPORARIA');
  raise exception 'S1S-04 sessao sem sub aceita';
 exception when insufficient_privilege then null;end;
end $t$;
\echo 'PASS S1S-04: ausencia de identidade e rejeitada'

select pg_catalog.set_config('request.jwt.claim.sub',
 'e1120000-0000-4000-8000-000000000005',true);
do $t$ begin
 begin
  perform prumo_private.s1_pausar_operador_sessao(
    'e1120000-0000-4000-8000-000000000003','AUSENCIA_TEMPORARIA');
  raise exception 'S1S-05 operador alheio pausou O3';
 exception when insufficient_privilege then null;end;
end $t$;
\echo 'PASS S1S-05: operador nao supervisionado nao pausa pessoa alheia'

select pg_catalog.set_config('request.jwt.claim.sub',
 'e1120000-0000-4000-8000-000000000001',true);
select prumo_private.s1_mover_atendimento_sessao(
 'e2120000-0000-4000-8000-000000000001',
 'e5120000-0000-4000-8000-000000000001',
 :'prev_a'::uuid,'e1120000-0000-4000-8000-000000000004');
reset role;
do $t$ begin
 if (select count(*) from prumo_private.s1_movimentos_manuais_historico h
   where h.caso_id='e5120000-0000-4000-8000-000000000001'
   and h.solicitante_id='e1120000-0000-4000-8000-000000000001')<>1
 or (select count(*) from public.atribuicoes_humanas a
  where a.caso_id='e5120000-0000-4000-8000-000000000001'
  and a.operador_id='e1120000-0000-4000-8000-000000000004'
  and a.encerrada_em is null)<>1
 then raise exception 'S1S-06 identidade nao vinculada a movimento';end if;
end $t$;
\echo 'PASS S1S-06: autoria extraida de auth.uid, novo titular unico A'

set local role authenticated;
select pg_catalog.set_config('request.jwt.claim.sub',
 'e1120000-0000-4000-8000-000000000002',true);
do $t$ begin
 begin
  perform prumo_private.s1_mover_atendimento_sessao(
   'e2120000-0000-4000-8000-000000000002',
   'e5120000-0000-4000-8000-000000000002',
   pg_catalog.current_setting('s1.test.prev_b')::uuid,'e1120000-0000-4000-8000-000000000005');
  raise exception 'S1S-07 gestor B obteve O3';
 exception when insufficient_privilege then null;end;
end $t$;
\echo 'PASS S1S-07: gestor de outra equipe nao toma casos da origem'
select pg_catalog.set_config('request.jwt.claims',
 '{"user_metadata":{"papel":"responsavel","can_admin":true},"app_metadata":{"papel":"responsavel"}}',true);
do $t$ begin
 begin
  perform prumo_private.s1_pausar_operador_sessao(
   'e1120000-0000-4000-8000-000000000003','AUSENCIA_TEMPORARIA');
  raise exception 'S1S-08 metadados deram permissao de gestor';
 exception when insufficient_privilege then null;end;
end $t$;
\echo 'PASS S1S-08: papel forged em metadata nao altera autorizacao de equipe'

select pg_catalog.set_config('request.jwt.claim.sub',
 'e1120000-0000-4000-8000-000000000001',true);
select prumo_private.s1_pausar_operador_sessao(
 'e1120000-0000-4000-8000-000000000003','AUSENCIA_TEMPORARIA');
reset role;
do $t$ begin
 if (select count(*) from prumo_private.s1_pausas_operadores_historico
  where solicitante_id='e1120000-0000-4000-8000-000000000001'
   and operador_id='e1120000-0000-4000-8000-000000000003'
   and acao='PAUSA_GLOBAL')<>1
 or (select count(*) from public.atribuicoes_humanas
  where operador_id='e1120000-0000-4000-8000-000000000003'
   and encerrada_em is null)<>0
 or (select count(*) from public.vinculos_papel_escopo
  where ator_id='e1120000-0000-4000-8000-000000000003')<>2
 then raise exception 'S1S-09 pausa nao foi global ou removendo grants';end if;
end $t$;
\echo 'PASS S1S-09: pausa global com autoria da sessao, grants A/B mantidos'

set local role authenticated;
select pg_catalog.set_config('request.jwt.claim.sub',
 'e1120000-0000-4000-8000-000000000002',true);
do $t$ begin
 begin
  perform prumo_private.s1_reativar_operador_sessao(
   'e1120000-0000-4000-8000-000000000003');
  raise exception 'S1S-10 outro gestor reativou O3';
 exception when insufficient_privilege then null;end;
end $t$;
\echo 'PASS S1S-10: outro gestor nao reativa membro alheio'

select pg_catalog.set_config('request.jwt.claim.sub',
 'e1120000-0000-4000-8000-000000000001',true);
select prumo_private.s1_reativar_operador_sessao(
 'e1120000-0000-4000-8000-000000000003');
reset role;
do $t$ begin
 if (select count(*) from prumo_private.s1_pausas_operadores_historico
  where solicitante_id='e1120000-0000-4000-8000-000000000001'
   and operador_id='e1120000-0000-4000-8000-000000000003')<>2
 or (select estado from public.equipe_prumo_s1
  where ator_id='e1120000-0000-4000-8000-000000000003')<>'ativo'
 or (select count(*) from public.atribuicoes_humanas
  where operador_id='e1120000-0000-4000-8000-000000000003'
   and encerrada_em is null)<>0
 then raise exception 'S1S-11 retorno reatribuiu casos ou autoria incorreta';end if;
end $t$;
\echo 'PASS S1S-11: retorno com autoria, sem tomar carteira antiga'

set local role anon;
do $t$ begin
 begin
  perform prumo_private.s1_pausar_operador_sessao(
   'e1120000-0000-4000-8000-000000000003','AUSENCIA_TEMPORARIA');
  raise exception 'S1S-12 anon invocou definer';
 exception when insufficient_privilege then null;end;
end $t$;
reset role;
set local role service_role;
do $t$ begin
 begin
  perform prumo_private.s1_mover_atendimento_sessao(
   'e2120000-0000-4000-8000-000000000001',
   'e5120000-0000-4000-8000-000000000001',
   pg_catalog.current_setting('s1.test.prev_a')::uuid,'e1120000-0000-4000-8000-000000000003');
  raise exception 'S1S-12 service_role invocou definer';
 exception when insufficient_privilege then null;end;
end $t$;
\echo 'PASS S1S-12: anon/service_role sem EXECUTE nem schema privado'
reset role;

set local role authenticated;
select pg_catalog.set_config('request.jwt.claim.sub',
 'e1120000-0000-4000-8000-000000000001',true);
do $t$ begin
 begin
  perform prumo_private.s1_mover_atendimento_da_equipe(
   'e1120000-0000-4000-8000-000000000006',
   'e2120000-0000-4000-8000-000000000001',
   'e5120000-0000-4000-8000-000000000001',
   pg_catalog.current_setting('s1.test.prev_a')::uuid,'e1120000-0000-4000-8000-000000000003');
  raise exception 'S1S-13 camada transacional interna liberada';
 exception when insufficient_privilege then null;end;
end $t$;
\echo 'PASS S1S-13: authenticated nao chama funcao interna com solicitante informado'
reset role;

do $t$ begin
 if exists(select 1 from pg_catalog.pg_proc p
  where p.pronamespace='public'::regnamespace
   and p.proname in (
    's1_mover_atendimento_sessao','s1_pausar_operador_sessao',
    's1_reativar_operador_sessao'))
 or exists(select 1 from pg_catalog.pg_proc p
  where p.pronamespace='prumo_private'::regnamespace
   and p.proname in (
    's1_mover_atendimento_sessao','s1_pausar_operador_sessao',
    's1_reativar_operador_sessao')
    and pg_catalog.pg_get_function_arguments(p.oid) like '%solicitante%')
 then raise exception 'S1S-14 fachada exposta ou aceita autor parametrizado';end if;
end $t$;
\echo 'PASS S1S-14: sem RPC no schema public nem argumento de identidade do cliente'
rollback;
