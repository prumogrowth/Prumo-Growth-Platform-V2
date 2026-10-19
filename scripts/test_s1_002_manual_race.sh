#!/usr/bin/env bash
set -euo pipefail
: "$PRUMO_TEST_DATABASE_URL"
python3 - <<'PY'
import os,sys
from urllib.parse import urlparse,unquote
u=urlparse(os.environ['PRUMO_TEST_DATABASE_URL'])
if u.scheme not in ('postgres','postgresql') or u.hostname not in ('localhost','127.0.0.1','::1') or not unquote((u.path or '').strip('/')).startswith('prumo_s0_test_'):
 sys.exit('PG local descartavel obrigatorio')
PY
w="$(mktemp -d)";trap 'rm -rf "$w"' EXIT
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$w/setup" <<'SQL'
insert into auth.users(id) select ('c1120000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid from generate_series(1,4) i;
insert into public.atores(id) select id from auth.users where id::text like 'c1120000-%';
insert into public.equipe_prumo_s1(ator_id,estado) select id,'ativo' from public.atores where id::text like 'c1120000-%';
insert into prumo_private.s1_gestor_operadores(gestor_id,operador_id)
 select 'c1120000-0000-4000-8000-000000000001',('c1120000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid from generate_series(2,4) i;
insert into public.concessionarias(id,nome_operacional) values('c2120000-0000-4000-8000-000000000001','S1MR fake A');
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel)
 select ('c1120000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,'c2120000-0000-4000-8000-000000000001','operador' from generate_series(2,4) i;
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado)
 select ('c3120000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,'c2120000-0000-4000-8000-000000000001',
 '+5581981200'||lpad(i::text,4,'0') from generate_series(1,2) i;
insert into public.ciclos_comerciais(id,concessionaria_id,lead_id,status_comercial)
 select ('c4120000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,'c2120000-0000-4000-8000-000000000001',
 ('c3120000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,'em atendimento pelo operador' from generate_series(1,2) i;
insert into public.casos_humanos(id,concessionaria_id,lead_id,ciclo_id)
 select ('c5120000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,'c2120000-0000-4000-8000-000000000001',
 ('c3120000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 ('c4120000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid from generate_series(1,2) i;
insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id)
 select concessionaria_id,id,'c1120000-0000-4000-8000-000000000002'
 from public.casos_humanos where id::text like 'c5120000-%';
SQL
echo 'PASS S1MR-01: dois casos e 3 operadores sob um gestor'
assignment="$(psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -c "select id from public.atribuicoes_humanas where caso_id='c5120000-0000-4000-8000-000000000001' and encerrada_em is null")"
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$w/first" 2>&1 <<SQL &
begin;
select prumo_private.s1_mover_atendimento_da_equipe('c1120000-0000-4000-8000-000000000001','c2120000-0000-4000-8000-000000000001',
'c5120000-0000-4000-8000-000000000001','$assignment','c1120000-0000-4000-8000-000000000003');
select pg_sleep(1.2);commit;
SQL
one=$!
sleep 0.25
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$w/second" 2>&1 <<SQL &
select prumo_private.s1_mover_atendimento_da_equipe('c1120000-0000-4000-8000-000000000001','c2120000-0000-4000-8000-000000000001',
'c5120000-0000-4000-8000-000000000001','$assignment','c1120000-0000-4000-8000-000000000004');
SQL
two=$!
wait "$one" || { cat "$w/first";exit 1; }
if wait "$two";then echo 'FAIL S1MR-02 aceitou duas transferencias';exit 1;fi
grep -q 'ATRIBUICAO_ESPERADA_' "$w/second"
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" <<'SQL'
do $t$ begin
 if (select count(*) from public.atribuicoes_humanas where caso_id='c5120000-0000-4000-8000-000000000001' and encerrada_em is null)<>1
 or (select count(*) from prumo_private.s1_movimentos_manuais_historico where caso_id='c5120000-0000-4000-8000-000000000001')<>1
 then raise exception 'S1MR-02 duplicidade';end if;end $t$;
SQL
echo 'PASS S1MR-02: movimentos concorrentes mantem so um titular/historico'
assignment="$(psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -c "select id from public.atribuicoes_humanas where caso_id='c5120000-0000-4000-8000-000000000002' and encerrada_em is null")"
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$w/pause" 2>&1 <<'SQL' &
begin;
select prumo_private.s1_pausar_operador_da_equipe('c1120000-0000-4000-8000-000000000001','c1120000-0000-4000-8000-000000000002','AUSENCIA_TEMPORARIA');
select pg_sleep(1.2);commit;
SQL
pause=$!
sleep 0.25
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$w/manual" 2>&1 <<SQL &
select prumo_private.s1_mover_atendimento_da_equipe('c1120000-0000-4000-8000-000000000001','c2120000-0000-4000-8000-000000000001',
'c5120000-0000-4000-8000-000000000002','$assignment','c1120000-0000-4000-8000-000000000003');
SQL
manual=$!
wait "$pause" || { cat "$w/pause";exit 1; }
if wait "$manual";then echo 'FAIL S1MR-03 moveu carteira durante pausa';exit 1;fi
grep -q 'ATRIBUICAO_ESPERADA_' "$w/manual"
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" <<'SQL'
do $t$ begin
 if exists(select 1 from public.atribuicoes_humanas where operador_id='c1120000-0000-4000-8000-000000000002' and encerrada_em is null)
 or (select count(*) from public.atribuicoes_humanas where caso_id='c5120000-0000-4000-8000-000000000002' and encerrada_em is null)<>1
 or exists(select 1 from prumo_private.s1_movimentos_manuais_historico where caso_id='c5120000-0000-4000-8000-000000000002')
 then raise exception 'S1MR-03 falha de corrida pausa/movimento';end if;end $t$;
SQL
echo 'PASS S1MR-03: pausa global prevalece sobre movimento obsoleto'
echo 'PASS S1MR-04: nenhuma duplicidade, nenhuma transferência fora da equipe'
