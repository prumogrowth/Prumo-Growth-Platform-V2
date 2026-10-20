#!/usr/bin/env bash
# WA14C: PG17 concurrent fixture only. No transport, commercial writes, or ACKs.
set -euo pipefail
: "$PRUMO_TEST_DATABASE_URL"
python3 - <<'PY'
import os,re,sys
from urllib.parse import urlparse,unquote
u=urlparse(os.environ['PRUMO_TEST_DATABASE_URL'])
name=unquote(u.path[1:]) if u.path.startswith('/') else ''
if (u.scheme not in ('postgres','postgresql')
    or u.hostname not in ('localhost','127.0.0.1','::1')
    or not re.fullmatch(r'prumo_s0_test_[a-z0-9_]{1,40}',name)
    or u.query or u.fragment or u.params):
    sys.exit('REFUSED: disposable local PostgreSQL only')
PY
unset PGHOSTADDR PGHOST PGPORT PGDATABASE PGUSER PGSERVICE PGSERVICEFILE PGOPTIONS PGSSLMODE PGSSLCERT PGSSLKEY PGSSLROOTCERT
command -v psql >/dev/null || { echo 'psql unavailable' >&2; exit 69; }
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >/dev/null <<'SQL'
insert into public.concessionarias(id,nome_operacional)
 values('f9200000-0000-4000-8000-000000000001','WA14C fixture');
insert into public.canais_loja(id,concessionaria_id,identificador_emissor)
 values('f9300000-0000-4000-8000-000000000001',
 'f9200000-0000-4000-8000-000000000001','WA14C_CHANNEL');
insert into prumo_private.meta_apps_fixture_s0(app_ref,concessionaria_id)
 values('FIXTURE_WA14C_APP','f9200000-0000-4000-8000-000000000001');
insert into prumo_private.meta_canais_fixture_s0(
 app_ref,concessionaria_id,canal_id,waba_ref,phone_number_ref)
 values('FIXTURE_WA14C_APP','f9200000-0000-4000-8000-000000000001',
 'f9300000-0000-4000-8000-000000000001',
 'FIXTURE_WA14C_WABA','FIXTURE_WA14C_PHONE');
insert into prumo_private.outbox_intencoes_s0(
 id,concessionaria_id,canal_id,contrato,chave_idempotencia,versao_estado_sintetica)
 values('f9400000-0000-4000-8000-000000000001',
 'f9200000-0000-4000-8000-000000000001',
 'f9300000-0000-4000-8000-000000000001','C03','WA14C_BLOCKED',1);
SQL
# WA14C-01: independently committed competitor, same scoped ledger.
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$tmp/r01a" 2>"$tmp/r01aerr" <<'SQL' &
begin;
select prumo_private.registrar_vinculo_meta_fixture_s0(
 'FIXTURE_WA14C_APP','f9300000-0000-4000-8000-000000000001',
 'f9400000-0000-4000-8000-000000000001',
 'WA14C_ATTEMPT_A','WA14C_CORR_A','5581900000000','wamid.WA14C.A',200);
select pg_sleep(1);
commit;
SQL
one=$!
sleep 0.2
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$tmp/r01b" 2>"$tmp/r01berr" <<'SQL' &
select prumo_private.registrar_vinculo_meta_fixture_s0(
 'FIXTURE_WA14C_APP','f9300000-0000-4000-8000-000000000001',
 'f9400000-0000-4000-8000-000000000001',
 'WA14C_ATTEMPT_A','WA14C_CORR_A','5581900000000','wamid.WA14C.A_ALT',200);
