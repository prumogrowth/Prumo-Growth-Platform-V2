#!/usr/bin/env bash
set -euo pipefail
: "$PRUMO_TEST_DATABASE_URL"
python3 - <<'PY'
import os,sys
from urllib.parse import urlparse,unquote
u=urlparse(os.environ["PRUMO_TEST_DATABASE_URL"])
if u.scheme not in ("postgres","postgresql") or u.hostname not in ("localhost","127.0.0.1","::1") or not unquote(u.path.strip("/")).startswith("prumo_s0_test_"):
 sys.exit("I58 only local disposable PG17")
PY
w="$(mktemp -d)";trap 'rm -rf "$w"' EXIT
m='79060000-0000-4000-8000-000000000001'
shop='79070000-0000-4000-8000-000000000001'
cy='79090000-0000-4000-8000-000000000001'
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" <<SQL
begin;
insert into auth.users(id) values('$m');
insert into public.atores(id) values('$m');
insert into public.equipe_prumo_s1(ator_id,estado) values('$m','ativo');
insert into public.concessionarias(id,nome_operacional) values('$shop','I58 disposable shop');
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel)
 values('$m','$shop','gestor');
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado)
 values('79080000-0000-4000-8000-000000000001','$shop','+5581885810001');
insert into public.ciclos_comerciais(id,concessionaria_id,lead_id,status_comercial)
 values('$cy','$shop','79080000-0000-4000-8000-000000000001','em atendimento pelo operador');
commit;
SQL
await_lock() {
 local name="$1" i n
 for i in $(seq 1 80); do
  n="$(psql -X -qAt "$PRUMO_TEST_DATABASE_URL" -c "select count(*) from pg_catalog.pg_stat_activity where application_name='$name' and state='active' and wait_event_type='Lock'")"
  if [[ "$n" == "1" ]];then return 0;fi;sleep .1
 done
 echo "I58 did not observe lock wait: $name" >&2;return 1
}
# Writer locks and revokes manager grant while a real S0 claim waits.
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$w/revoke" 2>&1 <<SQL &
begin;
update public.vinculos_papel_escopo set valido_ate=pg_catalog.clock_timestamp()
 where ator_id='$m' and concessionaria_id='$shop' and papel='gestor';
select pg_sleep(2.8);commit;
SQL
one=$!
sleep .3
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$w/claim" 2>&1 <<SQL &
set application_name='i58_claim_wait_grant';
select prumo_private.s0_fila_assumir('$m','$shop','$cy',1);
SQL
two=$!
await_lock i58_claim_wait_grant || { cat "$w/revoke" "$w/claim";exit 1; }
wait "$one"
if wait "$two";then echo "I58 CLAIM authorized after revoked grant" >&2;exit 1;fi
grep -q S0_FILA_GESTOR_SEM_LOJA "$w/claim"
[[ "$(psql -X -qAt "$PRUMO_TEST_DATABASE_URL" -c "select estado||':'||versao from prumo_private.s0_fila_humana where ciclo_id='$cy'")" == "pendente:1" ]]
[[ "$(psql -X -qAt "$PRUMO_TEST_DATABASE_URL" -c "select count(*) from public.casos_humanos where ciclo_id='$cy'")" == "0" ]]
echo 'PASS I58-RACE-01: grant revoked while CLAIM awaited SQL lock; queue/case unchanged'
# A signed LIST uses the SAME helper; test expiry of an unchanged grant after
# an observed lock wait. statement_timestamp would incorrectly remain valid.
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -c \
 "update public.vinculos_papel_escopo set valido_ate=pg_catalog.clock_timestamp()+interval '1.5 seconds' where ator_id='$m' and concessionaria_id='$shop' and papel='gestor'" >/dev/null
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$w/hold" 2>&1 <<SQL &
begin;
select ator_id from public.vinculos_papel_escopo where ator_id='$m'
 and concessionaria_id='$shop' and papel='gestor' for update;
select pg_sleep(2.9);commit;
SQL
one=$!
sleep .2
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$w/list" 2>&1 <<SQL &
set application_name='i58_list_wait_expiry';
select prumo_private.s0_fila_exigir_gestor_i58('$m','$shop');
SQL
two=$!
await_lock i58_list_wait_expiry || { cat "$w/hold" "$w/list";exit 1; }
wait "$one"
if wait "$two";then echo "I58 LIST helper accepted naturally expired grant" >&2;exit 1;fi
grep -q S0_FILA_GESTOR_SEM_LOJA "$w/list"
[[ "$(psql -X -qAt "$PRUMO_TEST_DATABASE_URL" -c "select estado||':'||versao from prumo_private.s0_fila_humana where ciclo_id='$cy'")" == "pendente:1" ]]
echo 'PASS I58-RACE-02: LIST authorization rejects naturally expired grant after actual lock wait'
echo 'I58-RACE 2/2 real PG17 lock waits'
