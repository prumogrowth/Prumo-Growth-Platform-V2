#!/usr/bin/env bash
set -euo pipefail
: "$PRUMO_TEST_DATABASE_URL"
python3 - <<'PY'
import os,sys
from urllib.parse import urlparse,unquote
u=urlparse(os.environ['PRUMO_TEST_DATABASE_URL'])
db=unquote((u.path or '').strip('/'))
if u.scheme not in ('postgres','postgresql') or u.hostname not in ('localhost','127.0.0.1','::1') or not db.startswith('prumo_s0_test_'):
 sys.exit('RECUSADO: somente PostgreSQL local descartavel prumo_s0_test_*')
PY
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" > "$work/setup" <<'SQL'
insert into auth.users(id) values
('81020000-0000-4000-8000-000000000001'),
('81020000-0000-4000-8000-000000000002'),
('81020000-0000-4000-8000-000000000003'),
('81020000-0000-4000-8000-000000000004');
insert into public.atores(id) select id from auth.users where id::text like '81020000-%';
insert into public.equipe_prumo_s1(ator_id,estado)
 select id,'ativo' from public.atores where id::text like '81020000-%';
insert into public.concessionarias(id,nome_operacional) values
('82020000-0000-4000-8000-000000000001','S1C loja A sintética'),
('82020000-0000-4000-8000-000000000002','S1C loja B sintética');
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel,valido_ate) values
('81020000-0000-4000-8000-000000000001','82020000-0000-4000-8000-000000000001','operador',null),
('81020000-0000-4000-8000-000000000002','82020000-0000-4000-8000-000000000001','operador',null),
('81020000-0000-4000-8000-000000000003','82020000-0000-4000-8000-000000000001','operador',null),
('81020000-0000-4000-8000-000000000003','82020000-0000-4000-8000-000000000002','operador',statement_timestamp()+interval '1 second'),
('81020000-0000-4000-8000-000000000004','82020000-0000-4000-8000-000000000002','operador',null);
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado)
 select ('83020000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 case when i=5 then '82020000-0000-4000-8000-000000000002'::uuid
 else '82020000-0000-4000-8000-000000000001'::uuid end,
 '+5581987000'||lpad(i::text,4,'0') from generate_series(1,5) i;
insert into public.ciclos_comerciais(id,concessionaria_id,lead_id,status_comercial)
 select ('84020000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 l.concessionaria_id,l.id,'em atendimento pelo operador'
 from generate_series(1,5) i
 join public.leads_loja l on l.id=('83020000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid;
insert into public.casos_humanos(id,concessionaria_id,lead_id,ciclo_id)
 select ('85020000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 c.concessionaria_id,c.lead_id,c.id
 from generate_series(1,5) i
 join public.ciclos_comerciais c on c.id=('84020000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid;
insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id) values
('82020000-0000-4000-8000-000000000001','85020000-0000-4000-8000-000000000001','81020000-0000-4000-8000-000000000001'),
('82020000-0000-4000-8000-000000000001','85020000-0000-4000-8000-000000000003','81020000-0000-4000-8000-000000000002'),
('82020000-0000-4000-8000-000000000001','85020000-0000-4000-8000-000000000004','81020000-0000-4000-8000-000000000003'),
('82020000-0000-4000-8000-000000000002','85020000-0000-4000-8000-000000000005','81020000-0000-4000-8000-000000000003');
SQL
echo 'PASS S1C-01: fixtures A/B e equipe inicialmente validas'
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$work/suspend1" 2>&1 <<'SQL' &
begin;
update public.equipe_prumo_s1 set estado='suspenso'
where ator_id='81020000-0000-4000-8000-000000000001';
select pg_sleep(1.3);
commit;
SQL
one=$!
sleep 0.25
if psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$work/new1" 2>&1 <<'SQL'
insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id)
values('82020000-0000-4000-8000-000000000001',
'85020000-0000-4000-8000-000000000002',
'81020000-0000-4000-8000-000000000001');
SQL
then echo 'FAIL S1C-02: suspenso recebeu caso sem dono'; exit 1
fi
wait "$one"
grep -q 'PROFISSIONAL_PRUMO_INELEGIVEL' "$work/new1"
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$work/check1" <<'SQL'
do $s1$ begin
 if exists(select 1 from public.atribuicoes_humanas
  where operador_id='81020000-0000-4000-8000-000000000001' and encerrada_em is null)
 or (select count(*) from public.atribuicoes_humanas
  where caso_id='85020000-0000-4000-8000-000000000001' and encerrada_em is null)<>1
 or exists(select 1 from public.atribuicoes_humanas
  where caso_id='85020000-0000-4000-8000-000000000002')
 then raise exception 'FAIL S1C-02 estado de carteira';end if;
end $s1$;
SQL
echo 'PASS S1C-02: suspensao prevalece sobre atribuicao concorrente'
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$work/suspend2a" 2>&1 <<'SQL' &
begin;
update public.equipe_prumo_s1 set estado='suspenso'
where ator_id='81020000-0000-4000-8000-000000000002';
select pg_sleep(1.3);
commit;
SQL
a=$!
sleep 0.25
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$work/suspend2b" 2>&1 <<'SQL' &
update public.equipe_prumo_s1 set estado='desligado'
where ator_id='81020000-0000-4000-8000-000000000002';
SQL
b=$!
wait "$a"; wait "$b"
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$work/check2" <<'SQL'
do $s1$ begin
 if (select estado from public.equipe_prumo_s1
  where ator_id='81020000-0000-4000-8000-000000000002')<>'desligado'
 or exists(select 1 from public.atribuicoes_humanas
  where operador_id='81020000-0000-4000-8000-000000000002' and encerrada_em is null)
 or (select count(*) from prumo_private.s1_remanejamento_historico
  where operador_anterior='81020000-0000-4000-8000-000000000002'
  and caso_id='85020000-0000-4000-8000-000000000003')<>1
 then raise exception 'FAIL S1C-03 dupla transicao criou efeito duplicado';end if;
end $s1$;
SQL
echo 'PASS S1C-03: transicoes concorrentes do mesmo profissional sem duplicidade'
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$work/reconA" 2>&1 <<'SQL' &
begin;
select prumo_private.s1_reconciliar_elegibilidade_vencida(10);
select pg_sleep(1.3);
commit;
SQL
x=$!
sleep 0.25
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$work/reconB" 2>&1 <<'SQL' &
select prumo_private.s1_reconciliar_elegibilidade_vencida(10);
SQL
y=$!
wait "$x"; wait "$y"
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$work/check3" <<'SQL'
do $s1$ begin
 if (select count(*) from public.atribuicoes_humanas
  where caso_id='85020000-0000-4000-8000-000000000005' and encerrada_em is null)<>1
 or (select count(*) from public.atribuicoes_humanas
  where caso_id='85020000-0000-4000-8000-000000000005' and encerrada_em is null
  and operador_id='81020000-0000-4000-8000-000000000004')<>1
 or (select count(*) from prumo_private.s1_remanejamento_historico
  where caso_id='85020000-0000-4000-8000-000000000005')<>1
 or (select count(*) from public.ciclos_comerciais
  where id in ('84020000-0000-4000-8000-000000000001',
               '84020000-0000-4000-8000-000000000005')
  and status_comercial='em atendimento pelo operador')<>2
 then raise exception 'FAIL S1C-04 auditoria/reconciliacao concorrente';end if;
end $s1$;
SQL
echo 'PASS S1C-04: duas reconciliacoes concorrentes sem duplicar transferencia'
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$work/check4" <<'SQL'
begin;
set local role authenticated;
select set_config('request.jwt.claim.sub','81020000-0000-4000-8000-000000000004',true);
do $s1$ begin
 begin
  perform prumo_private.s1_reconciliar_elegibilidade_vencida(10);
  raise exception 'FAIL S1C-05 cliente executou reconciliador';
 exception when insufficient_privilege then null;end;
end $s1$;
rollback;
SQL
echo 'PASS S1C-05: API autenticada nao pode executar reparo privado'
echo 'PASS S1C: concorrencia S1-002 local PG17 concluida'
