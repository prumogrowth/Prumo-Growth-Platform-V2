\set ON_ERROR_STOP on
-- I51 [D/T], disposable PG17 only. A2 closed by direct decision 23/10/2026.
-- Exercise BOTH manual paths and preserve old-case rights during intake pause.
-- Uses only original S1 I53/I54/I55 laboratory routines, not S0 migrations.
begin;
\ir s1_062_setup_historico_excecao_local_only.sql
-- Manager 1 supervises C2 (existing owner), C3 (no general shop grant)
-- and C6 (normal destination with shop grant); store B is independent.
insert into auth.users(id) values('62110000-0000-4000-8000-000000000006');
insert into public.atores(id) values('62110000-0000-4000-8000-000000000006');
insert into public.equipe_prumo_s1(ator_id,estado)
 values('62110000-0000-4000-8000-000000000006','ativo');
insert into prumo_private.s1_gestor_operadores(gestor_id,operador_id)
 values('62110000-0000-4000-8000-000000000001',
        '62110000-0000-4000-8000-000000000006');
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel)
 values('62110000-0000-4000-8000-000000000001',
        '62220000-0000-4000-8000-000000000002','gestor'),
       ('62110000-0000-4000-8000-000000000006',
        '62220000-0000-4000-8000-000000000002','operador');
insert into prumo_private.s1_disponibilidade_leads_10(operador_id,pausado)
 values('62110000-0000-4000-8000-000000000002',true),
       ('62110000-0000-4000-8000-000000000003',true),
       ('62110000-0000-4000-8000-000000000006',true);
do $a2$
declare olda uuid;err text;
begin
 select id into olda from public.atribuicoes_humanas
 where caso_id='62550000-0000-4000-8000-000000000004'
 and operador_id='62110000-0000-4000-8000-000000000002'
 and encerrada_em is null;
 if olda is null then raise exception 'I51 setup missing original assignment';end if;
 -- Exception path: paused consultant C3 has no general concession grant.
 begin
  perform prumo_private.s1_mover_excecao_caso_55(
   '62110000-0000-4000-8000-000000000001',
   '62220000-0000-4000-8000-000000000002',
   '62550000-0000-4000-8000-000000000004',olda,
   '62110000-0000-4000-8000-000000000003');
  raise exception 'I51 exception path transferred to paused consultant';
 exception when insufficient_privilege then
  get stacked diagnostics err=message_text;
  if err<>'DESTINO_COM_INTAKE_PAUSADO'
  then raise exception 'I51 exception rejected for wrong reason: %',err;end if;
 end;
end
$a2$;
\echo 'PASS I51-01: manual exception-by-case refuses paused consultant with exact A2 reason'

do $a2$
declare olda uuid;err text;
begin
 select id into olda from public.atribuicoes_humanas
 where caso_id='62550000-0000-4000-8000-000000000004'
 and encerrada_em is null;
 -- Normal manual transfer: even with explicit shop grant, paused C6 cannot receive.
 begin
  perform prumo_private.s1_mover_atendimento_da_equipe(
   '62110000-0000-4000-8000-000000000001',
   '62220000-0000-4000-8000-000000000002',
   '62550000-0000-4000-8000-000000000004',olda,
   '62110000-0000-4000-8000-000000000006');
  raise exception 'I51 normal manual path transferred to paused consultant';
 exception when check_violation then
  get stacked diagnostics err=message_text;
  if err<>'NOVOS_LEADS_PAUSADOS'
  then raise exception 'I51 normal path rejected for wrong reason: %',err;end if;
 end;
end
$a2$;
\echo 'PASS I51-02: normal manual route refuses paused destination despite shop grant'

do $a2$
begin
 if (select count(*) from public.atribuicoes_humanas
  where caso_id='62550000-0000-4000-8000-000000000004'
  and encerrada_em is null
  and operador_id='62110000-0000-4000-8000-000000000002')<>1
 or exists(select 1 from public.atribuicoes_humanas
  where caso_id='62550000-0000-4000-8000-000000000004'
  and operador_id in ('62110000-0000-4000-8000-000000000003',
                      '62110000-0000-4000-8000-000000000006'))
 or exists(select 1 from prumo_private.s1_excecoes_55
  where caso_id='62550000-0000-4000-8000-000000000004')
 then raise exception 'I51 denied transfer mutated original case or entitlements';end if;
