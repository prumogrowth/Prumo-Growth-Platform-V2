#!/usr/bin/env bash
set -euo pipefail
: "$PRUMO_TEST_DATABASE_URL"
python3 - <<'PY'
from urllib.parse import urlparse, unquote
import os,sys
u=urlparse(os.environ['PRUMO_TEST_DATABASE_URL'])
if u.scheme not in ('postgres','postgresql') or u.hostname not in ('localhost','127.0.0.1','::1') or not unquote(u.path.strip('/')).startswith('prumo_s0_test_'):
 sys.exit('Somente PostgreSQL local prumo_s0_test_*')
PY
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >/dev/null <<'SQL'
insert into auth.users(id) values('f1000000-0000-4000-8000-000000000071');
insert into public.atores(id) values('f1000000-0000-4000-8000-000000000071');
insert into public.concessionarias(id,nome_operacional) values
('f2000000-0000-4000-8000-000000000071','Corrida C04 ficticia');
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel) values
('f1000000-0000-4000-8000-000000000071','f2000000-0000-4000-8000-000000000071','gestor');
insert into public.canais_loja(id,concessionaria_id,identificador_emissor) values
('f3000000-0000-4000-8000-000000000071','f2000000-0000-4000-8000-000000000071','CANAL_RACE_C04');
insert into public.catalogo_templates_sinteticos(id,concessionaria_id,codigo,versao,aprovado_simulacao)
values('f4000000-0000-4000-8000-000000000071','f2000000-0000-4000-8000-000000000071','TMP',1,true);
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado) values
('f5000000-0000-4000-8000-000000000071','f2000000-0000-4000-8000-000000000071','+5581877710001'),
('f5000000-0000-4000-8000-000000000072','f2000000-0000-4000-8000-000000000071','+5581877710002');
insert into public.ciclos_comerciais(id,concessionaria_id,lead_id) values
('f6000000-0000-4000-8000-000000000071','f2000000-0000-4000-8000-000000000071','f5000000-0000-4000-8000-000000000071'),
('f6000000-0000-4000-8000-000000000072','f2000000-0000-4000-8000-000000000071','f5000000-0000-4000-8000-000000000072');
insert into public.evidencias_elegibilidade_sinteticas(
 concessionaria_id,lead_id,canal_id,finalidade,referencia_ficticia)
values
('f2000000-0000-4000-8000-000000000071','f5000000-0000-4000-8000-000000000071',
'f3000000-0000-4000-8000-000000000071','recontato_comercial_sintetico','EVIDENCIA_FICTICIA_RACE_1'),
('f2000000-0000-4000-8000-000000000071','f5000000-0000-4000-8000-000000000072',
'f3000000-0000-4000-8000-000000000071','recontato_comercial_sintetico','EVIDENCIA_FICTICIA_RACE_2');
select prumo_private.agendar_recontatos_sinteticos(
'f1000000-0000-4000-8000-000000000071','f2000000-0000-4000-8000-000000000071',
'f6000000-0000-4000-8000-000000000071','f3000000-0000-4000-8000-000000000071',
'C04-RACE-1',jsonb_build_array(jsonb_build_object('template_id','f4000000-0000-4000-8000-000000000071',
'agendado_em',(statement_timestamp()+interval '1 day')::text)));
select prumo_private.agendar_recontatos_sinteticos(
'f1000000-0000-4000-8000-000000000071','f2000000-0000-4000-8000-000000000071',
'f6000000-0000-4000-8000-000000000072','f3000000-0000-4000-8000-000000000071',
'C04-RACE-2',jsonb_build_array(jsonb_build_object('template_id','f4000000-0000-4000-8000-000000000071',
'agendado_em',(statement_timestamp()+interval '1 day')::text)));
SQL
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$tmp/reserve1" <<'SQL' &
begin;
select prumo_private.reservar_envio_sintetico(
'f2000000-0000-4000-8000-000000000071',
(select e.id from public.envios_template_sinteticos e
join public.planos_recontato_sinteticos p on p.id=e.plano_id and p.concessionaria_id=e.concessionaria_id
where p.chave_idempotencia='C04-RACE-1'),statement_timestamp()+interval '3 days');
select pg_sleep(1);
commit;
SQL
one=$!
sleep 0.15
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$tmp/optout1" <<'SQL' &
select prumo_private.registrar_optout_sintetico(
'f2000000-0000-4000-8000-000000000071','f5000000-0000-4000-8000-000000000071',
'f3000000-0000-4000-8000-000000000071','recontato_comercial_sintetico','RACE-OUT-1');
SQL
two=$!
wait "$one"; wait "$two"
grep -q 'RESERVED_SIMULATED' "$tmp/reserve1"
grep -q 'envios_cancelados' "$tmp/optout1"
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$tmp/optout2" <<'SQL' &
begin;
select prumo_private.registrar_optout_sintetico(
'f2000000-0000-4000-8000-000000000071','f5000000-0000-4000-8000-000000000072',
'f3000000-0000-4000-8000-000000000071','recontato_comercial_sintetico','RACE-OUT-2');
select pg_sleep(1);
commit;
SQL
three=$!
sleep 0.15
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$tmp/reserve2" <<'SQL' &
select prumo_private.reservar_envio_sintetico(
'f2000000-0000-4000-8000-000000000071',
(select e.id from public.envios_template_sinteticos e
join public.planos_recontato_sinteticos p on p.id=e.plano_id and p.concessionaria_id=e.concessionaria_id
where p.chave_idempotencia='C04-RACE-2'),statement_timestamp()+interval '3 days');
SQL
four=$!
wait "$three"; wait "$four"
grep -q 'NOT_ELIGIBLE' "$tmp/reserve2"
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >/dev/null <<'SQL'
do $race$
begin
 if (select count(*) from public.supressoes_contato_sinteticas
 where evento_origem in ('RACE-OUT-1','RACE-OUT-2'))<>2
 or (select count(*) from public.planos_recontato_sinteticos
 where chave_idempotencia in ('C04-RACE-1','C04-RACE-2') and estado='cancelado')<>2
 or (select count(*) from public.envios_template_sinteticos
 where estado='cancelado' and plano_id in
 (select id from public.planos_recontato_sinteticos
 where chave_idempotencia in ('C04-RACE-1','C04-RACE-2')))<>2
 then raise exception 'FAIL C04 optout-race';end if;
end $race$;
SQL
echo 'PASS C04-RACE: duas ordens reserva versus optout, sem envio elegivel'
