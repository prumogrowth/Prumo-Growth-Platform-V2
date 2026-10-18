#!/usr/bin/env bash
set -euo pipefail
: "$PRUMO_TEST_DATABASE_URL"
python3 - <<'PY'
import os,sys
from urllib.parse import urlparse,unquote
u=urlparse(os.environ['PRUMO_TEST_DATABASE_URL'])
if u.scheme not in ('postgres','postgresql') or u.hostname not in ('localhost','127.0.0.1','::1') or not unquote((u.path or '').strip('/')).startswith('prumo_s0_test_'):
 sys.exit('RECUSADO: somente banco PostgreSQL local descartavel')
PY
scratch="$(mktemp -d)"
trap 'rm -rf "$scratch"' EXIT
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$scratch/setup" <<'SQL'
insert into auth.users(id) values
 ('b1020000-0000-4000-8000-000000000001'),
 ('b1020000-0000-4000-8000-000000000002');
insert into public.atores(id)
 select id from auth.users where id::text like 'b1020000-%';
insert into public.equipe_prumo_s1(ator_id,estado) values
 ('b1020000-0000-4000-8000-000000000001','suspenso'),
 ('b1020000-0000-4000-8000-000000000002','ativo');
insert into public.concessionarias(id,nome_operacional) values
 ('b2020000-0000-4000-8000-000000000001','S1 queue recovery race A');
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel) values
 ('b1020000-0000-4000-8000-000000000001','b2020000-0000-4000-8000-000000000001','operador'),
 ('b1020000-0000-4000-8000-000000000002','b2020000-0000-4000-8000-000000000001','operador');
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado) values
 ('b3020000-0000-4000-8000-000000000001','b2020000-0000-4000-8000-000000000001','+5581985000001'),
 ('b3020000-0000-4000-8000-000000000002','b2020000-0000-4000-8000-000000000001','+5581985000002');
insert into public.ciclos_comerciais(id,concessionaria_id,lead_id,status_comercial) values
 ('b4020000-0000-4000-8000-000000000001','b2020000-0000-4000-8000-000000000001','b3020000-0000-4000-8000-000000000001','em atendimento pelo operador'),
 ('b4020000-0000-4000-8000-000000000002','b2020000-0000-4000-8000-000000000001','b3020000-0000-4000-8000-000000000002','em atendimento pelo operador');
insert into public.casos_humanos(id,concessionaria_id,lead_id,ciclo_id) values
 ('b5020000-0000-4000-8000-000000000001','b2020000-0000-4000-8000-000000000001','b3020000-0000-4000-8000-000000000001','b4020000-0000-4000-8000-000000000001'),
 ('b5020000-0000-4000-8000-000000000002','b2020000-0000-4000-8000-000000000001','b3020000-0000-4000-8000-000000000002','b4020000-0000-4000-8000-000000000002');
-- Fixtures excepcionais: fila ja existente antes de operador ficar disponivel.
-- Insercao privada sintetica nao substitui trigger normal do dominio I2.
insert into prumo_private.s1_remanejamento_pendencias(
 concessionaria_id,caso_id,operador_anterior,motivo)
 values('b2020000-0000-4000-8000-000000000001',
        'b5020000-0000-4000-8000-000000000001',
        'b1020000-0000-4000-8000-000000000001','EQUIPE_INATIVA');
SQL
echo 'PASS S1QC-01: fixture privada de fila sem titular e profissional valido'
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$scratch/first" 2>&1 <<'SQL' &
begin;
select prumo_private.s1_recuperar_fila_protegida(
 'b2020000-0000-4000-8000-000000000001',10);
select pg_sleep(1.15);
commit;
SQL
first=$!
sleep 0.25
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$scratch/second" 2>&1 <<'SQL' &
select prumo_private.s1_recuperar_fila_protegida(
 'b2020000-0000-4000-8000-000000000001',10);
