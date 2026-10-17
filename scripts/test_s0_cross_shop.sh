#!/usr/bin/env bash
set -euo pipefail
: "$PRUMO_TEST_DATABASE_URL"
python3 - <<'PY'
from urllib.parse import urlparse,unquote
import os,sys
u=urlparse(os.environ["PRUMO_TEST_DATABASE_URL"])
if u.scheme not in ("postgres","postgresql") or u.hostname not in ("localhost","127.0.0.1","::1") or not unquote(u.path.strip("/")).startswith("prumo_s0_test_"):
 sys.exit("RECUSADO: somente banco local prumo_s0_test_*")
PY
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >/dev/null <<'SQL'
insert into auth.users(id) values
('93000000-0000-4000-8000-000000000041'),
('93000000-0000-4000-8000-000000000042');
insert into public.atores(id) values
('93000000-0000-4000-8000-000000000041'),
('93000000-0000-4000-8000-000000000042');
insert into public.concessionarias(id,nome_operacional) values
('93000000-0000-4000-8000-000000000043','A concorrente'),
('93000000-0000-4000-8000-000000000044','B concorrente');
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel) values
('93000000-0000-4000-8000-000000000041','93000000-0000-4000-8000-000000000043','gestor'),
('93000000-0000-4000-8000-000000000042','93000000-0000-4000-8000-000000000044','gestor');
SQL
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" <<'SQL' >/dev/null &
begin;
select prumo_private.importar_lote_sintetico(
'93000000-0000-4000-8000-000000000041','93000000-0000-4000-8000-000000000043',
'LOTE-A','[{"telefone":"+5519999990000"}]'::jsonb);
select pg_sleep(1);
commit;
SQL
one=$!
sleep 0.15
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" <<'SQL' >/dev/null &
select prumo_private.importar_lote_sintetico(
'93000000-0000-4000-8000-000000000042','93000000-0000-4000-8000-000000000044',
'LOTE-B','[{"telefone":"+5519999990000"}]'::jsonb);
SQL
two=$!
wait "$one"
wait "$two"
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" <<'SQL' >/dev/null
do $verify$
begin
 if (select count(*) from public.leads_loja
     where telefone_cliente_normalizado='+5519999990000')<>2
 or (select count(distinct concessionaria_id) from public.leads_loja
     where telefone_cliente_normalizado='+5519999990000')<>2
 or (select count(*) from public.itens_lote
     where resultado='aceito' and concessionaria_id in
     ('93000000-0000-4000-8000-000000000043','93000000-0000-4000-8000-000000000044'))<>2
 or (select count(*) from public.itens_lote
     where resultado='rejeitado' and concessionaria_id in
     ('93000000-0000-4000-8000-000000000043','93000000-0000-4000-8000-000000000044'))<>0
 or (select count(*) from public.ciclos_comerciais
     where concessionaria_id in
     ('93000000-0000-4000-8000-000000000043','93000000-0000-4000-8000-000000000044'))<>2
 then raise exception 'FAIL: mesmo cliente deve criar registros isolados em A e B'; end if;
end $verify$;
begin;
set local role authenticated;
select set_config('request.jwt.claim.sub','93000000-0000-4000-8000-000000000041',true);
do $a$
begin
 if (select count(*) from public.leads_loja where telefone_cliente_normalizado='+5519999990000')<>1
 or (select count(*) from public.ciclos_comerciais)<>1
 then raise exception 'FAIL: gestor A enxerga registros de B'; end if;
end $a$;
select set_config('request.jwt.claim.sub','93000000-0000-4000-8000-000000000042',true);
do $b$
begin
 if (select count(*) from public.leads_loja where telefone_cliente_normalizado='+5519999990000')<>1
 or (select count(*) from public.ciclos_comerciais)<>1
 then raise exception 'FAIL: gestor B enxerga registros de A'; end if;
end $b$;
rollback;
SQL
echo 'PASS TX-CROSS-SHOP: mesmo cliente em A e B sob concorrencia; historicos isolados'