end
$a2$;
\echo 'PASS I51-03: both denied transfers preserve original owner, history and grants'

-- Paused C2 remains logged in and can respond on own existing case;
-- never infer account suspension from paused intake.
set local role authenticated;
select pg_catalog.set_config('request.jwt.claim.sub',
 '62110000-0000-4000-8000-000000000002',true);
do $a2$
begin
 if (select count(*) from public.casos_humanos
  where id='62550000-0000-4000-8000-000000000004')<>1
 or (select count(*) from public.mensagens
  where caso_id='62550000-0000-4000-8000-000000000004')<1
 then raise exception 'I51 pause removed existing case or messages';end if;
end
$a2$;
insert into public.mensagens(
 concessionaria_id,conversa_id,canal_id,caso_id,direcao,origem,
 conteudo_sintetico,enviada_por)
 values(
 '62220000-0000-4000-8000-000000000002',
 '62770000-0000-4000-8000-000000000004',
 '62660000-0000-4000-8000-000000000002',
 '62550000-0000-4000-8000-000000000004',
 'saida','simulado','I51 resposta em caso antigo apos pausa',
 '62110000-0000-4000-8000-000000000002');
reset role;
\echo 'PASS I51-04: intake pause does not revoke existing-case access and reply'

-- Reactivation makes NEW manual transfer possible; no retroactive handoff.
update prumo_private.s1_disponibilidade_leads_10 set pausado=false,
 versao=versao+1 where operador_id in (
  '62110000-0000-4000-8000-000000000002',
  '62110000-0000-4000-8000-000000000003',
  '62110000-0000-4000-8000-000000000006');
do $a2$
declare olda uuid;r jsonb;
begin
 select id into olda from public.atribuicoes_humanas
 where caso_id='62550000-0000-4000-8000-000000000004'
 and encerrada_em is null;
 r:=prumo_private.s1_mover_atendimento_da_equipe(
 '62110000-0000-4000-8000-000000000001',
 '62220000-0000-4000-8000-000000000002',
 '62550000-0000-4000-8000-000000000004',olda,
 '62110000-0000-4000-8000-000000000006');
 if r->>'outcome'<>'MOVED'
 or (select count(*) from public.atribuicoes_humanas
  where caso_id='62550000-0000-4000-8000-000000000004'
   and operador_id='62110000-0000-4000-8000-000000000006'
   and encerrada_em is null)<>1
 then raise exception 'I51 resumed normal transfer failed: %',r;end if;
end
$a2$;
\echo 'PASS I51-05: after intake resumes, normal manual handoff may succeed again'

do $a2$
declare olda uuid;r jsonb;
begin
 select id into olda from public.atribuicoes_humanas
 where caso_id='62550000-0000-4000-8000-000000000004'
 and encerrada_em is null;
 r:=prumo_private.s1_mover_excecao_caso_55(
 '62110000-0000-4000-8000-000000000001',
 '62220000-0000-4000-8000-000000000002',
 '62550000-0000-4000-8000-000000000004',olda,
 '62110000-0000-4000-8000-000000000003');
 if r->>'outcome'<>'MOVED_CASE_EXCEPTION'
 or (select count(*) from public.atribuicoes_humanas
  where caso_id='62550000-0000-4000-8000-000000000004'
   and operador_id='62110000-0000-4000-8000-000000000003'
   and encerrada_em is null)<>1
 then raise exception 'I51 resumed exception transfer failed: %',r;end if;
 if exists(select 1 from public.vinculos_papel_escopo
  where ator_id='62110000-0000-4000-8000-000000000003'
  and concessionaria_id='62220000-0000-4000-8000-000000000002')
 then raise exception 'I51 exception granted concession-wide privilege';end if;
end
$a2$;
\echo 'PASS I51-06: resumed exception remains case-scoped and unique-owner'
rollback;
\echo 'I51/A2 6/6 test cases passed in disposable PG17; no S0 product change'
