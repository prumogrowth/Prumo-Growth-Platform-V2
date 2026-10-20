\set ON_ERROR_STOP on
-- WA16B: extend the already committed WA15C synthetic S0 registry.
-- PostgreSQL-local disposable DB only; no Graph API, HTTP ACK or real lead.
begin;
insert into prumo_private.outbox_intencoes_s0(
 id,concessionaria_id,canal_id,contrato,chave_idempotencia,versao_estado_sintetica
) values
 ('f6400000-0000-4000-8000-000000000003',
  'f6200000-0000-4000-8000-000000000001',
  'f6300000-0000-4000-8000-000000000001','C03','WA16_BEFORE',3),
 ('f6400000-0000-4000-8000-000000000004',
  'f6200000-0000-4000-8000-000000000001',
  'f6300000-0000-4000-8000-000000000001','C03','WA16_AFTER',4);
commit;
\echo PASS WA16P-00: two synthetic blocked intents committed
