\set ON_ERROR_STOP on
-- I52: test the NEW canonical S0 assignment INSERT guard, not I53 mocks.
-- Full S0/001–037 + S1/038–053 PG17 stack, disposable transaction.
begin;
insert into auth.users(id) select
 ('76510000-0000-4000-8000-'||pg_catalog.lpad(i::text,12,'0'))::uuid
 from pg_catalog.generate_series(1,4) i;
insert into public.atores(id) select id from auth.users
 where id::text like '76510000-%';
insert into public.equipe_prumo_s1(ator_id,estado) select id,'ativo'
 from public.atores where id::text like '76510000-%';
insert into prumo_private.s1_gestor_operadores(gestor_id,operador_id) values
 ('76510000-0000-4000-8000-000000000001','76510000-0000-4000-8000-000000000002'),
 ('76510000-0000-4000-8000-000000000001','76510000-0000-4000-8000-000000000003');
insert into public.concessionarias(id,nome_operacional)
 values('76520000-0000-4000-8000-000000000001','I52 test shop');
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel)
 values('76510000-0000-4000-8000-000000000002','76520000-0000-4000-8000-000000000001','operador'),
 ('76510000-0000-4000-8000-000000000003','76520000-0000-4000-8000-000000000001','operador');
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado)
 select ('76530000-0000-4000-8000-'||pg_catalog.lpad(i::text,12,'0'))::uuid,
 '76520000-0000-4000-8000-000000000001',
 '+5581888700'||pg_catalog.lpad(i::text,4,'0')
 from pg_catalog.generate_series(1,3) i;
insert into public.ciclos_comerciais(id,concessionaria_id,lead_id,status_comercial)
 select ('76540000-0000-4000-8000-'||pg_catalog.lpad(i::text,12,'0'))::uuid,
 '76520000-0000-4000-8000-000000000001',
 ('76530000-0000-4000-8000-'||pg_catalog.lpad(i::text,12,'0'))::uuid,
 'em atendimento pelo operador' from pg_catalog.generate_series(1,3) i;
insert into public.casos_humanos(id,concessionaria_id,lead_id,ciclo_id)
 select ('76550000-0000-4000-8000-'||pg_catalog.lpad(i::text,12,'0'))::uuid,
 '76520000-0000-4000-8000-000000000001',
 ('76530000-0000-4000-8000-'||pg_catalog.lpad(i::text,12,'0'))::uuid,
 ('76540000-0000-4000-8000-'||pg_catalog.lpad(i::text,12,'0'))::uuid
 from pg_catalog.generate_series(1,3) i;
insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id)
 values('76520000-0000-4000-8000-000000000001',
        '76550000-0000-4000-8000-000000000001',
        '76510000-0000-4000-8000-000000000002'),
       ('76520000-0000-4000-8000-000000000001',
        '76550000-0000-4000-8000-000000000002',
        '76510000-0000-4000-8000-000000000003');
\echo 'PASS I52-01: S0-owned canonical assignments created before intake pause'

do $test$ declare r jsonb;
begin
 r:=prumo_private.s1_definir_intake(
 '76510000-0000-4000-8000-000000000001',
 '76510000-0000-4000-8000-000000000003',true,1);
 if r->>'outcome'<>'INTAKE_PAUSED' or (r->>'version')::int<>2
 or (select estado from public.equipe_prumo_s1
 where ator_id='76510000-0000-4000-8000-000000000003')<>'ativo'
 or (select count(*) from public.atribuicoes_humanas
 where operador_id='76510000-0000-4000-8000-000000000003'
 and encerrada_em is null)<>1
 then raise exception 'I52 pause removed account or old case: %',r;end if;
end $test$;
\echo 'PASS I52-02: versioned intake-only pause preserves original owner/account'

do $test$ declare err text;aid uuid;
begin
 -- Direct INSERT from S0 transactional path must fail closed.
 begin
 insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id)
 values('76520000-0000-4000-8000-000000000001',
        '76550000-0000-4000-8000-000000000003',
        '76510000-0000-4000-8000-000000000003');
 raise exception 'I52 direct assignment wrongly accepted paused target';
 exception when check_violation then
 get stacked diagnostics err=message_text;
 if err<>'DESTINO_COM_INTAKE_PAUSADO' then
  raise exception 'I52 wrong gate: %',err;end if;
 end;
 select id into aid from public.atribuicoes_humanas
 where caso_id='76550000-0000-4000-8000-000000000001' and encerrada_em is null;
 -- Real S1 manual function re-enters the SAME S0 owned canonical table.
 begin
 perform prumo_private.s1_mover_atendimento_da_equipe(
 '76510000-0000-4000-8000-000000000001',
 '76520000-0000-4000-8000-000000000001',
 '76550000-0000-4000-8000-000000000001',aid,
 '76510000-0000-4000-8000-000000000003');
 raise exception 'I52 manual assignment wrongly accepted paused target';
 exception when check_violation then
 get stacked diagnostics err=message_text;
 if err<>'DESTINO_COM_INTAKE_PAUSADO' then
  raise exception 'I52 wrong manual gate: %',err;end if;
 end;
 if (select count(*) from public.atribuicoes_humanas
  where caso_id='76550000-0000-4000-8000-000000000001'
  and operador_id='76510000-0000-4000-8000-000000000002'
  and encerrada_em is null)<>1
 or exists(select 1 from public.atribuicoes_humanas
  where caso_id='76550000-0000-4000-8000-000000000003')
 then raise exception 'I52 denied operations changed owner';end if;
