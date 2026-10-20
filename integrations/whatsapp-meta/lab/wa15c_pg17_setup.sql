\set ON_ERROR_STOP on
-- WA-15C: disposable PostgreSQL 17 only. Creates synthetic S0 fixture rows.
-- Its COMMIT is intentionally read from two subsequent independent sessions.
begin;
insert into public.concessionarias(id,nome_operacional) values
 ('f6200000-0000-4000-8000-000000000001','WA15C S0 shop A'),
 ('f6200000-0000-4000-8000-000000000002','WA15C S0 shop B');
insert into public.canais_loja(id,concessionaria_id,identificador_emissor) values
 ('f6300000-0000-4000-8000-000000000001','f6200000-0000-4000-8000-000000000001','WA15C_A'),
 ('f6300000-0000-4000-8000-000000000002','f6200000-0000-4000-8000-000000000002','WA15C_B');
insert into prumo_private.meta_apps_fixture_s0(app_ref,concessionaria_id,app_technical_ref) values
 ('FIXTURE_WA15C_APP_A','f6200000-0000-4000-8000-000000000001','12345678912'),
 ('FIXTURE_WA15C_APP_B','f6200000-0000-4000-8000-000000000002','22345678912');
insert into prumo_private.meta_canais_fixture_s0(
 app_ref,concessionaria_id,canal_id,waba_ref,phone_number_ref,
 waba_technical_ref,phone_technical_ref) values
 ('FIXTURE_WA15C_APP_A','f6200000-0000-4000-8000-000000000001',
  'f6300000-0000-4000-8000-000000000001',
  'FIXTURE_WA15C_WABA_A','FIXTURE_WA15C_PHONE_A','33345678912','55545678912'),
 ('FIXTURE_WA15C_APP_B','f6200000-0000-4000-8000-000000000002',
  'f6300000-0000-4000-8000-000000000002',
  'FIXTURE_WA15C_WABA_B','FIXTURE_WA15C_PHONE_B','44445678912','77745678912');
insert into prumo_private.outbox_intencoes_s0(
 id,concessionaria_id,canal_id,contrato,chave_idempotencia,versao_estado_sintetica)
values
 ('f6400000-0000-4000-8000-000000000001',
  'f6200000-0000-4000-8000-000000000001',
  'f6300000-0000-4000-8000-000000000001','C03','WA15C_A',1),
 ('f6400000-0000-4000-8000-000000000002',
  'f6200000-0000-4000-8000-000000000002',
  'f6300000-0000-4000-8000-000000000002','C06','WA15C_B',1);
commit;
\echo PASS WA15C-00: S0 fixture identity and blocked intent committed