SQL
second=$!
wait "$first" || { cat "$scratch/first"; exit 1; }
wait "$second" || { cat "$scratch/second"; exit 1; }
grep -q '"reassigned": 1' "$scratch/first"
grep -q '"inspected": 0' "$scratch/second"
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$scratch/check1" <<'SQL'
do $chk$ begin
 if (select count(*) from public.atribuicoes_humanas
  where caso_id='b5020000-0000-4000-8000-000000000001'
   and encerrada_em is null
   and operador_id='b1020000-0000-4000-8000-000000000002')<>1
 or (select count(*) from prumo_private.s1_recuperacao_fila_historico
  where caso_id='b5020000-0000-4000-8000-000000000001'
   and resultado='RECUPERADO')<>1
 or exists(select 1 from prumo_private.s1_remanejamento_pendencias
  where caso_id='b5020000-0000-4000-8000-000000000001')
 then raise exception 'S1QC-02 dois consumidores duplicaram caso';end if;
end $chk$;
SQL
echo 'PASS S1QC-02: dois recuperadores simultaneos geram apenas uma atribuicao e uma auditoria'
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$scratch/pend" <<'SQL'
insert into prumo_private.s1_remanejamento_pendencias(
 concessionaria_id,caso_id,operador_anterior,motivo)
 values('b2020000-0000-4000-8000-000000000001',
        'b5020000-0000-4000-8000-000000000002',
        'b1020000-0000-4000-8000-000000000001','EQUIPE_INATIVA');
SQL
-- Outra operacao transacional ganha posse do CASO antes de recuperar.
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$scratch/manual" 2>&1 <<'SQL' &
begin;
select id from public.casos_humanos
 where id='b5020000-0000-4000-8000-000000000002' for update;
select pg_sleep(1.15);
insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id)
 values('b2020000-0000-4000-8000-000000000001',
        'b5020000-0000-4000-8000-000000000002',
        'b1020000-0000-4000-8000-000000000002');
commit;
SQL
manual=$!
sleep 0.25
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$scratch/reconcile" 2>&1 <<'SQL' &
select prumo_private.s1_recuperar_fila_protegida(
 'b2020000-0000-4000-8000-000000000001',10);
SQL
recover=$!
wait "$manual" || { cat "$scratch/manual"; exit 1; }
wait "$recover" || { cat "$scratch/reconcile"; exit 1; }
grep -q '"already_assigned": 1' "$scratch/reconcile"
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$scratch/check2" <<'SQL'
do $chk$ begin
 if (select count(*) from public.atribuicoes_humanas
   where caso_id='b5020000-0000-4000-8000-000000000002' and encerrada_em is null)<>1
 or (select count(*) from prumo_private.s1_recuperacao_fila_historico
   where caso_id='b5020000-0000-4000-8000-000000000002'
   and resultado='JA_ATRIBUIDO')<>1
 or exists(select 1 from prumo_private.s1_remanejamento_pendencias
   where caso_id='b5020000-0000-4000-8000-000000000002')
 then raise exception 'S1QC-03 conflito com atribuicao simultanea';end if;
end $chk$;
SQL
echo 'PASS S1QC-03: nova atribuicao concorrente vence; recuperacao fecha pendencia stale'
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$scratch/rls" <<'SQL'
begin;
set local role authenticated;
select set_config('request.jwt.claim.sub','b1020000-0000-4000-8000-000000000001',true);
do $chk$ begin
 if exists(select 1 from public.casos_humanos) then
  raise exception 'S1QC-04 suspenso tem acesso';end if;
end $chk$;
select set_config('request.jwt.claim.sub','b1020000-0000-4000-8000-000000000002',true);
do $chk$ begin
 if (select count(*) from public.casos_humanos)<>2 then
  raise exception 'S1QC-04 destinatario perdeu casos';end if;
end $chk$;
rollback;
SQL
echo 'PASS S1QC-04: suspenso sem leitura; dois casos no destino autorizado'
echo 'PASS S1QC: recuperacao concorrente sem duplicar'
