#!/usr/bin/env bash
set -euo pipefail
: "\${PRUMO_TEST_DATABASE_URL:?local disposable PG17 required}"
python3 - <<'PY'
import os,sys
from urllib.parse import urlparse,unquote
u=urlparse(os.environ["PRUMO_TEST_DATABASE_URL"])
if u.scheme not in ("postgres","postgresql") or u.hostname not in ("localhost","127.0.0.1","::1") or not unquote(u.path.strip("/")).startswith("prumo_s0_test_"):
 sys.exit("I57 refuses non-disposable or hosted SQL")
PY
tmp="$(mktemp -d)";trap 'rm -rf "$tmp"' EXIT
m='78960000-0000-4000-8000-000000000001'
owner='78960000-0000-4000-8000-000000000002'
dest='78960000-0000-4000-8000-000000000003'
shop='78970000-0000-4000-8000-000000000001'
ca='789a0000-0000-4000-8000-000000000001'
cb='789a0000-0000-4000-8000-000000000002'
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" <<SQL
begin;
insert into auth.users(id) values('$m'),('$owner'),('$dest');
insert into public.atores(id) values('$m'),('$owner'),('$dest');
insert into public.equipe_prumo_s1(ator_id,estado)
 values('$m','ativo'),('$owner','ativo'),('$dest','ativo');
insert into prumo_private.s1_gestor_operadores(gestor_id,operador_id)
 values('$m','$owner'),('$m','$dest');
insert into public.concessionarias(id,nome_operacional) values('$shop','I57 synthetic');
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel)
 values('$owner','$shop','operador'),('$dest','$shop','operador');
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado)
 values('78980000-0000-4000-8000-000000000001','$shop','+5581885710001'),
 ('78980000-0000-4000-8000-000000000002','$shop','+5581885710002');
insert into public.ciclos_comerciais(id,concessionaria_id,lead_id,status_comercial)
 values('78990000-0000-4000-8000-000000000001','$shop',
 '78980000-0000-4000-8000-000000000001','aguardando primeiro disparo'),
 ('78990000-0000-4000-8000-000000000002','$shop',
 '78980000-0000-4000-8000-000000000002','aguardando primeiro disparo');
insert into public.casos_humanos(id,concessionaria_id,lead_id,ciclo_id)
 values('$ca','$shop','78980000-0000-4000-8000-000000000001','78990000-0000-4000-8000-000000000001'),
 ('$cb','$shop','78980000-0000-4000-8000-000000000002','78990000-0000-4000-8000-000000000002');
insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id)
 values('$shop','$cb','$owner');
commit;
SQL
await_lock() {
 local name="$1" n c
 for n in $(seq 1 70);do
  c="$(psql -X -qAt "$PRUMO_TEST_DATABASE_URL" -c "select count(*) from pg_catalog.pg_stat_activity where application_name='$name' and state='active' and wait_event_type='Lock'")"
  if [[ "$c" == 1 ]];then return 0;fi;sleep .1
 done
 echo "I57 no observed lock wait $name" >&2;return 1
}
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$tmp/revoke" 2>&1 <<SQL &
begin;
update public.vinculos_papel_escopo set valido_ate=pg_catalog.clock_timestamp()
 where ator_id='$dest' and concessionaria_id='$shop' and papel='operador';
select pg_sleep(2.8);commit;
SQL
one=$!
sleep .3
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$tmp/direct" 2>&1 <<SQL &
set application_name='i57_direct_wait';
insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id)
 values('$shop','$ca','$dest');
SQL
two=$!
await_lock i57_direct_wait || { cat "$tmp/revoke" "$tmp/direct";exit 1; }
wait "$one"
if wait "$two";then echo 'I57 direct accepted revoked grant' >&2;exit 1;fi
grep -q S0_DESTINO_SEM_CONCESSAO_ATIVA "$tmp/direct"
[[ "$(psql -X -qAt "$PRUMO_TEST_DATABASE_URL" -c "select count(*) from public.atribuicoes_humanas where caso_id='$ca'")" == "0" ]]
echo 'PASS I57-RACE-01: direct S0 assignment blocked on revoked grant and denied'
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -c \
 "update public.vinculos_papel_escopo set valido_ate=pg_catalog.clock_timestamp()+interval '1.5 seconds' where ator_id='$dest' and concessionaria_id='$shop' and papel='operador'" >/dev/null
previous="$(psql -X -qAt "$PRUMO_TEST_DATABASE_URL" -c "select id from public.atribuicoes_humanas where caso_id='$cb' and encerrada_em is null")"
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$tmp/hold" 2>&1 <<SQL &
begin;
select ator_id from public.vinculos_papel_escopo where ator_id='$dest'
 and concessionaria_id='$shop' and papel='operador' for update;
select pg_sleep(2.9);commit;
SQL
one=$!
sleep .2
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$tmp/move" 2>&1 <<SQL &
set application_name='i57_manual_wait';
select prumo_private.s1_mover_atendimento_da_equipe('$m','$shop','$cb','$previous','$dest');
SQL
two=$!
await_lock i57_manual_wait || { cat "$tmp/hold" "$tmp/move";exit 1; }
wait "$one"
if wait "$two";then echo 'I57 manual accepted naturally expired grant' >&2;exit 1;fi
grep -Eq 'S0_DESTINO_SEM_CONCESSAO_ATIVA|DESTINO_SEM_ACESSO_OU_INATIVO' "$tmp/move"
[[ "$(psql -X -qAt "$PRUMO_TEST_DATABASE_URL" -c "select count(*) from public.atribuicoes_humanas where caso_id='$cb' and operador_id='$owner' and encerrada_em is null")" == "1" ]]
[[ "$(psql -X -qAt "$PRUMO_TEST_DATABASE_URL" -c "select count(*) from prumo_private.s1_movimentos_manuais_historico where caso_id='$cb'")" == "0" ]]
echo 'PASS I57-RACE-02: natural grant expiry during manual wait; prior owner and audit intact'
echo 'I57-RACE 2/2 real PG17 lock waits'
