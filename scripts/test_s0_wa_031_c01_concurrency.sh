#!/usr/bin/env bash
set -euo pipefail
: "$PRUMO_TEST_DATABASE_URL"
python3 - <<'PY'
import os,sys
from urllib.parse import urlparse,unquote
u=urlparse(os.environ['PRUMO_TEST_DATABASE_URL'])
if u.scheme not in ('postgres','postgresql') or u.hostname not in ('localhost','127.0.0.1','::1') or not unquote((u.path or '').strip('/')).startswith('prumo_s0_test_'):
 sys.exit('REFUSED: only localhost disposable prumo_s0_test_*')
PY
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >/dev/null <<'SQL'
insert into auth.users(id) values
 ('c4110000-0000-4000-8000-000000000001');
insert into public.atores(id) values
 ('c4110000-0000-4000-8000-000000000001');
insert into public.concessionarias(id,nome_operacional) values
 ('c4120000-0000-4000-8000-000000000001','WA31 simultaneous fixture');
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel) values
 ('c4110000-0000-4000-8000-000000000001',
  'c4120000-0000-4000-8000-000000000001','gestor');
insert into public.canais_loja(id,concessionaria_id,identificador_emissor) values
 ('c4130000-0000-4000-8000-000000000001',
  'c4120000-0000-4000-8000-000000000001','WA31_CONCURRENT_EMISSOR');
SQL
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

# C01 insert holds transaction; C02 with opposite number waits for alias lock.
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$tmp/c01" <<'SQL' &
begin;
select prumo_private.importar_lote_identidade_s0(
 'c4110000-0000-4000-8000-000000000001',
 'c4120000-0000-4000-8000-000000000001',
 'WA31-CONC-C01','[{"telefone":"+5581999971234","mobile_confirmado_sintetico":true}]'::jsonb);
select pg_sleep(1);
commit;
SQL
one=$!
sleep 0.2
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$tmp/c02" <<'SQL' &
select prumo_private.receber_mensagem_identidade_s0(
 'c4130000-0000-4000-8000-000000000001',
 '+558199971234','WA31-CONC-C02','C02 durante C01',true);
SQL
two=$!
wait "$one"
wait "$two"
grep -q '"outcome": "APPLIED"' "$tmp/c01"
grep -q '"outcome": "APPLIED"' "$tmp/c02"

# Two distinct batches contend over a different 8/9 canonical contact.
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$tmp/c01a" <<'SQL' &
begin;
select prumo_private.importar_lote_identidade_s0(
 'c4110000-0000-4000-8000-000000000001',
 'c4120000-0000-4000-8000-000000000001',
 'WA31-CONC-BATCH-1','[{"telefone":"+558176543210","mobile_confirmado_sintetico":true}]'::jsonb);
select pg_sleep(1);
commit;
SQL
three=$!
sleep 0.2
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$tmp/c01b" <<'SQL' &
select prumo_private.importar_lote_identidade_s0(
 'c4110000-0000-4000-8000-000000000001',
 'c4120000-0000-4000-8000-000000000001',
 'WA31-CONC-BATCH-2','[{"telefone":"+5581976543210","mobile_confirmado_sintetico":true}]'::jsonb);
SQL
four=$!
wait "$three"
wait "$four"
grep -q '"outcome": "APPLIED"' "$tmp/c01a"
grep -q '"outcome": "APPLIED"' "$tmp/c01b"

psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >/dev/null <<'SQL'
do $verify$
begin
 if (select count(*) from public.leads_loja
    where concessionaria_id='c4120000-0000-4000-8000-000000000001')<>2
 or (select count(*) from public.ciclos_comerciais
    where concessionaria_id='c4120000-0000-4000-8000-000000000001')<>2
 or (select count(*) from prumo_private.aliases_identidade_s0
    where concessionaria_id='c4120000-0000-4000-8000-000000000001')<>4
 or (select count(*) from public.mensagens
    where concessionaria_id='c4120000-0000-4000-8000-000000000001')<>1
 or (select count(*) from public.reencontros_lote
    where concessionaria_id='c4120000-0000-4000-8000-000000000001')<>1
 or (select count(*) from public.itens_lote
    where concessionaria_id='c4120000-0000-4000-8000-000000000001'
    and resultado='aceito')<>3
 then raise exception 'FAIL WA31-CONC: duplicate lead/cycle or lost message';end if;
end $verify$;
SQL
echo 'PASS WA31-CONC: C01/C02 and C01/C01 simultaneous 8-9 use one lead per contact'
