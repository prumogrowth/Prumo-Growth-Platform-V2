\set ON_ERROR_STOP on
-- S1-002 / issue #10: prova I32 (fase 1) NO postgres local.
begin;
insert into auth.users(id) select ('b2100000-0000-4000-8000-'||pg_catalog.lpad(i::text,12,'0'))::uuid
 from pg_catalog.generate_series(1,6) i;
insert into public.atores(id)
 select id from auth.users where id::text like 'b2100000-%';
insert into public.equipe_prumo_s1(ator_id,estado)
 select id,'ativo' from public.atores where id::text like 'b2100000-%';
insert into prumo_private.s1_gestor_operadores(gestor_id,operador_id) values
 ('b2100000-0000-4000-8000-000000000001','b2100000-0000-4000-8000-000000000003'),
 ('b2100000-0000-4000-8000-000000000001','b2100000-0000-4000-8000-000000000004'),
 ('b2100000-0000-4000-8000-000000000002','b2100000-0000-4000-8000-000000000005');
insert into public.concessionarias(id,nome_operacional) values
 ('b2200000-0000-4000-8000-000000000001','S1 issue10 A'),
 ('b2200000-0000-4000-8000-000000000002','S1 issue10 B');
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel)
 values
 ('b2100000-0000-4000-8000-000000000003','b2200000-0000-4000-8000-000000000001','operador'),
 ('b2100000-0000-4000-8000-000000000003','b2200000-0000-4000-8000-000000000002','operador'),
 ('b2100000-0000-4000-8000-000000000004','b2200000-0000-4000-8000-000000000001','operador'),
 ('b2100000-0000-4000-8000-000000000005','b2200000-0000-4000-8000-000000000001','operador');
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado)
 values
 ('b2300000-0000-4000-8000-000000000001','b2200000-0000-4000-8000-000000000001','+5581999990001'),
 ('b2300000-0000-4000-8000-000000000002','b2200000-0000-4000-8000-000000000002','+5581999990002'),
 ('b2300000-0000-4000-8000-000000000003','b2200000-0000-4000-8000-000000000001','+5581999990003');
insert into public.ciclos_comerciais(id,concessionaria_id,lead_id,status_comercial)
 values
 ('b2400000-0000-4000-8000-000000000001','b2200000-0000-4000-8000-000000000001','b2300000-0000-4000-8000-000000000001','em atendimento pelo operador'),
 ('b2400000-0000-4000-8000-000000000002','b2200000-0000-4000-8000-000000000002','b2300000-0000-4000-8000-000000000002','em atendimento pelo operador'),
 ('b2400000-0000-4000-8000-000000000003','b2200000-0000-4000-8000-000000000001','b2300000-0000-4000-8000-000000000003','em atendimento pelo operador');
insert into public.casos_humanos(id,concessionaria_id,lead_id,ciclo_id)
 values
 ('b2500000-0000-4000-8000-000000000001','b2200000-0000-4000-8000-000000000001','b2300000-0000-4000-8000-000000000001','b2400000-0000-4000-8000-000000000001'),
 ('b2500000-0000-4000-8000-000000000002','b2200000-0000-4000-8000-000000000002','b2300000-0000-4000-8000-000000000002','b2400000-0000-4000-8000-000000000002'),
 ('b2500000-0000-4000-8000-000000000003','b2200000-0000-4000-8000-000000000001','b2300000-0000-4000-8000-000000000003','b2400000-0000-4000-8000-000000000003');
insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id)
 values
 ('b2200000-0000-4000-8000-000000000001','b2500000-0000-4000-8000-000000000001','b2100000-0000-4000-8000-000000000003'),
 ('b2200000-0000-4000-8000-000000000002','b2500000-0000-4000-8000-000000000002','b2100000-0000-4000-8000-000000000003');
\echo 'PASS ISSUE10-01: duas equipes, operador com A/B, casos historicos preservados'
do $t$ declare r jsonb; begin
 r:=prumo_private.s1_definir_disponibilidade_leads_10(
  'b2100000-0000-4000-8000-000000000001',
  'b2100000-0000-4000-8000-000000000003',true,1);
 if r->>'outcome'<>'INTAKE_PAUSED' or (r->>'version')::int<>2
  or r->>'redistribution'<>'DEFERRED_S0_PROOF'
  or (select estado from public.equipe_prumo_s1
      where ator_id='b2100000-0000-4000-8000-000000000003')<>'ativo'
 then raise exception 'ISSUE10-02 pause alterou conta: %',r;end if;
