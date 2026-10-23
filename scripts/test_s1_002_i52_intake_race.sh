#!/usr/bin/env bash
# I52: two independent real PostgreSQL transaction races; disposable only.
set -euo pipefail
: "$PRUMO_TEST_DATABASE_URL"
python3 - <<'PY'
import os,sys
from urllib.parse import urlparse,unquote
u=urlparse(os.environ["PRUMO_TEST_DATABASE_URL"])
if u.scheme not in ("postgres","postgresql") or u.hostname not in ("localhost","127.0.0.1","::1") or not unquote(u.path.strip("/")).startswith("prumo_s0_test_"):
    sys.exit("I52 refuses nonlocal or non-disposable DB")
PY
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
m='76610000-0000-4000-8000-000000000001'
c='76610000-0000-4000-8000-000000000002'
shop='76620000-0000-4000-8000-000000000001'
case_a='76650000-0000-4000-8000-000000000001'
case_b='76650000-0000-4000-8000-000000000002'
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" <<SQL
begin;
insert into auth.users(id) values('$m'),('$c');
insert into public.atores(id) values('$m'),('$c');
insert into public.equipe_prumo_s1(ator_id,estado) values('$m','ativo'),('$c','ativo');
insert into prumo_private.s1_gestor_operadores(gestor_id,operador_id) values('$m','$c');
insert into public.concessionarias(id,nome_operacional) values('$shop','I52 concurrent shop');
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel) values('$c','$shop','operador');
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado)
 values('76630000-0000-4000-8000-000000000001','$shop','+5581999910101'),
 ('76630000-0000-4000-8000-000000000002','$shop','+5581999910102');
insert into public.ciclos_comerciais(id,concessionaria_id,lead_id,status_comercial)
 values('76640000-0000-4000-8000-000000000001','$shop',
 '76630000-0000-4000-8000-000000000001','em atendimento pelo operador'),
 ('76640000-0000-4000-8000-000000000002','$shop',
 '76630000-0000-4000-8000-000000000002','em atendimento pelo operador');
insert into public.casos_humanos(id,concessionaria_id,lead_id,ciclo_id)
 values('$case_a','$shop','76630000-0000-4000-8000-000000000001',
 '76640000-0000-4000-8000-000000000001'),
 ('$case_b','$shop','76630000-0000-4000-8000-000000000002',
 '76640000-0000-4000-8000-000000000002');
commit;
SQL
await_lock() {
 local tag="$1" seen n
 for n in $(seq 1 55); do
  seen="$(psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -c \
  "select count(*) from pg_catalog.pg_stat_activity where application_name='$tag' and wait_event_type='Lock' and state='active'")"
  if [[ "$seen" == "1" ]]; then return 0; fi
  sleep 0.1
 done
 echo "I52 fail: $tag did not wait on a lock" >&2
 return 1
}
# Pause wins: canonical INSERT starts while transaction is blocked.
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$work/pause1" 2>&1 <<SQL &
begin;
set local application_name='s1_i52_pause_winner';
select prumo_private.s1_definir_intake('$m','$c',true,1);
select pg_sleep(2.5);
commit;
SQL
p1=$!
sleep 0.25
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$work/assign1" 2>&1 <<SQL &
set application_name='s1_i52_assign_loser';
insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id)
 values('$shop','$case_a','$c');
SQL
a1=$!
await_lock s1_i52_assign_loser || { cat "$work/pause1" "$work/assign1"; exit 1; }
wait "$p1" || { cat "$work/pause1";exit 1; }
if wait "$a1";then
 echo 'I52 fail: assignment accepted after pause committed first' >&2;exit 1
fi
grep -q DESTINO_COM_INTAKE_PAUSADO "$work/assign1"
[[ "$(psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -c \
 "select count(*) from public.atribuicoes_humanas where caso_id='$case_a'::uuid")" == "0" ]]
echo 'PASS I52-RACE-01: pause committed first; waiting S0 assignment rejected'

psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -c \
 "select prumo_private.s1_definir_intake('$m','$c',false,2)" >"$work/resume"
# Assignment wins: a subsequent pause blocks until assignment commits.
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$work/assign2" 2>&1 <<SQL &
begin;
set local application_name='s1_i52_assign_winner';
insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id)
 values('$shop','$case_b','$c');
select pg_sleep(2.5);
commit;
SQL
a2=$!
sleep 0.25
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$work/pause2" 2>&1 <<SQL &
set application_name='s1_i52_pause_loser';
select prumo_private.s1_definir_intake('$m','$c',true,3);
SQL
p2=$!
await_lock s1_i52_pause_loser || { cat "$work/assign2" "$work/pause2";exit 1; }
wait "$a2" || { cat "$work/assign2";exit 1; }
wait "$p2" || { cat "$work/pause2";exit 1; }
[[ "$(psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -c \
 "select pausado::text||':'||versao from prumo_private.s1_intake_estado where operador_id='$c'::uuid")" == 'true:4' ]]
[[ "$(psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -c \
 "select count(*) from public.atribuicoes_humanas where caso_id='$case_b'::uuid and operador_id='$c'::uuid and encerrada_em is null")" == "1" ]]
[[ "$(psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -c \
 "select count(*) from prumo_private.s1_intake_eventos where operador_id='$c'::uuid")" == "3" ]]
echo 'PASS I52-RACE-02: assignment committed first; subsequent pause keeps prior owner'
echo 'I52-RACE 2/2 confirmed wait_event Lock interleavings, disposable S0/S1 PG17'
