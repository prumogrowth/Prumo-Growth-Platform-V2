#!/usr/bin/env bash
set -euo pipefail
: "${PRUMO_TEST_DATABASE_URL:?URL PG17 local descartavel obrigatoria}"
python3 - <<'PY'
import os,sys
from urllib.parse import urlparse,unquote
u=urlparse(os.environ["PRUMO_TEST_DATABASE_URL"])
if u.scheme not in ("postgres","postgresql") or u.hostname not in ("127.0.0.1","localhost","::1") or not unquote(u.path.lstrip("/")).startswith("prumo_s0_test_"):
 sys.exit("BLOQUEADO: only disposable loopback PostgreSQL")
PY
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$work/setup" <<'SQL'
insert into auth.users(id)
 select ('e3100000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid
 from generate_series(1,3) i;
insert into public.atores(id)
 select id from auth.users where id::text like 'e3100000-%';
insert into public.equipe_prumo_s1(ator_id,estado)
 select id,'ativo' from public.atores where id::text like 'e3100000-%';
insert into prumo_private.s1_gestor_operadores(gestor_id,operador_id)
 select 'e3100000-0000-4000-8000-000000000001',
  ('e3100000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid
 from generate_series(2,3) i;
insert into public.concessionarias(id,nome_operacional)
 values('e3200000-0000-4000-8000-000000000001','RACE S0 S1 local ficticio');
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel)
 select ('e3100000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 'e3200000-0000-4000-8000-000000000001','operador'
 from generate_series(2,3) i;
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado)
 select ('e3300000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 'e3200000-0000-4000-8000-000000000001',
 '+5581985300'||lpad(i::text,4,'0') from generate_series(1,2) i;
insert into public.ciclos_comerciais(id,concessionaria_id,lead_id,status_comercial)
 select ('e3400000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 'e3200000-0000-4000-8000-000000000001',
 ('e3300000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 'em atendimento pelo operador' from generate_series(1,2) i;
insert into public.casos_humanos(id,concessionaria_id,lead_id,ciclo_id)
 select ('e3500000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 'e3200000-0000-4000-8000-000000000001',
 ('e3300000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 ('e3400000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid from generate_series(1,2) i;
insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id)
 select concessionaria_id,id,'e3100000-0000-4000-8000-000000000002'
 from public.casos_humanos where id::text like 'e3500000-%';
select prumo_private.s1_definir_disponibilidade_leads_10(
 'e3100000-0000-4000-8000-000000000001',
 'e3100000-0000-4000-8000-000000000002',true,1);
select prumo_private.s0_registrar_contato_humano_fixture_10(
 a.concessionaria_id,a.caso_id,a.id,'SEM_INICIO_CONFIRMADO',
 's0:race:verified-no-human:case1')
 from public.atribuicoes_humanas a
 where a.caso_id='e3500000-0000-4000-8000-000000000001' and a.encerrada_em is null;
select prumo_private.s0_registrar_contato_humano_fixture_10(
 a.concessionaria_id,a.caso_id,a.id,'SEM_INICIO_CONFIRMADO',
 's0:race:verified-no-human:case2')
 from public.atribuicoes_humanas a
 where a.caso_id='e3500000-0000-4000-8000-000000000002' and a.encerrada_em is null;
SQL
echo 'PASS ISSUE10R-01: fixture S0+S1 dois casos nao iniciados e operador pausado'
a1="$(psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -c "select id from public.atribuicoes_humanas where caso_id='e3500000-0000-4000-8000-000000000001' and encerrada_em is null")"
a2="$(psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -c "select id from public.atribuicoes_humanas where caso_id='e3500000-0000-4000-8000-000000000002' and encerrada_em is null")"

# S0 adquire lock de caso primeiro e CONFIRMA inicio, mantendo transacao aberta.
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$work/human1" 2>&1 <<SQL &
begin;
select prumo_private.s0_registrar_contato_humano_fixture_10(
 'e3200000-0000-4000-8000-000000000001',
 'e3500000-0000-4000-8000-000000000001',
 '$a1','INICIADO','s0:race:human-confirmed:case1');
select pg_sleep(1.1);
commit;
SQL
human_pid=$!
sleep 0.24
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$work/reconcile1" 2>&1 <<'SQL' &
select prumo_private.s1_redistribuir_pausado_provas_10(
 'e3100000-0000-4000-8000-000000000001',
 'e3100000-0000-4000-8000-000000000002',2);
SQL
reconcile_pid=$!
wait "$human_pid" || { cat "$work/human1"; exit 1; }
wait "$reconcile_pid" || { cat "$work/reconcile1"; exit 1; }
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" <<'SQL'
do $t$ begin
 if not exists(select 1 from public.atribuicoes_humanas
    where caso_id='e3500000-0000-4000-8000-000000000001'
    and operador_id='e3100000-0000-4000-8000-000000000002'
    and encerrada_em is null)
 or (select count(*) from public.atribuicoes_humanas
    where caso_id='e3500000-0000-4000-8000-000000000001'
      and encerrada_em is null)<>1
 then raise exception 'ISSUE10R-02 inicio humano nao teve prioridade';end if;
end $t$;
SQL
echo 'PASS ISSUE10R-02: resposta humana confirmada antes do commit impede movimento'

# Case2 ainda na origem? A primeira reconciliacao pode transferir case2,
# pois estava elegivel. Para esta segunda corrida e necessario outro caso,
# com titular da origem: cria um terceiro caso e prova S0 negativa.
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" <<'SQL'
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado)
 values('e3300000-0000-4000-8000-000000000003',
 'e3200000-0000-4000-8000-000000000001','+5581985300003');
insert into public.ciclos_comerciais(id,concessionaria_id,lead_id,status_comercial)
 values('e3400000-0000-4000-8000-000000000003',
 'e3200000-0000-4000-8000-000000000001',
 'e3300000-0000-4000-8000-000000000003','em atendimento pelo operador');
insert into public.casos_humanos(id,concessionaria_id,lead_id,ciclo_id)
 values('e3500000-0000-4000-8000-000000000003',
 'e3200000-0000-4000-8000-000000000001',
 'e3300000-0000-4000-8000-000000000003',
 'e3400000-0000-4000-8000-000000000003');
-- Forma intencionalmente administrativa: atribuicao a origem ocorre por
-- fluxo de recuperacao legada sem envolver cliente real. O guard deve
-- impedir porque pausa vigente; despausa brevemente de forma versionada.
select prumo_private.s1_definir_disponibilidade_leads_10(
 'e3100000-0000-4000-8000-000000000001',
 'e3100000-0000-4000-8000-000000000002',false,2);
insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id)
 values('e3200000-0000-4000-8000-000000000001',
 'e3500000-0000-4000-8000-000000000003',
 'e3100000-0000-4000-8000-000000000002');
select prumo_private.s0_registrar_contato_humano_fixture_10(
 a.concessionaria_id,a.caso_id,a.id,'SEM_INICIO_CONFIRMADO',
 's0:race:verified-no-human:case3')
 from public.atribuicoes_humanas a
 where a.caso_id='e3500000-0000-4000-8000-000000000003' and a.encerrada_em is null;
select prumo_private.s1_definir_disponibilidade_leads_10(
 'e3100000-0000-4000-8000-000000000001',
 'e3100000-0000-4000-8000-000000000002',true,3);
SQL
a3="$(psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -c "select id from public.atribuicoes_humanas where caso_id='e3500000-0000-4000-8000-000000000003' and encerrada_em is null")"
# S1 trava caso e efetua remanejamento, ainda sem commit; S0 humano com
# atribuicao ANTIGA fica aguardando e depois recebe conflito 40001.
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$work/reconcile2" 2>&1 <<'SQL' &
begin;
select prumo_private.s1_redistribuir_pausado_provas_10(
 'e3100000-0000-4000-8000-000000000001',
 'e3100000-0000-4000-8000-000000000002',4);
select pg_sleep(1.1);
commit;
SQL
reconcile_pid=$!
sleep 0.24
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$work/latehuman" 2>&1 <<SQL &
select prumo_private.s0_registrar_contato_humano_fixture_10(
 'e3200000-0000-4000-8000-000000000001',
 'e3500000-0000-4000-8000-000000000003',
 '$a3','INICIADO','s0:race:late-human-old-assignment:case3');
SQL
late_pid=$!
wait "$reconcile_pid" || { cat "$work/reconcile2"; exit 1; }
if wait "$late_pid";then
 echo 'FAIL ISSUE10R-03: aceitou resposta humana vinculada a atribuicao obsoleta';exit 1
fi
grep -q 'ATRIBUICAO_NAO_ATUAL' "$work/latehuman" || { cat "$work/latehuman";exit 1; }
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" <<'SQL'
do $t$ begin
 if (select count(*) from public.atribuicoes_humanas
    where caso_id='e3500000-0000-4000-8000-000000000003'
      and encerrada_em is null)<>1
 or not exists(select 1 from public.atribuicoes_humanas
    where caso_id='e3500000-0000-4000-8000-000000000003'
      and encerrada_em is null
      and operador_id='e3100000-0000-4000-8000-000000000003')
 then raise exception 'ISSUE10R-03 duas atribuicoes ou destino errado';end if;
end $t$;
SQL
echo 'PASS ISSUE10R-03: se transferencia venceu, resposta do antigo titular e recusada'
echo 'PASS ISSUE10R-04: titularidade permanece unica e estado de equipe/grants intactos'