end $t$;
\echo 'PASS ISSUE10-02: pausa so intake, estado de conta ativo, sem motivo'
do $t$ begin
 if (select count(*) from public.atribuicoes_humanas a
     where a.operador_id='b2100000-0000-4000-8000-000000000003'
      and a.encerrada_em is null)<>2
 or (select count(*) from public.vinculos_papel_escopo v
     where v.ator_id='b2100000-0000-4000-8000-000000000003')<>2
 or exists(select 1 from prumo_private.s1_remanejamento_pendencias q
           where q.caso_id in ('b2500000-0000-4000-8000-000000000001'::uuid,
                               'b2500000-0000-4000-8000-000000000002'::uuid))
 then raise exception 'ISSUE10-03 titular/grants/pendencia alterados';end if;
end $t$;
\echo 'PASS ISSUE10-03: nao ha redistribuicao sem prova S0, caso sem substituto permanece'
do $t$ begin
 begin
  insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id)
   values('b2200000-0000-4000-8000-000000000001',
          'b2500000-0000-4000-8000-000000000003',
          'b2100000-0000-4000-8000-000000000003');
  raise exception 'ISSUE10-04 paused recebeu novo caso';
 exception when check_violation then null;end;
end $t$;
\echo 'PASS ISSUE10-04: nova atribuicao para pausado recusada pelo guard'
do $t$ declare r jsonb;begin
 r:=prumo_private.s1_definir_disponibilidade_leads_10(
  'b2100000-0000-4000-8000-000000000001',
  'b2100000-0000-4000-8000-000000000003',true,2);
 if r->>'outcome'<>'ALREADY_APPLIED' or (r->>'version')::int<>2 then
  raise exception 'ISSUE10-05 replay inesperado %',r;end if;
 begin
  perform prumo_private.s1_definir_disponibilidade_leads_10(
   'b2100000-0000-4000-8000-000000000001',
   'b2100000-0000-4000-8000-000000000003',false,1);
  raise exception 'ISSUE10-05 CAS obsoleto aceito';
 exception when invalid_parameter_value then null;end;
end $t$;
\echo 'PASS ISSUE10-05: replay idempotente e CAS obsoleto recusado'
do $t$ begin
 begin
  perform prumo_private.s1_definir_disponibilidade_leads_10(
   'b2100000-0000-4000-8000-000000000002',
   'b2100000-0000-4000-8000-000000000003',false,2);
  raise exception 'ISSUE10-06 gestor cruzado aceito';
 exception when insufficient_privilege then null;end;
end $t$;
\echo 'PASS ISSUE10-06: gestor de outra equipe nao governa intake'
do $t$ begin
 begin
  perform prumo_private.s1_pausar_operador_da_equipe(
   'b2100000-0000-4000-8000-000000000001',
   'b2100000-0000-4000-8000-000000000003','AUSENCIA_TEMPORARIA');
  raise exception 'ISSUE10-07 caminho antigo pausou conta';
 exception when insufficient_privilege then null;end;
 begin
  perform prumo_private.s1_reativar_operador_da_equipe(
   'b2100000-0000-4000-8000-000000000001',
   'b2100000-0000-4000-8000-000000000003');
  raise exception 'ISSUE10-07 reativacao antiga alterou conta';
 exception when insufficient_privilege then null;end;
end $t$;
\echo 'PASS ISSUE10-07: pausa/retomada legadas desabilitadas, nao suspendem conta'
do $t$ declare r jsonb; begin
 r:=prumo_private.s1_definir_disponibilidade_leads_10(
  'b2100000-0000-4000-8000-000000000001',
  'b2100000-0000-4000-8000-000000000003',false,2);
 if r->>'outcome'<>'INTAKE_RESUMED' or (r->>'version')::int<>3
  or (select count(*) from prumo_private.s1_eventos_disponibilidade_10
       where operador_id='b2100000-0000-4000-8000-000000000003')<>2
 then raise exception 'ISSUE10-08 retomada nao registrada %',r;end if;
