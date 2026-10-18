#!/usr/bin/env bash
set -euo pipefail
: "$PRUMO_TEST_DATABASE_URL"
python3 - <<'PY'
import os,sys
from urllib.parse import urlparse,unquote
u=urlparse(os.environ["PRUMO_TEST_DATABASE_URL"])
if u.scheme not in ("postgres","postgresql") or u.hostname not in ("localhost","127.0.0.1","::1") or not unquote((u.path or "").strip("/")).startswith("prumo_s0_test_"):
 sys.exit("REFUSED: only disposable localhost prumo_s0_test_*")
PY
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >/dev/null <<'SQL'
insert into public.concessionarias(id,nome_operacional) values
 ('f8a03030-0000-4000-8000-000000000001','WA30 race synthetic');
insert into public.canais_loja(id,concessionaria_id,identificador_emissor) values
 ('f8a03031-0000-4000-8000-000000000001',
 'f8a03030-0000-4000-8000-000000000001','WA30_RACE_CHANNEL');
SQL
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$tmp/eight" <<'SQL' &
begin;
select prumo_private.receber_mensagem_identidade_s0(
'f8a03031-0000-4000-8000-000000000001',
'+558166667777','WA30-8','FIXTURE_EIGHT',true);
select pg_sleep(1);
commit;
SQL
p1=$!
sleep 0.2
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$tmp/nine" <<'SQL' &
select prumo_private.receber_mensagem_identidade_s0(
'f8a03031-0000-4000-8000-000000000001',
'+5581966667777','WA30-9','FIXTURE_NINE',true);
SQL
p2=$!
wait "$p1"
wait "$p2"
grep -q '"outcome": "APPLIED"' "$tmp/eight"
grep -q '"outcome": "APPLIED"' "$tmp/nine"
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >/dev/null <<'SQL'
do $race$
begin
 if (select count(*) from public.leads_loja
  where concessionaria_id='f8a03030-0000-4000-8000-000000000001')<>1
 or (select count(*) from prumo_private.aliases_identidade_s0
  where concessionaria_id='f8a03030-0000-4000-8000-000000000001')<>2
 or (select count(*) from public.mensagens
  where concessionaria_id='f8a03030-0000-4000-8000-000000000001')<>2
 or (select count(*) from public.ciclos_comerciais
  where concessionaria_id='f8a03030-0000-4000-8000-000000000001')<>1
 then raise exception 'FAIL WA30-CONC-01: duplicate lead or missing event';end if;
end $race$;
SQL
echo 'PASS WA30-CONC-01: 8 and 9 concurrent sessions -> one lead, two events'
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >/dev/null <<'SQL'
select prumo_private.aceitar_lote_ingresso_s0(
'f8a03031-0000-4000-8000-000000000001',
jsonb_build_array(jsonb_build_object(
 'event_kind','inbound_message','dedupe_key','WA30-RACE-JOB',
 'payload_fingerprint',repeat('a',64))));
SQL
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$tmp/claim1" <<'SQL' &
begin;
select prumo_private.reservar_ingresso_s0(
'f8a03030-0000-4000-8000-000000000001',
'f8a03031-0000-4000-8000-000000000001',
'f8a03032-0000-4000-8000-000000000001');
select pg_sleep(1);
commit;
SQL
p1=$!
sleep 0.2
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$tmp/claim2" <<'SQL' &
select prumo_private.reservar_ingresso_s0(
'f8a03030-0000-4000-8000-000000000001',
'f8a03031-0000-4000-8000-000000000001',
'f8a03032-0000-4000-8000-000000000002');
SQL
p2=$!
wait "$p1"
wait "$p2"
grep -q '"outcome": "LEASED"' "$tmp/claim1"
grep -q '"outcome": "EMPTY"' "$tmp/claim2"
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >/dev/null <<'SQL'
do $check$
begin
 if (select count(*) from prumo_private.tarefas_ingresso_s0
  where estado='LEASED' and tentativas=1
  and concessionaria_id='f8a03030-0000-4000-8000-000000000001')<>1
 then raise exception 'FAIL WA30-CONC-02 duplicate lease';end if;
end $check$;
update prumo_private.tarefas_ingresso_s0 set lease_ate=clock_timestamp()-interval '1 second'
 where concessionaria_id='f8a03030-0000-4000-8000-000000000001';
do $recovery$
declare r jsonb;v_inbox uuid;
begin
 select inbox_id into v_inbox from prumo_private.tarefas_ingresso_s0
 where concessionaria_id='f8a03030-0000-4000-8000-000000000001';
 r:=prumo_private.reservar_ingresso_s0(
 'f8a03030-0000-4000-8000-000000000001',
 'f8a03031-0000-4000-8000-000000000001',
 'f8a03032-0000-4000-8000-000000000003');
 if r->>'outcome'<>'EMPTY' then raise exception 'FAIL WA30-CONC-03: auto-reclaim expired lease';end if;
 r:=prumo_private.reconciliar_lease_expirado_s0(
 'f8a03030-0000-4000-8000-000000000001',
 'f8a03031-0000-4000-8000-000000000001',
 v_inbox,2,'f8a03033-0000-4000-8000-000000000001','SEM_EFEITO_FIXTURE');
 if r->>'estado'<>'RETRY_PENDING' then raise exception 'FAIL WA30-CONC-03 reviewed recovery';end if;
 update prumo_private.tarefas_ingresso_s0
 set proxima_tentativa_em=clock_timestamp()-interval '1 second'
 where inbox_id=v_inbox;
 r:=prumo_private.reservar_ingresso_s0(
 'f8a03030-0000-4000-8000-000000000001',
 'f8a03031-0000-4000-8000-000000000001',
 'f8a03032-0000-4000-8000-000000000003');
 if r->>'outcome'<>'LEASED' or (r->>'versao')::integer<>4
 or (select count(*) from prumo_private.tarefas_ingresso_s0
  where tentativas=2 and versao=4
    and concessionaria_id='f8a03030-0000-4000-8000-000000000001')<>1
 then raise exception 'FAIL WA30-CONC-03 lease not recovered';end if;
end $recovery$;
SQL
echo 'PASS WA30-CONC-02/03: simultaneous claim + explicitly reviewed recovery, no blind retry'
