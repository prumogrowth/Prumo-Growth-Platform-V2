#!/usr/bin/env bash
set -euo pipefail
: "$PRUMO_TEST_DATABASE_URL"
python3 - <<'PY'
import os,sys
from urllib.parse import urlparse
u=urlparse(os.environ["PRUMO_TEST_DATABASE_URL"])
if u.hostname not in ("localhost","127.0.0.1","::1") or not u.path.strip("/").startswith("prumo_s0_test_"):
 sys.exit("I54 disposable DB required")
PY
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
m='78610000-0000-4000-8000-000000000001'
shop='78620000-0000-4000-8000-000000000001'
a='78630000-0000-4000-8000-000000000001'
b='78630000-0000-4000-8000-000000000002'
ca='78640000-0000-4000-8000-000000000001'
cb='78640000-0000-4000-8000-000000000002'
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" <<SQL
begin;
insert into auth.users(id) values('$m');
insert into public.atores(id) values('$m');
insert into public.equipe_prumo_s1(ator_id,estado) values('$m','ativo');
insert into public.concessionarias(id,nome_operacional) values('$shop','I54 race');
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel)
 values('$m','$shop','gestor');
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado)
 values('$a','$shop','+5581885410001'),('$b','$shop','+5581885410002');
insert into public.ciclos_comerciais(id,concessionaria_id,lead_id,status_comercial)
 values('$ca','$shop','$a','em atendimento pelo operador'),
 ('$cb','$shop','$b','em atendimento pelo operador');
commit;
SQL
await_block() {
 local app="$1" n v
 for n in $(seq 1 60);do
  v="$(psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -c \
  "select count(*) from pg_catalog.pg_stat_activity where application_name='$app' and wait_event_type='Lock' and state='active'")"
  if [[ "$v" == "1" ]];then return 0;fi
  sleep .1
 done
 echo "I54 no Lock wait: $app" >&2;return 1
}
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$tmp/holda" 2>&1 <<SQL &
begin;
select id from public.leads_loja where id='$a'::uuid for update;
select pg_sleep(2.8);
commit;
SQL
holder=$!
sleep .25
for n in 1 2;do
 psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$tmp/claim$n" 2>&1 <<SQL &
set application_name='i54_claim_$n';
select prumo_private.s0_fila_assumir('$m','$shop','$ca',1);
SQL
 if [[ "$n" == "1" ]];then a1=$!;else a2=$!;fi
done
await_block i54_claim_1 || { cat "$tmp/claim1";exit 1; }
await_block i54_claim_2 || { cat "$tmp/claim2";exit 1; }
wait "$holder" && wait "$a1" && wait "$a2"
[[ "$(grep -c CLAIMED_BY_MANAGER "$tmp/claim1" "$tmp/claim2" | awk -F: '{s+=$NF} END {print s+0}')" == "1" ]]
[[ "$(grep -c CONFLICT "$tmp/claim1" "$tmp/claim2" | awk -F: '{s+=$NF} END {print s+0}')" == "1" ]]
[[ "$(psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -c \
 "select count(*) from public.atribuicoes_humanas a join public.casos_humanos h on h.id=a.caso_id where h.ciclo_id='$ca'::uuid and a.encerrada_em is null")" == "1" ]]
[[ "$(psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -c \
 "select count(*) from prumo_private.s0_fila_humana_eventos where ciclo_id='$ca'::uuid and resultado='ASSUMIDO'")" == "1" ]]
echo 'PASS I54-RACE-01: concurrent claims => one canonical owner and one audit, loser CAS conflict'

psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$tmp/holdb" 2>&1 <<SQL &
begin;
select id from public.leads_loja where id='$b'::uuid for update;
select pg_sleep(2.8);
commit;
SQL
holder=$!
sleep .25
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$tmp/revoked" 2>&1 <<SQL &
set application_name='i54_revoked_claim';
select prumo_private.s0_fila_assumir('$m','$shop','$cb',1);
SQL
waiter=$!
await_block i54_revoked_claim || { cat "$tmp/revoked";exit 1; }
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -c \
 "update public.vinculos_papel_escopo set valido_ate=clock_timestamp() where ator_id='$m'::uuid and concessionaria_id='$shop'::uuid and papel='gestor' and valido_ate is null"
wait "$holder"
if wait "$waiter";then echo 'I54 revoked manager claimed lead' >&2;exit 1;fi
grep -q S0_FILA_GESTOR_SEM_LOJA "$tmp/revoked"
[[ "$(psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -c \
 "select count(*) from public.casos_humanos where ciclo_id='$cb'::uuid")" == "0" ]]
[[ "$(psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -c \
 "select estado||':'||versao from prumo_private.s0_fila_humana where ciclo_id='$cb'::uuid")" == "pendente:1" ]]
echo 'PASS I54-RACE-02: grant revoked while blocked => no case and unchanged queue'
echo 'I54-RACE 2/2 observed real Lock waits'
