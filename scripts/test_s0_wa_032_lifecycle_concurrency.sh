#!/usr/bin/env bash
set -euo pipefail
: "$PRUMO_TEST_DATABASE_URL"
python3 - <<'PY'
import os,sys
from urllib.parse import urlparse,unquote
u=urlparse(os.environ['PRUMO_TEST_DATABASE_URL'])
if u.scheme not in ('postgres','postgresql') or u.hostname not in ('localhost','127.0.0.1','::1') or not unquote((u.path or '').strip('/')).startswith('prumo_s0_test_'):
 sys.exit('REFUSED: only disposable local PostgreSQL prumo_s0_test_*')
PY
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >/dev/null <<'SQL'
insert into public.concessionarias(id,nome_operacional) values
 ('a4200000-0000-4000-8000-000000000001','WA32 race fixture');
insert into public.canais_loja(id,concessionaria_id,identificador_emissor) values
 ('a4210000-0000-4000-8000-000000000001',
 'a4200000-0000-4000-8000-000000000001','WA32-RACE-FIXTURE');
select prumo_private.aceitar_lote_ingresso_s0(
 'a4210000-0000-4000-8000-000000000001',
 jsonb_build_array(jsonb_build_object(
  'event_kind','inbound_message','dedupe_key','WA32-RACE-ONLY',
  'payload_fingerprint',repeat('a',64))));
select prumo_private.reservar_ingresso_s0(
 'a4200000-0000-4000-8000-000000000001',
 'a4210000-0000-4000-8000-000000000001',
 'a4220000-0000-4000-8000-000000000001');
SQL
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$tmp/first" <<'SQL' &
begin;
select prumo_private.registrar_resultado_ingresso_s0(
 'a4200000-0000-4000-8000-000000000001',
 'a4210000-0000-4000-8000-000000000001',
 (select id from prumo_private.inbox_eventos_s0 where chave_evento='WA32-RACE-ONLY'),
 'a4220000-0000-4000-8000-000000000001',2,'APLICADO_SINTETICO');
select pg_sleep(1);
commit;
SQL
first=$!
sleep 0.2
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$tmp/second" <<'SQL' &
do $race$
begin
 begin
 perform prumo_private.registrar_resultado_ingresso_s0(
  'a4200000-0000-4000-8000-000000000001',
  'a4210000-0000-4000-8000-000000000001',
  (select id from prumo_private.inbox_eventos_s0 where chave_evento='WA32-RACE-ONLY'),
  'a4220000-0000-4000-8000-000000000002',2,'FALHA_RETRY_SEGURA');
 raise exception 'FAIL WA32-CONC-01 stale worker committed';
 exception when serialization_failure then null; end;
end $race$;
SQL
second=$!
wait "$first"
wait "$second"
grep -q '"estado": "APPLIED"' "$tmp/first"
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >/dev/null <<'SQL'
do $race$
declare v uuid;
begin
 select id into v from prumo_private.inbox_eventos_s0 where chave_evento='WA32-RACE-ONLY';
 if (select count(*) from prumo_private.historico_tarefas_ingresso_s0
  where inbox_id=v)<>2
 or (select estado from prumo_private.tarefas_ingresso_s0 where inbox_id=v)<>'APPLIED'
 then raise exception 'FAIL WA32-CONC-01 lost fencing';end if;
 begin
  perform prumo_private.reconciliar_lease_expirado_s0(
   'a4200000-0000-4000-8000-000000000001',
   'a4210000-0000-4000-8000-000000000001',v,2,
   'a4230000-0000-4000-8000-000000000001','SEM_EFEITO_FIXTURE');
  raise exception 'FAIL WA32-CONC-01 stale recovery accepted';
 exception when serialization_failure then null;end;
end $race$;
SQL
echo 'PASS WA32-CONC-01: competing settlement fenced; no stale worker or recovery'
