#!/usr/bin/env bash
set -euo pipefail
: "$PRUMO_TEST_DATABASE_URL"
python3 - <<'PY'
import os,sys
from urllib.parse import urlparse,unquote
u=urlparse(os.environ['PRUMO_TEST_DATABASE_URL'])
if u.scheme not in ('postgres','postgresql') or u.hostname not in ('localhost','127.0.0.1','::1') or not unquote((u.path or '').strip('/')).startswith('prumo_s0_test_'):
 sys.exit('RECUSADO: somente PG local descartavel prumo_s0_test_*')
PY
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$work/setup" <<'SQL'
insert into auth.users(id)
 select ('91020000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid
 from generate_series(1,5) i;
insert into public.atores(id) select id from auth.users where id::text like '91020000-%';
insert into public.equipe_prumo_s1(ator_id,estado)
 select id,'ativo' from public.atores where id::text like '91020000-%';
insert into public.concessionarias(id,nome_operacional) values
 ('92020000-0000-4000-8000-000000000001','S1D loja A teste'),
 ('92020000-0000-4000-8000-000000000002','S1D loja B teste');
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel)
 select ('91020000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 case when i<=3 then '92020000-0000-4000-8000-000000000001'::uuid
 else '92020000-0000-4000-8000-000000000002'::uuid end,'operador'
 from generate_series(1,5) i;
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado)
 select ('93020000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 case when i<=6 then '92020000-0000-4000-8000-000000000001'::uuid
 else '92020000-0000-4000-8000-000000000002'::uuid end,
 '+5581988000'||lpad(i::text,4,'0') from generate_series(1,8) i;
insert into public.ciclos_comerciais(id,concessionaria_id,lead_id,status_comercial)
 select ('94020000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 l.concessionaria_id,l.id,'em atendimento pelo operador'
 from generate_series(1,8) i join public.leads_loja l
 on l.id=('93020000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid;
insert into public.casos_humanos(id,concessionaria_id,lead_id,ciclo_id)
 select ('95020000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 c.concessionaria_id,c.lead_id,c.id
 from generate_series(1,8) i join public.ciclos_comerciais c
 on c.id=('94020000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid;
insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id)
 select h.concessionaria_id,h.id,
 ('91020000-0000-4000-8000-'||lpad((case when i=1 then 1 when i=2 then 2
 when i<=6 then 3 when i=7 then 4 else 5 end)::text,12,'0'))::uuid
 from generate_series(1,8) i join public.casos_humanos h
 on h.id=('95020000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid;
SQL
echo 'PASS S1D-01: A com substituto sobrecarregado, B com apenas dois operadores'
# Cada transacao segura o proprio ator, aguarda a outra sessao, depois
# suspende. O candidato mutuo bloqueado deve ser IGNORADO, sem deadlock.
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$work/A1" 2>&1 <<'SQL' &
begin;
select ator_id from public.equipe_prumo_s1
 where ator_id='91020000-0000-4000-8000-000000000001' for update;
select pg_sleep(1);
update public.equipe_prumo_s1 set estado='suspenso'
 where ator_id='91020000-0000-4000-8000-000000000001';
commit;
SQL
a=$!
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$work/A2" 2>&1 <<'SQL' &
begin;
select ator_id from public.equipe_prumo_s1
 where ator_id='91020000-0000-4000-8000-000000000002' for update;
select pg_sleep(1);
update public.equipe_prumo_s1 set estado='suspenso'
 where ator_id='91020000-0000-4000-8000-000000000002';
commit;
SQL
b=$!
wait "$a" || { cat "$work/A1"; exit 1; }
wait "$b" || { cat "$work/A2"; exit 1; }
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$work/checkA" <<'SQL'
do $t$ begin
 if (select count(*) from public.atribuicoes_humanas
 where concessionaria_id='92020000-0000-4000-8000-000000000001'
  and encerrada_em is null
  and operador_id='91020000-0000-4000-8000-000000000003')<>6
 or (select count(*) from prumo_private.s1_remanejamento_historico
 where concessionaria_id='92020000-0000-4000-8000-000000000001'
 and resultado='REDISTRIBUIDO')<>2
 or exists(select 1 from prumo_private.s1_remanejamento_pendencias
 where concessionaria_id='92020000-0000-4000-8000-000000000001')
 then raise exception 'S1D-02 falha simultanea com substituto elegivel';end if;
end $t$;
SQL
echo 'PASS S1D-02: suspensoes simultaneas ignoram candidato bloqueado sem deadlock'
# Mesmo evento concorrente, agora NENHUM outro operador B existe.
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$work/B4" 2>&1 <<'SQL' &
begin;
select ator_id from public.equipe_prumo_s1
 where ator_id='91020000-0000-4000-8000-000000000004' for update;
select pg_sleep(1);
update public.equipe_prumo_s1 set estado='suspenso'
 where ator_id='91020000-0000-4000-8000-000000000004';
commit;
SQL
c=$!
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$work/B5" 2>&1 <<'SQL' &
begin;
select ator_id from public.equipe_prumo_s1
 where ator_id='91020000-0000-4000-8000-000000000005' for update;
select pg_sleep(1);
update public.equipe_prumo_s1 set estado='suspenso'
 where ator_id='91020000-0000-4000-8000-000000000005';
commit;
SQL
d=$!
wait "$c" || { cat "$work/B4"; exit 1; }
wait "$d" || { cat "$work/B5"; exit 1; }
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$work/checkB" <<'SQL'
do $t$ begin
 if exists(select 1 from public.atribuicoes_humanas
 where concessionaria_id='92020000-0000-4000-8000-000000000002'
 and encerrada_em is null)
 or (select count(*) from prumo_private.s1_remanejamento_pendencias
 where concessionaria_id='92020000-0000-4000-8000-000000000002')<>2
 or (select count(*) from prumo_private.s1_remanejamento_historico
 where concessionaria_id='92020000-0000-4000-8000-000000000002'
 and resultado='FILA_PROTEGIDA')<>2
 then raise exception 'S1D-03 atribuiu a suspenso ou perdeu fila';end if;
end $t$;
SQL
echo 'PASS S1D-03: suspensoes simultaneas sem substituto criam fila protegida'
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$work/rls" <<'SQL'
begin;
set local role authenticated;
select set_config('request.jwt.claim.sub','91020000-0000-4000-8000-000000000001',true);
do $t$ begin
 if exists(select 1 from public.casos_humanos) then
  raise exception 'S1D-04 suspenso ainda tem caso';end if;
end $t$;
select set_config('request.jwt.claim.sub','91020000-0000-4000-8000-000000000003',true);
do $t$ begin
 if (select count(*) from public.casos_humanos)<>6
 then raise exception 'S1D-04 destinatario nao tem seis casos';end if;
end $t$;
rollback;
SQL
echo 'PASS S1D-04: RLS de suspensos e receptor respeita loja'
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$work/idempotent" <<'SQL'
do $t$ declare r jsonb;begin
 r:=prumo_private.s1_reconciliar_elegibilidade_vencida(100);
 if (r->>'cases_reassigned_or_closed')::integer<>0
 or (select count(*) from prumo_private.s1_remanejamento_historico)<>4
 then raise exception 'S1D-05 duplicacao em reconciliação %',r;end if;
end $t$;
SQL
echo 'PASS S1D-05: reexecucao nao duplica historico e mantém filas'
echo 'PASS S1D: corridas de dois desligamentos/suspensoes testadas'
