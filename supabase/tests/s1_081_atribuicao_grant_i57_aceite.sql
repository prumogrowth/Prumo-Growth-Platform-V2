\set ON_ERROR_STOP on
-- I57 5 independent checks in disposable PG17; all data rolled back.
begin;
insert into auth.users(id)
 select ('78910000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid from generate_series(1,3) i;
insert into public.atores(id) select id from auth.users where id::text like '78910000-%';
insert into public.equipe_prumo_s1(ator_id,estado)
 select id,'ativo' from public.atores where id::text like '78910000-%';
insert into prumo_private.s1_gestor_operadores(gestor_id,operador_id)
 values('78910000-0000-4000-8000-000000000001','78910000-0000-4000-8000-000000000002'),
       ('78910000-0000-4000-8000-000000000001','78910000-0000-4000-8000-000000000003');
insert into public.concessionarias(id,nome_operacional)
 values('78920000-0000-4000-8000-000000000001','I57 A'),
       ('78920000-0000-4000-8000-000000000002','I57 B');
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel)
 values('78910000-0000-4000-8000-000000000002','78920000-0000-4000-8000-000000000001','operador'),
       ('78910000-0000-4000-8000-000000000003','78920000-0000-4000-8000-000000000001','operador');
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado)
 values('78930000-0000-4000-8000-000000000001','78920000-0000-4000-8000-000000000001','+5581885700001'),
       ('78930000-0000-4000-8000-000000000002','78920000-0000-4000-8000-000000000001','+5581885700002'),
       ('78930000-0000-4000-8000-000000000003','78920000-0000-4000-8000-000000000002','+5581885700003');
insert into public.ciclos_comerciais(id,concessionaria_id,lead_id,status_comercial)
 select ('78940000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 case when i=3 then '78920000-0000-4000-8000-000000000002'::uuid
 else '78920000-0000-4000-8000-000000000001'::uuid end,
 ('78930000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 'aguardando primeiro disparo' from generate_series(1,3) i;
insert into public.casos_humanos(id,concessionaria_id,lead_id,ciclo_id)
 select ('78950000-0000-4000-8000-'||right(c.id::text,12))::uuid,
 c.concessionaria_id,c.lead_id,c.id from public.ciclos_comerciais c
 where c.id::text like '78940000-%';
insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id)
 values('78920000-0000-4000-8000-000000000001',
        '78950000-0000-4000-8000-000000000001',
        '78910000-0000-4000-8000-000000000002');
\echo 'PASS I57-01: valid shop grant enables canonical assignment'
do $t$ declare v text;begin
 begin
 insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id)
 values('78920000-0000-4000-8000-000000000002',
        '78950000-0000-4000-8000-000000000003',
        '78910000-0000-4000-8000-000000000003');
 raise exception 'I57 CROSS_STORE_ASSIGNED';
 exception when check_violation then
 get stacked diagnostics v=message_text;
 if v<>'S0_DESTINO_SEM_CONCESSAO_ATIVA' then raise exception 'I57 wrong denial %',v;end if;
 end;
end $t$;
\echo 'PASS I57-02: cross-store assignment denied'
select prumo_private.s1_definir_intake(
 '78910000-0000-4000-8000-000000000001',
 '78910000-0000-4000-8000-000000000003',true,1);
do $t$ declare v text;begin
 begin
 insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id)
 values('78920000-0000-4000-8000-000000000001',
        '78950000-0000-4000-8000-000000000002',
        '78910000-0000-4000-8000-000000000003');
 raise exception 'I57 PAUSED_ASSIGNED';
 exception when check_violation then
 get stacked diagnostics v=message_text;
 if v<>'DESTINO_COM_INTAKE_PAUSADO' then raise exception 'I57 wrong A2 %',v;end if;
 end;
end $t$;
\echo 'PASS I57-03: A2 paused intake continues blocking new assignment'
update public.vinculos_papel_escopo set valido_ate=pg_catalog.clock_timestamp()
 where ator_id='78910000-0000-4000-8000-000000000002';
update public.atribuicoes_humanas set encerrada_em=pg_catalog.clock_timestamp()
 where caso_id='78950000-0000-4000-8000-000000000001' and encerrada_em is null;
do $t$ begin
 if (select count(*) from public.atribuicoes_humanas
 where caso_id='78950000-0000-4000-8000-000000000001' and encerrada_em is not null)<>1
 then raise exception 'I57 existing case cannot be closed';end if;
end $t$;
\echo 'PASS I57-04: older assignment may be closed after grant expiry'
do $t$ begin
 if has_function_privilege('authenticated','public.s0_verificar_atribuicao()','EXECUTE')
 or has_function_privilege('anon','public.s0_verificar_atribuicao()','EXECUTE')
 or has_function_privilege('service_role','public.s0_verificar_atribuicao()','EXECUTE')
 or exists(select 1 from public.atribuicoes_humanas
 where caso_id in ('78950000-0000-4000-8000-000000000002',
                   '78950000-0000-4000-8000-000000000003'))
 then raise exception 'I57 unauthorized execution/assignment';end if;
end $t$;
\echo 'PASS I57-05: SQL direct execution denied; failed writes did not mutate cases'
rollback;
\echo 'I57 PG17 5/5 PASS, synthetic and rolled back'
