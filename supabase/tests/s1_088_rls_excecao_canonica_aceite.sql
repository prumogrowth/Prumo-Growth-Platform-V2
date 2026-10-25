\set ON_ERROR_STOP on
-- I63 PG17 acceptance: canonical S0 + I61, no historic fixture I55.
-- PG17 tests use auth.uid() GUC per role, all synthetic rows rollback.
begin;
insert into auth.users(id)
 select ('86310000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid
 from generate_series(1,5) i;
insert into public.atores(id) select id from auth.users where id::text like '86310000-%';
insert into public.equipe_prumo_s1(ator_id,estado)
 select id,'ativo' from public.atores where id::text like '86310000-%';
insert into prumo_private.s1_gestor_operadores(gestor_id,operador_id)
 values('86310000-0000-4000-8000-000000000001','86310000-0000-4000-8000-000000000002'),
 ('86310000-0000-4000-8000-000000000001','86310000-0000-4000-8000-000000000003'),
 ('86310000-0000-4000-8000-000000000004','86310000-0000-4000-8000-000000000005');
insert into public.concessionarias(id,nome_operacional)
 values('86320000-0000-4000-8000-000000000001','I63 Shop A'),
 ('86320000-0000-4000-8000-000000000002','I63 Shop B');
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel)
 values('86310000-0000-4000-8000-000000000002','86320000-0000-4000-8000-000000000001','operador'),
 ('86310000-0000-4000-8000-000000000005','86320000-0000-4000-8000-000000000001','operador'),
 ('86310000-0000-4000-8000-000000000005','86320000-0000-4000-8000-000000000002','operador'),
 -- Broad manager grant must NEVER trump restrictive case-specific RLS.
 ('86310000-0000-4000-8000-000000000004','86320000-0000-4000-8000-000000000001','gestor');
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado)
 values('86330000-0000-4000-8000-000000000001','86320000-0000-4000-8000-000000000001','+5581863000001'),
 ('86330000-0000-4000-8000-000000000002','86320000-0000-4000-8000-000000000001','+5581863000002'),
 ('86330000-0000-4000-8000-000000000003','86320000-0000-4000-8000-000000000002','+5581863000003');
