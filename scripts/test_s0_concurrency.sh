#!/usr/bin/env bash
set -euo pipefail
: "$PRUMO_TEST_DATABASE_URL"
python3 - <<'PY'
from urllib.parse import urlparse, unquote
import os,sys
u=urlparse(os.environ["PRUMO_TEST_DATABASE_URL"])
if u.scheme not in ("postgres","postgresql") or u.hostname not in ("localhost","127.0.0.1","::1") or not unquote(u.path.strip("/")).startswith("prumo_s0_test_"):
    sys.exit("RECUSADO: somente PostgreSQL local prumo_s0_test_*")
PY
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >/dev/null <<'SQL'
insert into auth.users(id) values('93000000-0000-4000-8000-000000000001');
insert into public.atores(id) values('93000000-0000-4000-8000-000000000001');
insert into public.concessionarias(id,nome_operacional) values
 ('93000000-0000-4000-8000-000000000002','Loja concorrente sintética');
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel) values
 ('93000000-0000-4000-8000-000000000001','93000000-0000-4000-8000-000000000002','gestor');
SQL
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$tmp/first" <<'SQL' &
begin;
select prumo_private.importar_lote_sintetico(
 '93000000-0000-4000-8000-000000000001',
 '93000000-0000-4000-8000-000000000002',
 'mesmo-lote-concorrente','[{"telefone":"+5512121212121"}]'::jsonb);
select pg_sleep(1);
commit;
SQL
first_pid=$!
sleep 0.15
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$tmp/second" <<'SQL' &
select prumo_private.importar_lote_sintetico(
 '93000000-0000-4000-8000-000000000001',
 '93000000-0000-4000-8000-000000000002',
 'mesmo-lote-concorrente','[{"telefone":"+5512121212121"}]'::jsonb);
SQL
second_pid=$!
wait "$first_pid"
wait "$second_pid"
grep -q '"outcome": "APPLIED"' "$tmp/first"
grep -q '"outcome": "ALREADY_APPLIED"' "$tmp/second"
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >/dev/null <<'SQL'
do $test$
begin
 if (select count(*) from public.lotes_importacao where chave_importacao='mesmo-lote-concorrente')<>1
    or (select count(*) from public.leads_loja
        where concessionaria_id='93000000-0000-4000-8000-000000000002')<>1
    or (select count(*) from public.ciclos_comerciais
        where concessionaria_id='93000000-0000-4000-8000-000000000002')<>1
    or (select count(*) from public.itens_lote
        where concessionaria_id='93000000-0000-4000-8000-000000000002')<>1
 then raise exception 'FAIL concorrencia de lote: houve duplicacao'; end if;
end $test$;
SQL
echo 'PASS TX-CONC: dois clientes concorrentes, um lote/lead/ciclo/item'
