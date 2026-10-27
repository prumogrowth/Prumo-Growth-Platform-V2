#!/usr/bin/env bash
set -euo pipefail
: "$PRUMO_TEST_DATABASE_URL"
python3 - <<'PY'
from urllib.parse import urlparse,unquote
import os,sys
u=urlparse(os.environ['PRUMO_TEST_DATABASE_URL'])
if u.scheme not in ('postgres','postgresql') or u.hostname not in ('localhost','127.0.0.1','::1') or not unquote(u.path.strip('/')).startswith('prumo_s0_test_'):
 sys.exit('RECUSADO: apenas banco LOCAL de teste prumo_s0_test_*')
PY
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >/dev/null <<'SQL'
insert into public.concessionarias(id,nome_operacional)
values('b2000000-0000-4000-8000-000000000001','C02 concorrencia ficticia');
insert into public.canais_loja(id,concessionaria_id,identificador_emissor)
values('b3000000-0000-4000-8000-000000000001',
'b2000000-0000-4000-8000-000000000001','EMISSOR_C02_CONCORRENTE');
SQL
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

# Duas chamadas em conexoes separadas com o mesmo ID externo.
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$tmp/first" <<'SQL' &
begin;
select prumo_private.receber_mensagem_sintetica(
'b3000000-0000-4000-8000-000000000001','+5581999991000','DUP1','Texto sintetico duplicado');
select pg_sleep(1);
commit;
SQL
one=$!
sleep 0.15
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$tmp/second" <<'SQL' &
select prumo_private.receber_mensagem_sintetica(
'b3000000-0000-4000-8000-000000000001','+5581999991000','DUP1','Texto sintetico duplicado');
SQL
two=$!
wait "$one"
wait "$two"
grep -q '"outcome": "APPLIED"' "$tmp/first"
grep -q '"outcome": "ALREADY_APPLIED"' "$tmp/second"

# Duas mensagens distintas do mesmo cliente nao criam duas conversas/ciclos.
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$tmp/third" <<'SQL' &
select prumo_private.receber_mensagem_sintetica(
'b3000000-0000-4000-8000-000000000001','+5581999991000','NEW2','Mensagem ficticia dois');
SQL
three=$!
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$tmp/fourth" <<'SQL' &
select prumo_private.receber_mensagem_sintetica(
'b3000000-0000-4000-8000-000000000001','+5581999991000','NEW3','Mensagem ficticia tres');
SQL
four=$!
wait "$three"
wait "$four"
grep -q '"outcome": "APPLIED"' "$tmp/third"
grep -q '"outcome": "APPLIED"' "$tmp/fourth"

psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >/dev/null <<'SQL'
do $verify$
begin
 if (select count(*) from public.leads_loja
  where concessionaria_id='b2000000-0000-4000-8000-000000000001')<>1
 or (select count(*) from public.ciclos_comerciais
  where concessionaria_id='b2000000-0000-4000-8000-000000000001')<>1
 or (select count(*) from public.conversas
  where concessionaria_id='b2000000-0000-4000-8000-000000000001')<>1
 or (select count(*) from public.mensagens
  where concessionaria_id='b2000000-0000-4000-8000-000000000001')<>3
 or (select count(*) from public.eventos_status_comercial
  where concessionaria_id='b2000000-0000-4000-8000-000000000001')<>1
 then raise exception 'FAIL: concorrencia C02 gerou duplicacao de lead/ciclo/conversa/evento'; end if;
end $verify$;
SQL
echo 'PASS C02-CONC: webhook repetido e dois eventos distintos em paralelo sem duplicacoes'
