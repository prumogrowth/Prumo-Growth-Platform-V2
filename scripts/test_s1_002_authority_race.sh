#!/usr/bin/env bash
set -euo pipefail
: "$PRUMO_TEST_DATABASE_URL"
python3 - <<'PY'
import os,sys
from urllib.parse import urlparse,unquote
u=urlparse(os.environ['PRUMO_TEST_DATABASE_URL'])
if u.scheme not in ('postgres','postgresql') or u.hostname not in ('localhost','127.0.0.1','::1') or not unquote((u.path or '').strip('/')).startswith('prumo_s0_test_'):
 sys.exit('RECUSADO: PostgreSQL local descartavel obrigatorio')
PY
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$work/setup" <<'SQL'
insert into auth.users(id) select ('d1120000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid from generate_series(1,4) i;
insert into public.atores(id) select id from auth.users where id::text like 'd1120000-%';
insert into public.equipe_prumo_s1(ator_id,estado) select id,'ativo' from public.atores where id::text like 'd1120000-%';
insert into public.concessionarias(id,nome_operacional) values('d2120000-0000-4000-8000-000000000001','S1AG ficticia');
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel)
 select ('d1120000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 'd2120000-0000-4000-8000-000000000001','operador' from generate_series(2,3) i;
insert into prumo_private.s1_gestor_operadores(gestor_id,operador_id)
 select 'd1120000-0000-4000-8000-000000000001',
 ('d1120000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid from generate_series(2,3) i;
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado)
 select ('d3120000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 'd2120000-0000-4000-8000-000000000001',
 '+5581981400'||lpad(i::text,4,'0') from generate_series(1,2) i;
insert into public.ciclos_comerciais(id,concessionaria_id,lead_id,status_comercial)
 select ('d4120000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 'd2120000-0000-4000-8000-000000000001',
 ('d3120000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 'em atendimento pelo operador' from generate_series(1,2) i;
insert into public.casos_humanos(id,concessionaria_id,lead_id,ciclo_id)
 select ('d5120000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 'd2120000-0000-4000-8000-000000000001',
 ('d3120000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 ('d4120000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid from generate_series(1,2) i;
insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id)
 select concessionaria_id,id,'d1120000-0000-4000-8000-000000000002'
 from public.casos_humanos where id::text like 'd5120000-%';
SQL
echo 'PASS S1AG-01: gestor M1 supervisiona origem O2 e destino O3'

a1="$(psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -c "select id from public.atribuicoes_humanas where caso_id='d5120000-0000-4000-8000-000000000001' and encerrada_em is null")"
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$work/revoke" 2>&1 <<'SQL' &
begin;
update prumo_private.s1_gestor_operadores set encerrado_em=statement_timestamp()
 where gestor_id='d1120000-0000-4000-8000-000000000001'
 and operador_id='d1120000-0000-4000-8000-000000000003' and encerrado_em is null;
select pg_sleep(1.25);
commit;
SQL
revoker=$!
sleep 0.22
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$work/move1" 2>&1 <<SQL &
select prumo_private.s1_mover_atendimento_da_equipe(
 'd1120000-0000-4000-8000-000000000001',
 'd2120000-0000-4000-8000-000000000001',
 'd5120000-0000-4000-8000-000000000001',
 '$a1','d1120000-0000-4000-8000-000000000003');
SQL
moving=$!
wait "$revoker" || { cat "$work/revoke"; exit 1; }
if wait "$moving"; then echo 'FAIL S1AG-02: gestor moveu depois da revogacao';exit 1;fi
grep -q 'GESTAO_EQUIPE_NAO_AUTORIZADA' "$work/move1"
echo 'PASS S1AG-02: gestor perde poder após revogação concorrente do destino'
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -c "insert into prumo_private.s1_gestor_operadores(gestor_id,operador_id) values('d1120000-0000-4000-8000-000000000001','d1120000-0000-4000-8000-000000000003')" >/dev/null

a2="$(psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -c "select id from public.atribuicoes_humanas where caso_id='d5120000-0000-4000-8000-000000000002' and encerrada_em is null")"
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$work/susp" 2>&1 <<'SQL' &
begin;
update public.equipe_prumo_s1 set estado='suspenso' where ator_id='d1120000-0000-4000-8000-000000000001';
select pg_sleep(1.25);
commit;
SQL
susp=$!
sleep 0.22
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$work/move2" 2>&1 <<SQL &
select prumo_private.s1_mover_atendimento_da_equipe(
 'd1120000-0000-4000-8000-000000000001',
 'd2120000-0000-4000-8000-000000000001',
 'd5120000-0000-4000-8000-000000000002',
 '$a2','d1120000-0000-4000-8000-000000000003');
SQL
moving=$!
wait "$susp" || { cat "$work/susp"; exit 1; }
if wait "$moving"; then echo 'FAIL S1AG-03: gestor suspenso moveu caso';exit 1;fi
grep -q 'GESTAO_EQUIPE_NAO_AUTORIZADA' "$work/move2"
echo 'PASS S1AG-03: suspensão concorrente do gestor impede movimento'
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -c "update public.equipe_prumo_s1 set estado='ativo' where ator_id='d1120000-0000-4000-8000-000000000001'" >/dev/null

psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" <<'SQL'
update prumo_private.s1_gestor_operadores set encerrado_em=statement_timestamp()
 where gestor_id='d1120000-0000-4000-8000-000000000001' and encerrado_em is null;
insert into prumo_private.s1_gestor_operadores(gestor_id,operador_id)
 select 'd1120000-0000-4000-8000-000000000004',
 ('d1120000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid from generate_series(2,3) i;
SQL
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" <<SQL
select prumo_private.s1_mover_atendimento_da_equipe(
 'd1120000-0000-4000-8000-000000000004',
 'd2120000-0000-4000-8000-000000000001',
 'd5120000-0000-4000-8000-000000000001',
 '$a1','d1120000-0000-4000-8000-000000000003');
SQL
echo 'PASS S1AG-04: novo gestor assume equipe e consegue mover caso'

psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" <<'SQL'
do $t$ begin
 if (select count(*) from public.atribuicoes_humanas
  where caso_id::text like 'd5120000-%' and encerrada_em is null)<>2
 or (select count(*) from prumo_private.s1_movimentos_manuais_historico
  where caso_id::text like 'd5120000-%')<>1
 or (select count(*) from public.vinculos_papel_escopo
  where ator_id::text like 'd1120000-%')<>2
 then raise exception 'S1AG-05 historico/titulares/grants divergentes';end if;
end $t$;
SQL
echo 'PASS S1AG-05: apenas uma transferência autorizada; grants imutáveis'