end $test$;
\echo 'PASS I52-03: canonical S0 INSERT and S1 manual transfer both reject paused destination without partial mutation'

do $test$ declare r jsonb;err text;
begin
 r:=prumo_private.s1_definir_intake(
 '76510000-0000-4000-8000-000000000001',
 '76510000-0000-4000-8000-000000000003',true,2);
 if r->>'outcome'<>'ALREADY_APPLIED' or (r->>'version')::int<>2
 then raise exception 'I52 CAS replay wrong: %',r;end if;
 begin
 perform prumo_private.s1_definir_intake(
 '76510000-0000-4000-8000-000000000001',
 '76510000-0000-4000-8000-000000000003',false,1);
 raise exception 'I52 stale version accepted';
 exception when invalid_parameter_value then
  get stacked diagnostics err=message_text;
  if err<>'INTAKE_VERSAO_OBSOLETA' then raise exception 'I52 version: %',err;end if;
 end;
 begin
 perform prumo_private.s1_definir_intake(
 '76510000-0000-4000-8000-000000000004',
 '76510000-0000-4000-8000-000000000003',false,2);
 raise exception 'I52 outsider changed intake';
 exception when insufficient_privilege then null;end;
 if (select count(*) from prumo_private.s1_intake_eventos
  where operador_id='76510000-0000-4000-8000-000000000003')<>1
 then raise exception 'I52 history unexpected';end if;
end $test$;
\echo 'PASS I52-04: strict CAS, outsider denied and one intake audit event'

-- Existing owners continue receiving and answering authorized messages.
insert into public.canais_loja(id,concessionaria_id,identificador_emissor)
 values('76560000-0000-4000-8000-000000000001',
        '76520000-0000-4000-8000-000000000001','i52-local');
insert into public.conversas(id,concessionaria_id,lead_id,canal_id,caso_id)
 values('76570000-0000-4000-8000-000000000001',
 '76520000-0000-4000-8000-000000000001',
 '76530000-0000-4000-8000-000000000002',
 '76560000-0000-4000-8000-000000000001',
 '76550000-0000-4000-8000-000000000002');
set local role authenticated;
select pg_catalog.set_config('request.jwt.claim.sub',
 '76510000-0000-4000-8000-000000000003',true);
do $test$
begin
 if not exists(select 1 from public.casos_humanos
 where id='76550000-0000-4000-8000-000000000002') then
 raise exception 'I52 previous case hidden after pause';end if;
end $test$;
insert into public.mensagens(concessionaria_id,conversa_id,canal_id,caso_id,
 direcao,origem,conteudo_sintetico,enviada_por)
 values('76520000-0000-4000-8000-000000000001',
 '76570000-0000-4000-8000-000000000001',
 '76560000-0000-4000-8000-000000000001',
 '76550000-0000-4000-8000-000000000002',
 'saida','simulado','I52 continued reply despite intake pause',
 '76510000-0000-4000-8000-000000000003');
reset role;
\echo 'PASS I52-05: paused consultant retains original case and can answer'

do $test$ declare r jsonb;aid uuid;
begin
 begin
 perform prumo_private.s1_pausar_operador_da_equipe(
 '76510000-0000-4000-8000-000000000001',
 '76510000-0000-4000-8000-000000000003',
 'AUSENCIA_TEMPORARIA');
 raise exception 'I52 legacy global account suspension accepted';
 exception when insufficient_privilege then null;end;
 r:=prumo_private.s1_definir_intake(
 '76510000-0000-4000-8000-000000000001',
 '76510000-0000-4000-8000-000000000003',false,2);
 if r->>'outcome'<>'INTAKE_RESUMED' then
 raise exception 'I52 resume failed: %',r;end if;
 select id into aid from public.atribuicoes_humanas
 where caso_id='76550000-0000-4000-8000-000000000001' and encerrada_em is null;
 r:=prumo_private.s1_mover_atendimento_da_equipe(
 '76510000-0000-4000-8000-000000000001',
 '76520000-0000-4000-8000-000000000001',
 '76550000-0000-4000-8000-000000000001',aid,
 '76510000-0000-4000-8000-000000000003');
 if r->>'outcome'<>'MOVED' then
  raise exception 'I52 post-resume transfer failed: %',r;end if;
 if (select count(*) from public.atribuicoes_humanas
 where caso_id='76550000-0000-4000-8000-000000000001'
 and encerrada_em is null)<>1 then
  raise exception 'I52 active owner uniqueness lost';end if;
 if (select count(*) from prumo_private.s1_intake_eventos
  where operador_id='76510000-0000-4000-8000-000000000003')<>2 then
  raise exception 'I52 audit history missing';end if;
end $test$;
\echo 'PASS I52-06: legacy global-pause disabled, resumed consultant receives manual transfer with one owner'
rollback;
\echo 'I52 canonical S0/S1 integration: 6/6 PG17 checks passed; local only'
