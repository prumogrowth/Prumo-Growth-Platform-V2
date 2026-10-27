#!/usr/bin/env bash
set -euo pipefail
: "$PRUMO_TEST_DATABASE_URL"
python3 - <<'PY'
import os,sys
from urllib.parse import urlparse,unquote
u=urlparse(os.environ['PRUMO_TEST_DATABASE_URL'])
if u.scheme not in ('postgres','postgresql') or u.hostname not in ('localhost','127.0.0.1','::1') or not unquote((u.path or '').strip('/')).startswith('prumo_s0_test_'):
 sys.exit('REFUSED: only local disposable prumo_s0_test_*')
PY
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >/dev/null <<'SQL'
insert into public.concessionarias(id,nome_operacional) values
 ('a4300000-0000-4000-8000-000000000001','WA33 concurrency fixture');
insert into public.canais_loja(id,concessionaria_id,identificador_emissor) values
 ('a4310000-0000-4000-8000-000000000001',
  'a4300000-0000-4000-8000-000000000001','WA33-CONCURRENT-SIM');
insert into prumo_private.meta_apps_fixture_s0(app_ref,concessionaria_id) values
 ('FIXTURE_WA33_RACE_APP','a4300000-0000-4000-8000-000000000001');
insert into prumo_private.meta_canais_fixture_s0(
 app_ref,concessionaria_id,canal_id,waba_ref,phone_number_ref) values
 ('FIXTURE_WA33_RACE_APP','a4300000-0000-4000-8000-000000000001',
 'a4310000-0000-4000-8000-000000000001',
 'FIXTURE_WA33_RACE_WABA','FIXTURE_WA33_RACE_PHONE');
select prumo_private.aceitar_lote_multicanal_fixture_s0(
 jsonb_build_array(jsonb_build_object(
 'app_ref','FIXTURE_WA33_RACE_APP','waba_id','FIXTURE_WA33_RACE_WABA',
 'phone_number_id','FIXTURE_WA33_RACE_PHONE',
 'event_kind','inbound_message','provider_message_id','wamid.WA33.RACE',
 'provider_kind','text','provider_timestamp','2026-10-18T10:00:00Z',
 'payload_fixture',jsonb_build_object('fixture_ref','FIXTURE_WA33_RACE_EVENT'))));
select prumo_private.anexar_fixture_c02_s0(
 'a4300000-0000-4000-8000-000000000001',
 'a4310000-0000-4000-8000-000000000001',
 (select id from prumo_private.inbox_eventos_s0 where provider_message_id_s0='wamid.WA33.RACE'),
 '+5581900003333','wamid.WA33.RACE','Mensagem concorrente ficticia',true);
select prumo_private.reservar_ingresso_s0(
 'a4300000-0000-4000-8000-000000000001',
 'a4310000-0000-4000-8000-000000000001',
 'a4320000-0000-4000-8000-000000000001');
SQL
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$tmp/owner" <<'SQL' &
begin;
select prumo_private.aplicar_inbox_c02_s0(
 'a4300000-0000-4000-8000-000000000001',
 'a4310000-0000-4000-8000-000000000001',
 (select id from prumo_private.inbox_eventos_s0 where provider_message_id_s0='wamid.WA33.RACE'),
 'a4320000-0000-4000-8000-000000000001',2);
select pg_sleep(1);
commit;
SQL
one=$!
sleep 0.2
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$tmp/contender" <<'SQL' &
do $race$
begin
 begin
  perform prumo_private.aplicar_inbox_c02_s0(
   'a4300000-0000-4000-8000-000000000001',
   'a4310000-0000-4000-8000-000000000001',
   (select id from prumo_private.inbox_eventos_s0 where provider_message_id_s0='wamid.WA33.RACE'),
   'a4320000-0000-4000-8000-000000000002',2);
  raise exception 'FAIL WA33-CONC-01 contender applied';
 exception when serialization_failure then null;end;
end $race$;
SQL
two=$!
wait "$one"
wait "$two"
grep -q '"outcome": "APPLIED_ATOMIC"' "$tmp/owner"
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >/dev/null <<'SQL'
do $race$
declare v uuid;
begin
 select id into v from prumo_private.inbox_eventos_s0
 where provider_message_id_s0='wamid.WA33.RACE';
 if (select count(*) from public.mensagens where id_externo='wamid.WA33.RACE')<>1
 or (select count(*) from prumo_private.aplicacoes_c02_inbox_s0 where inbox_id=v)<>1
 or (select count(*) from prumo_private.historico_tarefas_ingresso_s0 where inbox_id=v)<>2
 or (select estado from prumo_private.tarefas_ingresso_s0 where inbox_id=v)<>'APPLIED'
 then raise exception 'FAIL WA33-CONC-01: non-atomic or duplicated effect';end if;
end $race$;
SQL
echo 'PASS WA33-CONC-01: two SQL sessions, one C02 message and one durable inbox settlement'
