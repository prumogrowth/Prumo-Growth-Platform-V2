#!/usr/bin/env bash
set -euo pipefail
: "$PRUMO_TEST_DATABASE_URL"
python3 - <<'PY'
import os,sys
from urllib.parse import urlparse
u=urlparse(os.environ['PRUMO_TEST_DATABASE_URL'])
if u.hostname not in ('localhost','127.0.0.1','::1') or not u.path.strip('/').startswith('prumo_s0_test_'):
 sys.exit('I56 requires disposable local PG17')
PY
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
m='78810000-0000-4000-8000-000000000001'
shop='78820000-0000-4000-8000-000000000001'
a='78830000-0000-4000-8000-000000000001'
b='78830000-0000-4000-8000-000000000002'
ca='78840000-0000-4000-8000-000000000001'
cb='78840000-0000-4000-8000-000000000002'
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" <<SQL
begin;
insert into auth.users(id) values('$m');
insert into public.atores(id) values('$m');
insert into public.equipe_prumo_s1(ator_id,estado) values('$m','ativo');
insert into public.concessionarias(id,nome_operacional) values('$shop','I56 race');
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel) values('$m','$shop','gestor');
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado)
 values('$a','$shop','+5581885620001'),('$b','$shop','+5581885620002');
insert into public.ciclos_comerciais(id,concessionaria_id,lead_id,status_comercial)
 values('$ca','$shop','$a','em atendimento pelo operador'),
 ('$cb','$shop','$b','em atendimento pelo operador');
commit;
SQL
await_block() {
 local n v app="$1"
 for n in $(seq 1 65);do
  v="$(psql -X -qAt "$PRUMO_TEST_DATABASE_URL" -c "select count(*) from pg_stat_activity where application_name='$app' and wait_event_type='Lock' and state='active'")"
  if [[ "$v" == "1" ]];then return 0;fi
  sleep .1
 done
 echo "no lock wait observed: $app" >&2
 return 1
}
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$tmp/external" 2>&1 <<SQL &
begin;
insert into public.casos_humanos(concessionaria_id,lead_id,ciclo_id) values('$shop','$a','$ca');
select pg_sleep(2.8);
commit;
SQL
ext=$!
sleep .3
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$tmp/claim" 2>&1 <<SQL &
set application_name='i56_wait_external';
select prumo_private.s0_fila_assumir('$m','$shop','$ca',1);
SQL
cl=$!
await_block i56_wait_external || { cat "$tmp/external" "$tmp/claim";exit 1; }
wait "$ext" && wait "$cl"
grep -q CONFLICT "$tmp/claim"
[[ "$(psql -X -qAt "$PRUMO_TEST_DATABASE_URL" -c "select estado||':'||versao from prumo_private.s0_fila_humana where ciclo_id='$ca'")" == "reconciliado:2" ]]
[[ "$(psql -X -qAt "$PRUMO_TEST_DATABASE_URL" -c "select count(*) from public.casos_humanos where ciclo_id='$ca'")" == "1" ]]
echo 'PASS I56-RACE-01: external case first => one case and claim CAS conflict'
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$tmp/claimB" 2>&1 <<SQL &
begin;
select prumo_private.s0_fila_assumir('$m','$shop','$cb',1);
select pg_sleep(2.8);
commit;
SQL
cl=$!
sleep .3
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$tmp/extB" 2>&1 <<SQL &
set application_name='i56_wait_claim';
insert into public.casos_humanos(concessionaria_id,lead_id,ciclo_id) values('$shop','$b','$cb');
SQL
ext=$!
await_block i56_wait_claim || { cat "$tmp/claimB" "$tmp/extB";exit 1; }
wait "$cl"
if wait "$ext";then echo 'I56 duplicate case inserted' >&2;exit 1;fi
grep -q I56_DUPLICATE_CYCLE_CASE "$tmp/extB"
grep -q CLAIMED_BY_MANAGER "$tmp/claimB"
[[ "$(psql -X -qAt "$PRUMO_TEST_DATABASE_URL" -c "select estado||':'||versao from prumo_private.s0_fila_humana where ciclo_id='$cb'")" == "atribuido:2" ]]
[[ "$(psql -X -qAt "$PRUMO_TEST_DATABASE_URL" -c "select count(*) from public.atribuicoes_humanas a join public.casos_humanos h on h.id=a.caso_id where h.ciclo_id='$cb' and a.encerrada_em is null")" == "1" ]]
echo 'PASS I56-RACE-02: claim first => second case denied after lock, one owner'
echo 'I56-RACE 2/2 real PostgreSQL wait observations'