SQL
two=$!
wait "$one"
grep -q 'LAB_BOUND' "$tmp/r01a"
if wait "$two"; then echo 'FAIL WA14C-01: conflicting claim accepted' >&2; exit 1; fi
grep -q 'CONFLICT_TECHNICAL_BINDING' "$tmp/r01berr"
echo 'PASS WA14C-01: two-session scoped invariant'
# WA14C-02: independently committed competitor, same scoped ledger.
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$tmp/r02a" 2>"$tmp/r02aerr" <<'SQL' &
begin;
select prumo_private.registrar_vinculo_meta_fixture_s0(
 'FIXTURE_WA14C_APP','f9300000-0000-4000-8000-000000000001',
 'f9400000-0000-4000-8000-000000000001',
 'WA14C_ATTEMPT_B','WA14C_CORR_B','5581900000000','wamid.WA14C.B',200);
select pg_sleep(1);
commit;
SQL
one=$!
sleep 0.2
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$tmp/r02b" 2>"$tmp/r02berr" <<'SQL' &
select prumo_private.registrar_vinculo_meta_fixture_s0(
 'FIXTURE_WA14C_APP','f9300000-0000-4000-8000-000000000001',
 'f9400000-0000-4000-8000-000000000001',
 'WA14C_ATTEMPT_B_OTHER','WA14C_CORR_B_OTHER','5581900000000','wamid.WA14C.B',200);
SQL
two=$!
wait "$one"
grep -q 'LAB_BOUND' "$tmp/r02a"
if wait "$two"; then echo 'FAIL WA14C-02: conflicting claim accepted' >&2; exit 1; fi
grep -q 'CONFLICT_TECHNICAL_BINDING' "$tmp/r02berr"
echo 'PASS WA14C-02: two-session scoped invariant'
# WA14C-03: independently committed competitor, same scoped ledger.
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$tmp/r03a" 2>"$tmp/r03aerr" <<'SQL' &
begin;
select prumo_private.registrar_vinculo_meta_fixture_s0(
 'FIXTURE_WA14C_APP','f9300000-0000-4000-8000-000000000001',
 'f9400000-0000-4000-8000-000000000001',
 'WA14C_ATTEMPT_C','WA14C_CORR_C','5581900000000','wamid.WA14C.C',200);
select pg_sleep(1);
commit;
SQL
one=$!
sleep 0.2
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$tmp/r03b" 2>"$tmp/r03berr" <<'SQL' &
select prumo_private.registrar_vinculo_meta_fixture_s0(
 'FIXTURE_WA14C_APP','f9300000-0000-4000-8000-000000000001',
 'f9400000-0000-4000-8000-000000000001',
 'WA14C_ATTEMPT_C','WA14C_CORR_C','5581900000000','wamid.WA14C.C',200);
SQL
two=$!
wait "$one"
grep -q 'LAB_BOUND' "$tmp/r03a"
wait "$two"
grep -q 'LAB_REPLAY' "$tmp/r03b"
echo 'PASS WA14C-03: two-session scoped invariant'
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >/dev/null <<'SQL'
do $wa14_conc$
declare n integer; recovered jsonb;
begin
 select count(*) into n from prumo_private.meta_vinculos_tentativa_fixture_s0
 where app_ref='FIXTURE_WA14C_APP';
 if n<>3 then raise exception 'FAIL WA14C: expected 3 immutable winner rows';end if;
 if exists (select 1 from prumo_private.meta_vinculos_tentativa_fixture_s0
   where app_ref='FIXTURE_WA14C_APP'
   and provider_message_id not in ('wamid.WA14C.A','wamid.WA14C.B','wamid.WA14C.C'))
 then raise exception 'FAIL WA14C: wrong wamid survived';end if;
 recovered:=prumo_private.consultar_vinculo_meta_fixture_s0(
  'FIXTURE_WA14C_APP','f9300000-0000-4000-8000-000000000001',
  'f9400000-0000-4000-8000-000000000001',
  'WA14C_ATTEMPT_C','WA14C_CORR_C','5581900000000','wamid.WA14C.C');
 if recovered->>'outcome'<>'LAB_FOUND_EXACT'
  or (recovered->>'retry_external')::boolean then
  raise exception 'FAIL WA14C: read-only exact recovery';end if;
end $wa14_conc$;
SQL
echo 'PASS WA14C: 3 confirmed rows, no blind retry'