insert into public.ciclos_comerciais(id,concessionaria_id,lead_id,status_comercial)
 select ('86340000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 case when i=4 then '86320000-0000-4000-8000-000000000002'::uuid
 else '86320000-0000-4000-8000-000000000001'::uuid end,
 ('86330000-0000-4000-8000-'||lpad((case when i=4 then 3 when i=3 then 2 when i=2 then 1 else i end)::text,12,'0'))::uuid,
 'aguardando primeiro disparo'
 from generate_series(1,4) i;
insert into public.casos_humanos(id,concessionaria_id,lead_id,ciclo_id)
 select ('86350000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 c.concessionaria_id,c.lead_id,c.id
 from public.ciclos_comerciais c
 join generate_series(1,4) i on c.id=
 ('86340000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid;
insert into public.atribuicoes_humanas(id,concessionaria_id,caso_id,operador_id)
 values('86360000-0000-4000-8000-000000000001','86320000-0000-4000-8000-000000000001',
 '86350000-0000-4000-8000-000000000001','86310000-0000-4000-8000-000000000002'),
 ('86360000-0000-4000-8000-000000000003','86320000-0000-4000-8000-000000000001',
 '86350000-0000-4000-8000-000000000003','86310000-0000-4000-8000-000000000005'),
 ('86360000-0000-4000-8000-000000000004','86320000-0000-4000-8000-000000000002',
 '86350000-0000-4000-8000-000000000004','86310000-0000-4000-8000-000000000005');
insert into public.canais_loja(id,concessionaria_id,identificador_emissor)
 values('86370000-0000-4000-8000-000000000001','86320000-0000-4000-8000-000000000001','i63-sim-A'),
 ('86370000-0000-4000-8000-000000000002','86320000-0000-4000-8000-000000000002','i63-sim-B');
insert into public.conversas(id,concessionaria_id,lead_id,canal_id,caso_id)
 values('86380000-0000-4000-8000-000000000001','86320000-0000-4000-8000-000000000001',
 '86330000-0000-4000-8000-000000000001','86370000-0000-4000-8000-000000000001',
 '86350000-0000-4000-8000-000000000001'),
 ('86380000-0000-4000-8000-000000000002','86320000-0000-4000-8000-000000000001',
 '86330000-0000-4000-8000-000000000001','86370000-0000-4000-8000-000000000001',null),
 ('86380000-0000-4000-8000-000000000003','86320000-0000-4000-8000-000000000001',
 '86330000-0000-4000-8000-000000000002','86370000-0000-4000-8000-000000000001',null),
 ('86380000-0000-4000-8000-000000000004','86320000-0000-4000-8000-000000000002',
 '86330000-0000-4000-8000-000000000003','86370000-0000-4000-8000-000000000002',null);
insert into public.mensagens(id,concessionaria_id,conversa_id,canal_id,caso_id,
 direcao,origem,conteudo_sintetico,id_externo)
 select ('86390000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 co.concessionaria_id,co.id,co.canal_id,co.caso_id,'entrada','simulado',
 'i63 test '||i,'i63-pg-'||i
 from generate_series(1,4) i
 join public.conversas co on co.id=
 ('86380000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid;
-- Candidate has not been installed yet: exceptional consultant has no S0 grant.
set local role authenticated;
select set_config('request.jwt.claim.sub','86310000-0000-4000-8000-000000000003',true);
do $t$ begin
 if exists(select 1 from public.casos_humanos where id::text like '86350000-%')
 or exists(select 1 from public.conversas where id::text like '86380000-%')
 then raise exception 'I63 baseline accidentally granted exception';end if;
end $t$;
reset role;
\echo 'PASS I63-01: baseline no-grant consultant does not receive S0 history'
\ir s1_087_rls_excecao_canonica_local_only.sql
set local role authenticated;
select set_config('request.jwt.claim.sub','86310000-0000-4000-8000-000000000003',true);
do $t$ begin
 if exists(select 1 from public.casos_humanos where id::text like '86350000-%')
 or exists(select 1 from public.mensagens where id::text like '86390000-%')
 then raise exception 'I63 no entitlement gave historical read';end if;
end $t$;
reset role;
\echo 'PASS I63-02: candidate RLS does not invent entitlement from team membership'
do $t$ declare j jsonb;begin
 j:=prumo_private.s1_mover_excecao_caso_i61(
 '86310000-0000-4000-8000-000000000001',
 '86320000-0000-4000-8000-000000000001',
 '86350000-0000-4000-8000-000000000001',
 '86360000-0000-4000-8000-000000000001',
 '86310000-0000-4000-8000-000000000003');
 if j->>'outcome'<>'MOVED_CASE_EXCEPTION'
 then raise exception 'I63 canonical transfer %',j;end if;
end $t$;
set local role authenticated;
select set_config('request.jwt.claim.sub','86310000-0000-4000-8000-000000000003',true);
do $t$ begin
 if (select count(*) from public.casos_humanos where id::text like '86350000-%')<>2
 or (select count(*) from public.conversas where id::text like '86380000-%')<>2
 or (select count(*) from public.mensagens where id::text like '86390000-%')<>2
 or (select count(*) from public.atribuicoes_humanas
     where id::text like '86360000-%' and encerrada_em is null)<>0
 then raise exception 'I63 scope after transfer leaked/missed case or pre-case history';end if;
end $t$;
\echo 'PASS I63-03: transfer opens same-lead case and pre-case messages only'
select set_config('request.jwt.claim.sub','86310000-0000-4000-8000-000000000002',true);
do $t$ begin
 if exists(select 1 from public.casos_humanos where id='86350000-0000-4000-8000-000000000001')
 then raise exception 'I63 former consultant kept transferred case';end if;
end $t$;
select set_config('request.jwt.claim.sub','86310000-0000-4000-8000-000000000004',true);
do $t$ begin
 if exists(select 1 from public.casos_humanos where id='86350000-0000-4000-8000-000000000001')
 or not exists(select 1 from public.casos_humanos where id='86350000-0000-4000-8000-000000000003')
 then raise exception 'I63 manager broad shop grant bypassed team gate';end if;
end $t$;
\echo 'PASS I63-04: previous consultant loses case; foreign manager shop grant cannot bypass RLS'
select set_config('request.jwt.claim.sub','86310000-0000-4000-8000-000000000001',true);
do $t$ begin
 if not exists(select 1 from public.casos_humanos where id='86350000-0000-4000-8000-000000000001')
 or exists(select 1 from public.casos_humanos where id='86350000-0000-4000-8000-000000000003')
 then raise exception 'I63 supervisor case history outside team';end if;
end $t$;
\echo 'PASS I63-05: manager supervises participants not unrelated customer or store'
select set_config('request.jwt.claim.sub','86310000-0000-4000-8000-000000000003',true);
do $t$ begin
 begin
 insert into public.mensagens(concessionaria_id,conversa_id,canal_id,
  direcao,origem,conteudo_sintetico,enviada_por)
 values('86320000-0000-4000-8000-000000000001',
 '86380000-0000-4000-8000-000000000002',
 '86370000-0000-4000-8000-000000000001','saida','simulado',
 'i63 forbidden pre-case send','86310000-0000-4000-8000-000000000003');
 raise exception 'I63 pre-case outbound permitted';
 exception when check_violation or insufficient_privilege then null;end;
end $t$;
reset role;
\echo 'PASS I63-06: pre-case read never grants send without a case'
select prumo_private.s1_definir_intake(
 '86310000-0000-4000-8000-000000000001',
 '86310000-0000-4000-8000-000000000003',true,1);
set local role authenticated;
select set_config('request.jwt.claim.sub','86310000-0000-4000-8000-000000000003',true);
do $t$ begin
 if (select count(*) from public.casos_humanos where id::text like '86350000-%')<>2
 then raise exception 'I63 A2 pause removed existing cases';end if;
end $t$;
reset role;
\echo 'PASS I63-07: A2 intake pause retains existing exceptional case/history'
select prumo_private.s1_revogar_excecao_i61(
 '86310000-0000-4000-8000-000000000001',
 (select id from prumo_private.s1_excecoes_caso_i61
   where operador_id='86310000-0000-4000-8000-000000000003' and revogada_em is null));
set local role authenticated;
select set_config('request.jwt.claim.sub','86310000-0000-4000-8000-000000000003',true);
do $t$ begin
 if exists(select 1 from public.casos_humanos where id::text like '86350000-%')
 or exists(select 1 from public.conversas where id::text like '86380000-%')
 or exists(select 1 from public.mensagens where id::text like '86390000-%')
 or exists(select 1 from public.atribuicoes_humanas
            where caso_id='86350000-0000-4000-8000-000000000001')
 then raise exception 'I63 revoked entitlement still reads through same JWT';end if;
end $t$;
reset role;
\echo 'PASS I63-08: same JWT loses case, assignment, history and pre-case messages after revoke'
do $t$ begin
 if (select count(*) from pg_catalog.pg_policies where schemaname='public'
     and policyname like 's1_63_canon_%')<>8
 or (select count(*) from prumo_private.s1_excecoes_caso_eventos_i61
     where evento='REVOGADA' and excecao_id in
      (select id from prumo_private.s1_excecoes_caso_i61
       where operador_id='86310000-0000-4000-8000-000000000003'))<>1
 then raise exception 'I63 candidate/evidence invalid';end if;
end $t$;
\echo 'PASS I63-09: exactly eight local candidate policies, one durable revoke event'
rollback;
\echo 'I63 canonical history RLS PG17 9/9; all rolled back'
