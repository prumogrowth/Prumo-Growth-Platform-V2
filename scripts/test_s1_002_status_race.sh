#!/usr/bin/env bash
set -euo pipefail
: "$PRUMO_TEST_DATABASE_URL"
python3 - <<'PY'
import os,sys
from urllib.parse import urlparse,unquote
u=urlparse(os.environ['PRUMO_TEST_DATABASE_URL'])
if u.scheme not in ('postgres','postgresql') or u.hostname not in ('localhost','127.0.0.1','::1') or not unquote((u.path or '').strip('/')).startswith('prumo_s0_test_'):
 sys.exit('Somente PostgreSQL local descartavel')
PY
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$work/setup" <<'SQL'
insert into auth.users(id) values
 ('a6120000-0000-4000-8000-000000000001'),
 ('a6120000-0000-4000-8000-000000000002');
insert into public.atores(id) select id from auth.users where id::text like 'a6120000-%';
insert into public.concessionarias(id,nome_operacional) values
 ('a6220000-0000-4000-8000-000000000001','S1SC ficticia');
insert into public.equipe_prumo_s1(ator_id,estado)
 select id,'ativo' from public.atores where id::text like 'a6120000-%';
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel)
 select id,'a6220000-0000-4000-8000-000000000001','operador'
 from public.atores where id::text like 'a6120000-%';
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado)
 select ('a6320000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 'a6220000-0000-4000-8000-000000000001',
 '+5581981900'||lpad(i::text,4,'0') from generate_series(1,3) i;
insert into public.ciclos_comerciais(id,concessionaria_id,lead_id,status_comercial)
 select ('a6420000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 'a6220000-0000-4000-8000-000000000001',
 ('a6320000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 case when i=2 then 'vendido' else 'em atendimento pelo operador' end
 from generate_series(1,3) i;
insert into public.casos_humanos(id,concessionaria_id,lead_id,ciclo_id,motivo_simulado)
 select ('a6520000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 'a6220000-0000-4000-8000-000000000001',
 ('a6320000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 ('a6420000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 case when i=2 then 'retorno_pos_venda' else null end
 from generate_series(1,3) i;
insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id)
 select concessionaria_id,id,'a6120000-0000-4000-8000-000000000001'
 from public.casos_humanos where id::text like 'a6520000-%' and id<>'a6520000-0000-4000-8000-000000000003';
SQL
echo 'PASS S1SC-01: fixtures para estados concorrentes'
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$work/status" 2>&1 <<'SQL' &
begin;
update public.ciclos_comerciais set status_comercial='vendido'
 where id='a6420000-0000-4000-8000-000000000001';
select pg_sleep(1.3);
commit;
SQL
first=$!
sleep 0.24
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$work/suspension" 2>&1 <<'SQL' &
update public.equipe_prumo_s1 set estado='suspenso'
 where ator_id='a6120000-0000-4000-8000-000000000001';
SQL
second=$!
wait "$first" || { cat "$work/status"; exit 1; }
wait "$second" || { cat "$work/suspension"; exit 1; }
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$work/check1" <<'SQL'
do $t$ begin
 if exists(select 1 from public.atribuicoes_humanas
  where caso_id='a6520000-0000-4000-8000-000000000001' and encerrada_em is null)
 or (select count(*) from prumo_private.s1_remanejamento_historico
  where caso_id='a6520000-0000-4000-8000-000000000001'
   and resultado='ENCERRADO_HISTORICO')<>1
 or (select count(*) from public.atribuicoes_humanas
  where caso_id='a6520000-0000-4000-8000-000000000002'
   and operador_id='a6120000-0000-4000-8000-000000000002'
   and encerrada_em is null)<>1
 then raise exception 'S1SC-02 estado terminal concorrente violado';end if;
end $t$;
SQL
echo 'PASS S1SC-02: status terminal confirmado antes da suspensao nao gera titular'
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$work/pending" <<'SQL'
insert into prumo_private.s1_remanejamento_pendencias(
 concessionaria_id,caso_id,operador_anterior,motivo)
 values('a6220000-0000-4000-8000-000000000001',
 'a6520000-0000-4000-8000-000000000003',
 'a6120000-0000-4000-8000-000000000001','EQUIPE_INATIVA');
SQL
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$work/status2" 2>&1 <<'SQL' &
begin;
update public.ciclos_comerciais set status_comercial='perdido'
 where id='a6420000-0000-4000-8000-000000000003';
select pg_sleep(1.3);
commit;
SQL
s0=$!
sleep 0.24
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$work/recover" 2>&1 <<'SQL' &
select prumo_private.s1_recuperar_fila_protegida(
 'a6220000-0000-4000-8000-000000000001',25);
SQL
s1=$!
wait "$s0" || { cat "$work/status2"; exit 1; }
wait "$s1" || { cat "$work/recover"; exit 1; }
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$work/check2" <<'SQL'
do $t$ begin
 if exists(select 1 from public.atribuicoes_humanas
  where caso_id='a6520000-0000-4000-8000-000000000003' and encerrada_em is null)
 or (select count(*) from prumo_private.s1_recuperacao_fila_historico
  where caso_id='a6520000-0000-4000-8000-000000000003'
   and resultado='TERMINAL')<>1
 or exists(select 1 from prumo_private.s1_remanejamento_pendencias
  where caso_id='a6520000-0000-4000-8000-000000000003')
 then raise exception 'S1SC-03 recuperacao usou status antigo';end if;
end $t$;
SQL
echo 'PASS S1SC-03: recuperacao aguarda estado confirmado do ciclo'
echo 'PASS S1SC-04: duas corridas S0 SQL simulado/S1 sem deadlock'
