#!/usr/bin/env bash
set -euo pipefail
: "$PRUMO_TEST_DATABASE_URL"
python3 - <<'PY'
from urllib.parse import urlparse,unquote
import os,sys
u=urlparse(os.environ['PRUMO_TEST_DATABASE_URL'])
if u.scheme not in ('postgres','postgresql') or u.hostname not in ('localhost','127.0.0.1','::1') or not unquote(u.path.strip('/')).startswith('prumo_s0_test_'):
 sys.exit('RECUSADO: apenas banco local descartavel')
PY
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >/dev/null <<'SQL'
insert into auth.users(id) values('e1000000-0000-4000-8000-000000000001');
insert into public.atores(id) values('e1000000-0000-4000-8000-000000000001');
insert into public.concessionarias(id,nome_operacional) values
('e2000000-0000-4000-8000-000000000001','Race ficticia');
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel) values
('e1000000-0000-4000-8000-000000000001','e2000000-0000-4000-8000-000000000001','gestor');
insert into public.canais_loja(id,concessionaria_id,identificador_emissor) values
('e3000000-0000-4000-8000-000000000001','e2000000-0000-4000-8000-000000000001','RACE_SENDER_A');
insert into public.catalogo_templates_sinteticos(id,concessionaria_id,codigo,versao,aprovado_simulacao)
values('e4000000-0000-4000-8000-000000000001','e2000000-0000-4000-8000-000000000001','T',1,true);
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado) values
('e5000000-0000-4000-8000-000000000001','e2000000-0000-4000-8000-000000000001','+5581988800101'),
('e5000000-0000-4000-8000-000000000002','e2000000-0000-4000-8000-000000000001','+5581988800102');
insert into public.ciclos_comerciais(id,concessionaria_id,lead_id) values
('e6000000-0000-4000-8000-000000000001','e2000000-0000-4000-8000-000000000001','e5000000-0000-4000-8000-000000000001'),
('e6000000-0000-4000-8000-000000000002','e2000000-0000-4000-8000-000000000001','e5000000-0000-4000-8000-000000000002');
select prumo_private.agendar_recontatos_sinteticos(
'e1000000-0000-4000-8000-000000000001','e2000000-0000-4000-8000-000000000001',
'e6000000-0000-4000-8000-000000000001','e3000000-0000-4000-8000-000000000001',
'race-a',jsonb_build_array(jsonb_build_object('template_id','e4000000-0000-4000-8000-000000000001',
'agendado_em',(statement_timestamp()+interval '1 day')::text)));
select prumo_private.agendar_recontatos_sinteticos(
'e1000000-0000-4000-8000-000000000001','e2000000-0000-4000-8000-000000000001',
'e6000000-0000-4000-8000-000000000002','e3000000-0000-4000-8000-000000000001',
'race-b',jsonb_build_array(jsonb_build_object('template_id','e4000000-0000-4000-8000-000000000001',
'agendado_em',(statement_timestamp()+interval '1 day')::text)));
SQL
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
# Reservador segura a transacao; inbound bloqueia e depois cancela reserva.
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$tmp/reserva-a" <<'SQL' &
begin;
select prumo_private.reservar_envio_sintetico(
'e2000000-0000-4000-8000-000000000001',
(select e.id from public.envios_template_sinteticos e
 join public.planos_recontato_sinteticos p
 on p.id=e.plano_id and p.concessionaria_id=e.concessionaria_id
 where p.chave_idempotencia='race-a'),statement_timestamp()+interval '2 days');
select pg_sleep(1);
commit;
SQL
one=$!
sleep 0.15
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$tmp/inbound-a" <<'SQL' &
select prumo_private.receber_mensagem_sintetica(
'e3000000-0000-4000-8000-000000000001',
'+5581988800101','RACE-A-1','Resposta ficticia cancela reserva');
SQL
two=$!
wait "$one"; wait "$two"
grep -q 'RESERVED_SIMULATED' "$tmp/reserva-a"
grep -q 'envios_cancelados' "$tmp/inbound-a"
# Inbound detem a transacao; reserva bloqueia e depois ve que ja foi cancelado.
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$tmp/inbound-b" <<'SQL' &
begin;
select prumo_private.receber_mensagem_sintetica(
'e3000000-0000-4000-8000-000000000001',
'+5581988800102','RACE-B-1','Resposta ficticia antes de reserva');
select pg_sleep(1);
commit;
SQL
three=$!
sleep 0.15
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$tmp/reserva-b" <<'SQL' &
select prumo_private.reservar_envio_sintetico(
'e2000000-0000-4000-8000-000000000001',
(select e.id from public.envios_template_sinteticos e
 join public.planos_recontato_sinteticos p
 on p.id=e.plano_id and p.concessionaria_id=e.concessionaria_id
 where p.chave_idempotencia='race-b'),statement_timestamp()+interval '2 days');
SQL
four=$!
wait "$three"; wait "$four"
grep -q 'NOT_ELIGIBLE' "$tmp/reserva-b"
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >/dev/null <<'SQL'
do $verify$ begin
 if (select count(*) from public.planos_recontato_sinteticos
     where chave_idempotencia in ('race-a','race-b') and estado='cancelado')<>2
 or (select count(*) from public.envios_template_sinteticos
     where estado='cancelado' and plano_id in
      (select id from public.planos_recontato_sinteticos
       where chave_idempotencia in ('race-a','race-b')))<>2
 or (select count(*) from public.mensagens
     where id_externo in ('RACE-A-1','RACE-B-1'))<>2
 then raise exception 'FAIL envio obsoleto em corrida inbound'; end if;
end $verify$;
SQL
echo 'PASS REC-RACE: reserva versus inbound serializados sem envio obsoleto'