end $t$;
\echo 'PASS ISSUE10-08: retorno so intake, evento/versionamento, sem causa ou data'
do $t$ begin
 insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id)
 values('b2200000-0000-4000-8000-000000000001',
        'b2500000-0000-4000-8000-000000000003',
        'b2100000-0000-4000-8000-000000000003');
 if (select count(*) from public.atribuicoes_humanas
  where operador_id='b2100000-0000-4000-8000-000000000003'
   and encerrada_em is null)<>3 then
  raise exception 'ISSUE10-09 novo lead apos resume falhou';end if;
end $t$;
\echo 'PASS ISSUE10-09: novos casos so depois de retomar, casos antigos continuam'
set local role authenticated;
do $t$ begin
 begin
  perform prumo_private.s1_definir_disponibilidade_leads_10(
  'b2100000-0000-4000-8000-000000000001',
  'b2100000-0000-4000-8000-000000000003',true,3);
  raise exception 'ISSUE10-10 RPC indevida para authenticated';
 exception when insufficient_privilege then null;end;
end $t$;
reset role;
\echo 'PASS ISSUE10-10: nenhuma funcao nova exposta a authenticated'
do $t$ begin
 if exists(select 1 from pg_catalog.pg_policies
    where schemaname='public' and tablename='casos_humanos'
    and policyname='s1_10_excecao_geral')
 or exists(select 1 from public.vinculos_papel_escopo
    where ator_id='b2100000-0000-4000-8000-000000000004'
    and concessionaria_id='b2200000-0000-4000-8000-000000000002')
 then raise exception 'ISSUE10-11 concessao geral indevida';end if;
end $t$;
\echo 'PASS ISSUE10-11: excecao manual NAO concede automaticamente toda a loja'
-- I34: fixtures S0 dentro da mesma transacao, nenhuma prova do provedor real.
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado)
 values('b2300000-0000-4000-8000-000000000004',
        'b2200000-0000-4000-8000-000000000001','+5581999990004');
insert into public.ciclos_comerciais(id,concessionaria_id,lead_id,status_comercial)
 values('b2400000-0000-4000-8000-000000000004',
        'b2200000-0000-4000-8000-000000000001',
        'b2300000-0000-4000-8000-000000000004','em atendimento pelo operador');
insert into public.casos_humanos(id,concessionaria_id,lead_id,ciclo_id)
 values('b2500000-0000-4000-8000-000000000004',
        'b2200000-0000-4000-8000-000000000001',
        'b2300000-0000-4000-8000-000000000004',
        'b2400000-0000-4000-8000-000000000004');
insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id)
 values('b2200000-0000-4000-8000-000000000001',
        'b2500000-0000-4000-8000-000000000004',
        'b2100000-0000-4000-8000-000000000003');
do $t$ declare
 a record;r jsonb;
begin
 -- Cliente A: negativa sintética certificada pelo S0.
 select * into a from public.atribuicoes_humanas
 where caso_id='b2500000-0000-4000-8000-000000000001' and encerrada_em is null;
 r:=prumo_private.s0_registrar_contato_humano_fixture_10(
   a.concessionaria_id,a.caso_id,a.id,
   'SEM_INICIO_CONFIRMADO','s0:confirmed:not-started:case1');
 if r->>'outcome'<>'NOT_STARTED_PROVEN' then
  raise exception 'ISSUE10-12 prova nao registrada %',r;end if;
 r:=prumo_private.s0_registrar_contato_humano_fixture_10(
   a.concessionaria_id,a.caso_id,a.id,
   'SEM_INICIO_CONFIRMADO','s0:confirmed:not-started:case1');
 if r->>'outcome'<>'ALREADY_CONFIRMED' then
  raise exception 'ISSUE10-12 replay fonte nao idempotente %',r;end if;
 -- Cliente B: negativa certificada, mas nao ha destino equipe autorizado.
 select * into a from public.atribuicoes_humanas
 where caso_id='b2500000-0000-4000-8000-000000000002' and encerrada_em is null;
 perform prumo_private.s0_registrar_contato_humano_fixture_10(
   a.concessionaria_id,a.caso_id,a.id,
   'SEM_INICIO_CONFIRMADO','s0:confirmed:not-started:case2');
 -- Cliente A terceiro: prova positiva de resposta humana (irreversivel).
 select * into a from public.atribuicoes_humanas
 where caso_id='b2500000-0000-4000-8000-000000000003' and encerrada_em is null;
 perform prumo_private.s0_registrar_contato_humano_fixture_10(
   a.concessionaria_id,a.caso_id,a.id,
   'SEM_INICIO_CONFIRMADO','s0:confirmed:not-started:case3');
 perform prumo_private.s0_registrar_contato_humano_fixture_10(
   a.concessionaria_id,a.caso_id,a.id,
   'INICIADO','s0:human:confirmed-response:case3');
