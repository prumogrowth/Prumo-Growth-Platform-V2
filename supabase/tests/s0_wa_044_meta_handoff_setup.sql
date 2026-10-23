\set ON_ERROR_STOP on
-- WA40 disposable fixture, deliberately COMMITTED for Python PG17 race checks.
-- This fixture is run only by protected S0 CI (never production).
insert into public.concessionarias(id,nome_operacional)
values('f7200000-0000-4000-8000-000000000001','WA40 shop A'),
 ('f7200000-0000-4000-8000-000000000002','WA40 shop B');
insert into public.canais_loja(id,concessionaria_id,identificador_emissor)
values('f7300000-0000-4000-8000-000000000001',
       'f7200000-0000-4000-8000-000000000001','WA40_A'),
 ('f7300000-0000-4000-8000-000000000002',
  'f7200000-0000-4000-8000-000000000002','WA40_B');
insert into prumo_private.meta_apps_fixture_s0
 (app_ref,concessionaria_id,app_technical_ref)
values('FIXTURE_WA40_A','f7200000-0000-4000-8000-000000000001',
 '12346000001'),('FIXTURE_WA40_B','f7200000-0000-4000-8000-000000000002',
 '12346000002');
insert into prumo_private.meta_canais_fixture_s0
 (app_ref,concessionaria_id,canal_id,waba_ref,phone_number_ref,
  waba_technical_ref,phone_technical_ref)
values('FIXTURE_WA40_A','f7200000-0000-4000-8000-000000000001',
 'f7300000-0000-4000-8000-000000000001',
 'FIXTURE_WA40_WABA_A','FIXTURE_WA40_PHONE_A','22346000001','32346000001'),
 ('FIXTURE_WA40_B','f7200000-0000-4000-8000-000000000002',
 'f7300000-0000-4000-8000-000000000002',
 'FIXTURE_WA40_WABA_B','FIXTURE_WA40_PHONE_B','22346000002','32346000002');
insert into prumo_private.outbox_intencoes_s0
 (id,concessionaria_id,canal_id,contrato,chave_idempotencia,
 versao_estado_sintetica)
values('f7400000-0000-4000-8000-000000000001',
 'f7200000-0000-4000-8000-000000000001',
 'f7300000-0000-4000-8000-000000000001','C03','WA40_A',1),
 ('f7400000-0000-4000-8000-000000000002',
 'f7200000-0000-4000-8000-000000000002',
 'f7300000-0000-4000-8000-000000000002','C03','WA40_B',1);
select prumo_private.registrar_vinculo_meta_tecnico_fixture_s0(
 '12346000001','22346000001','32346000001',
 'f7300000-0000-4000-8000-000000000001',
 'f7400000-0000-4000-8000-000000000001',
 'ATTEMPT_A','CORR_A','5581900000000','wamid.WA40.SHARED',200);
select prumo_private.registrar_vinculo_meta_tecnico_fixture_s0(
 '12346000002','22346000002','32346000002',
 'f7300000-0000-4000-8000-000000000002',
 'f7400000-0000-4000-8000-000000000002',
 'ATTEMPT_B','CORR_B','5581900000000','wamid.WA40.SHARED',200);
insert into prumo_private.meta_servico_chaves_fixture_s0(
 chave_id,app_technical_ref,segredo,valido_desde,valido_ate,ativo)
values('f7500000-0000-4000-8000-000000000001','12346000001',
 decode(repeat('53',48),'hex'),clock_timestamp()-interval '60 seconds',
 clock_timestamp()+interval '2 hours',true),
 ('f7500000-0000-4000-8000-000000000002','12346000002',
 decode(repeat('54',48),'hex'),clock_timestamp()-interval '60 seconds',
 clock_timestamp()+interval '2 hours',true);
