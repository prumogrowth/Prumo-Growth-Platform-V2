#!/usr/bin/env bash
set -euo pipefail
: "$PRUMO_TEST_DATABASE_URL"
python3 - <<'PY'
from urllib.parse import urlparse,unquote
import os,sys
u=urlparse(os.environ['PRUMO_TEST_DATABASE_URL'])
if u.scheme not in ('postgres','postgresql') or u.hostname not in ('localhost','127.0.0.1','::1') or not unquote(u.path.strip('/')).startswith('prumo_s0_test_'):
 sys.exit('RECUSADO: apenas localhost/prumo_s0_test_*')
PY
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >/dev/null <<'SQL'
insert into auth.users(id) values('d1000000-0000-4000-8000-000000000091');
insert into public.atores(id) values('d1000000-0000-4000-8000-000000000091');
insert into public.concessionarias(id,nome_operacional) values
('d2000000-0000-4000-8000-000000000091','Reconciliacao concorrente ficticia');
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel) values
('d1000000-0000-4000-8000-000000000091',
 'd2000000-0000-4000-8000-000000000091','gestor');
insert into public.canais_loja(id,concessionaria_id,identificador_emissor) values
('d3000000-0000-4000-8000-000000000091',
 'd2000000-0000-4000-8000-000000000091','C07_RECON_RACE_CHANNEL');
select prumo_private.registrar_callback_c07_sintetico(
'd3000000-0000-4000-8000-000000000091','unknown-synth-race',
'race-event-1','INCERTO_SIMULADO',statement_timestamp());
SQL

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$tmp/first" <<'SQL' &
begin;
select prumo_private.conciliar_pendencia_c07_sintetica(
'd1000000-0000-4000-8000-000000000091',
'd2000000-0000-4000-8000-000000000091',
(select id from public.pendencias_reconciliacao_c07_sinteticas
 where concessionaria_id='d2000000-0000-4000-8000-000000000091'),
1,'ENCERRAR_SEM_PROVA','Investigacao ficticia sem comprovacao externa',null);
select pg_sleep(1);
commit;
SQL
one=$!
sleep 0.15
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$tmp/second" <<'SQL' &
select prumo_private.conciliar_pendencia_c07_sintetica(
'd1000000-0000-4000-8000-000000000091',
'd2000000-0000-4000-8000-000000000091',
(select id from public.pendencias_reconciliacao_c07_sinteticas
 where concessionaria_id='d2000000-0000-4000-8000-000000000091'),
1,'ENCERRAR_SEM_PROVA','Investigacao ficticia sem comprovacao externa',null);
SQL
two=$!
wait "$one"; wait "$two"
grep -q '"outcome": "APPLIED"' "$tmp/first"
grep -q '"outcome": "ALREADY_APPLIED"' "$tmp/second"
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >/dev/null <<'SQL'
do $verify$ begin
 if (select count(*) from public.auditoria_reconciliacao_c07_sintetica
 where concessionaria_id='d2000000-0000-4000-8000-000000000091')<>1
 or (select count(*) from public.pendencias_reconciliacao_c07_sinteticas
 where concessionaria_id='d2000000-0000-4000-8000-000000000091'
 and estado='encerrada' and versao=2)<>1
 or (select count(*) from public.eventos_callback_sinteticos
 where concessionaria_id='d2000000-0000-4000-8000-000000000091')<>1
 then raise exception 'FAIL C07 two concurrent reviewers caused duplicate decision';end if;
end $verify$;
SQL
echo 'PASS C07-REC-RACE: duas revisoes concorrentes, uma auditoria, versao unica'