end $t$;
\echo 'PASS ISSUE10-12: prova S0 vinculada a caso+atribuicao, replay e inicio irreversivel'
do $t$ declare r jsonb;begin
 r:=prumo_private.s1_definir_disponibilidade_leads_10(
  'b2100000-0000-4000-8000-000000000001',
  'b2100000-0000-4000-8000-000000000003',true,3);
 if r->>'outcome'<>'INTAKE_PAUSED' or (r->>'version')::int<>4 then
  raise exception 'ISSUE10-13 falha na pausa seletiva %',r;end if;
 if (select count(*) from public.atribuicoes_humanas
   where operador_id='b2100000-0000-4000-8000-000000000003'
     and encerrada_em is null)<>4 then
  raise exception 'ISSUE10-13 redistribuicao prematura';end if;
end $t$;
\echo 'PASS ISSUE10-13: pausa nao redistribui automaticamente sem reconciliacao S0'
do $t$ declare r jsonb;begin
 r:=prumo_private.s1_redistribuir_pausado_provas_10(
  'b2100000-0000-4000-8000-000000000001',
  'b2100000-0000-4000-8000-000000000003',4);
 if r->>'outcome'<>'RECONCILED' or (r->>'redistributed')::integer<>1
    or (r->>'kept_no_eligible')::integer<>1
    or (r->>'kept_started')::integer<>1
    or (r->>'kept_without_proof')::integer<>1 then
  raise exception 'ISSUE10-14 resultado de reconciliacao diferente %',r;end if;
end $t$;
\echo 'PASS ISSUE10-14: seletivo: 1 transferido, 1 sem destino, 1 iniciado, 1 sem prova'
do $t$ begin
 if not exists(select 1 from public.atribuicoes_humanas a
  where a.caso_id='b2500000-0000-4000-8000-000000000001'
   and a.operador_id='b2100000-0000-4000-8000-000000000004'
   and a.encerrada_em is null)
 or (select count(*) from public.atribuicoes_humanas a
     where a.caso_id='b2500000-0000-4000-8000-000000000001'
       and a.encerrada_em is null)<>1
 or (select count(*) from prumo_private.s1_movimentos_pause_10)<>1 then
  raise exception 'ISSUE10-15 titular unico / destino da mesma equipe ausente';end if;
end $t$;
\echo 'PASS ISSUE10-15: atribuido somente ao outro da mesma equipe, 1 titular e trilha'
do $t$ begin
 if not exists(select 1 from public.atribuicoes_humanas a
 where a.caso_id='b2500000-0000-4000-8000-000000000002'
  and a.operador_id='b2100000-0000-4000-8000-000000000003'
  and a.encerrada_em is null)
 or (select count(*) from public.atribuicoes_humanas a
 where a.operador_id='b2100000-0000-4000-8000-000000000005'
  and a.encerrada_em is null)>0 then
  raise exception 'ISSUE10-16 perdeu caso B ou moveu outra equipe';end if;
end $t$;
\echo 'PASS ISSUE10-16: sem substituto com grant da loja B mantem titular (sem cross-team)'
do $t$ begin
 if (select count(*) from public.atribuicoes_humanas a
     where a.caso_id in (
      'b2500000-0000-4000-8000-000000000003'::uuid,
      'b2500000-0000-4000-8000-000000000004'::uuid)
       and a.operador_id='b2100000-0000-4000-8000-000000000003'
       and a.encerrada_em is null)<>2 then
  raise exception 'ISSUE10-17 iniciado/unknown perderam titular';end if;
end $t$;
\echo 'PASS ISSUE10-17: iniciado e caso desconhecido permanecem no titular original'
do $t$ declare r jsonb;begin
 r:=prumo_private.s1_redistribuir_pausado_provas_10(
  'b2100000-0000-4000-8000-000000000001',
  'b2100000-0000-4000-8000-000000000003',4);
 if (r->>'redistributed')::integer<>0
   or (select count(*) from prumo_private.s1_movimentos_pause_10)<>1
 then raise exception 'ISSUE10-18 replay alterou titularidade %',r;end if;
end $t$;
\echo 'PASS ISSUE10-18: reconciliacao idempotente sem duplicar titular'
do $t$ declare a record;begin
 select * into a from public.atribuicoes_humanas
 where caso_id='b2500000-0000-4000-8000-000000000003' and encerrada_em is null;
 begin
  perform prumo_private.s0_registrar_contato_humano_fixture_10(
    a.concessionaria_id,a.caso_id,a.id,
    'SEM_INICIO_CONFIRMADO','s0:attack:reset-started:case3');
  raise exception 'ISSUE10-19 inicio humano reversivel';
 exception when insufficient_privilege then null;end;
end $t$;
\echo 'PASS ISSUE10-19: prova de humano iniciado e irreversivel'
do $t$ declare a record;begin
 select * into a from public.atribuicoes_humanas
 where caso_id='b2500000-0000-4000-8000-000000000001'
   and encerrada_em is not null limit 1;
 begin
  perform prumo_private.s0_registrar_contato_humano_fixture_10(
   a.concessionaria_id,a.caso_id,a.id,
   'SEM_INICIO_CONFIRMADO','s0:attack:old-assignment:case1');
  raise exception 'ISSUE10-20 prova com atribuicao obsoleta aceita';
 exception when serialization_failure then null;end;
end $t$;
\echo 'PASS ISSUE10-20: evidencias nao se aplicam a atribuicao antiga'
do $t$ begin
 begin
  perform prumo_private.s1_redistribuir_pausado_provas_10(
   'b2100000-0000-4000-8000-000000000002',
   'b2100000-0000-4000-8000-000000000003',4);
  raise exception 'ISSUE10-21 outra equipe executou reconciliacao';
 exception when insufficient_privilege then null;end;
end $t$;
\echo 'PASS ISSUE10-21: chefia cruzada nunca pode redistribuir'
set local role authenticated;
do $t$ begin
 begin
  perform prumo_private.s0_registrar_contato_humano_fixture_10(
   'b2200000-0000-4000-8000-000000000001',
   'b2500000-0000-4000-8000-000000000004',
   '00000000-0000-4000-8000-000000000001',
   'SEM_INICIO_CONFIRMADO','s0:attack:from-user');
  raise exception 'ISSUE10-22 usuario produziu prova S0';
 exception when insufficient_privilege then null;end;
 begin
  perform prumo_private.s1_redistribuir_pausado_provas_10(
   'b2100000-0000-4000-8000-000000000001',
   'b2100000-0000-4000-8000-000000000003',4);
  raise exception 'ISSUE10-22 usuario fez reconciliacao';
 exception when insufficient_privilege then null;end;
end $t$;
reset role;
\echo 'PASS ISSUE10-22: provas S0/reconciliacao inacessiveis a authenticated'
do $t$ declare r jsonb;begin
 r:=prumo_private.s1_definir_disponibilidade_leads_10(
 'b2100000-0000-4000-8000-000000000001',
 'b2100000-0000-4000-8000-000000000003',false,4);
 if r->>'outcome'<>'INTAKE_RESUMED' or (r->>'version')::integer<>5
 then raise exception 'ISSUE10-23 resume %',r;end if;
 begin
  perform prumo_private.s1_redistribuir_pausado_provas_10(
   'b2100000-0000-4000-8000-000000000001',
   'b2100000-0000-4000-8000-000000000003',4);
  raise exception 'ISSUE10-23 reconciliacao apos resume permitida';
 exception when serialization_failure then null;end;
end $t$;
\echo 'PASS ISSUE10-23: retomar pausa invalida reconciliacao de versao antiga'
rollback;
