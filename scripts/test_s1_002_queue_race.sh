#!/usr/bin/env bash
set -euo pipefail
: "$PRUMO_TEST_DATABASE_URL"
# Recusar conexoes remotas, bancos nao-descartaveis e esquemas externos.
python3 - <<'PY'
import os,sys
from urllib.parse import urlparse, unquote
u=urlparse(os.environ['PRUMO_TEST_DATABASE_URL'])
name=unquote((u.path or '').strip('/'))
if (u.scheme not in ('postgres','postgresql')
    or u.hostname not in ('127.0.0.1','localhost','::1')
    or not name.startswith('prumo_s0_test_')):
    sys.exit('RECUSADO I40: PostgreSQL LOCAL descartavel prumo_s0_test_* obrigatorio')
PY
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" \
 -f supabase/tests/s1_060_fila_race_seed_local_only.sql >"$work/setup"

loja='60220000-0000-4000-8000-000000000001'
c1='60550000-0000-4000-8000-000000000001'
c2='60550000-0000-4000-8000-000000000002'
m1='60110000-0000-4000-8000-000000000001'
m2='60110000-0000-4000-8000-000000000002'
m3='60110000-0000-4000-8000-000000000003'
op='60110000-0000-4000-8000-000000000004'

# Nao basta rodar consultas sequenciais: exigir prova de espera em lock real.
await_lock() {
 local tag="$1" seen=0 n
 for n in $(seq 1 25); do
  seen="$(psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -c \
   "select count(*) from pg_catalog.pg_stat_activity where application_name='$tag' and wait_event_type='Lock' and state='active'")"
  if [[ "$seen" == 1 ]]; then return 0; fi
  sleep 0.09
 done
 echo "FAIL I40: segunda conexao nao bloqueou no S0 case lock ($tag)" >&2
 return 1
}

# Corrida A: dois Gestores autorizados disputam o mesmo lead sem titular.
# Primeira sessao segura caso/fila em transacao aberta durante 2,5 segundos.
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$work/first" 2>&1 <<SQL &
begin;
set local application_name='s1_i40_claim_winner';
select prumo_private.s1_59_assumir('$m1','$loja','$c1',1);
select pg_sleep(2.5);
commit;
SQL
first=$!
sleep 0.20
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$work/second" 2>&1 <<SQL &
set application_name='s1_i40_claim_loser';
select prumo_private.s1_59_assumir('$m2','$loja','$c1',1);
SQL
second=$!
await_lock s1_i40_claim_loser || { cat "$work/first" "$work/second";exit 1; }
wait "$first" || { cat "$work/first";exit 1; }
if wait "$second"; then
 echo 'FAIL I40-CLAIM: duas assuncoes aceitas';cat "$work/second";exit 1
fi
grep -q 'CLAIMED_BY_MANAGER' "$work/first"
grep -q 'FILA_CAS_OBSOLETO' "$work/second"
echo 'PASS I40-01: duas conexoes competiram no lock; um Gestor venceu e CAS recusou o outro'

# Retomada do Consultor permite redistribuir lead ainda sem titular.
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" <<SQL >"$work/resume"
select prumo_private.s1_definir_disponibilidade_leads_10('$m1','$op',false,2);
SQL
grep -q 'INTAKE_RESUMED' "$work/resume"

# Corrida B: dispatcher automatico e Gestor disputam OUTRO caso.
# Nao podem criar um segundo titular nem substituir o primeiro commit.
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$work/dispatch" 2>&1 <<SQL &
begin;
set local application_name='s1_i40_dispatch_winner';
select prumo_private.s1_59_tentar_novo('$loja','$c2');
select pg_sleep(2.5);
commit;
SQL
dispatch=$!
sleep 0.20
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" >"$work/claim_after" 2>&1 <<SQL &
set application_name='s1_i40_dispatch_loser';
select prumo_private.s1_59_assumir('$m2','$loja','$c2',1);
SQL
later=$!
await_lock s1_i40_dispatch_loser || { cat "$work/dispatch" "$work/claim_after";exit 1; }
wait "$dispatch" || { cat "$work/dispatch";exit 1; }
if wait "$later";then
 echo 'FAIL I40-DISPATCH: assuncao manual atropelou atribuicao automatica'
 cat "$work/claim_after";exit 1
fi
grep -q 'ASSIGNED_NEW' "$work/dispatch"
grep -q 'FILA_CAS_OBSOLETO' "$work/claim_after"
echo 'PASS I40-02: dispatcher e Gestor concorreram; primeiro commit manteve titular unico'

# Gestor 3 sem grant da loja continua sem direito; caso 3 segue sem titular.
if psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" \
 -c "select prumo_private.s1_59_assumir('$m3','$loja','60550000-0000-4000-8000-000000000003',1)" \
 >"$work/no_grant" 2>&1; then
 echo 'FAIL I40-03: Gestor sem autorizacao assumiu lead';exit 1
fi
grep -q 'GESTOR_SEM_AUTORIZACAO_LOJA' "$work/no_grant"
psql -X -qAt -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" <<'SQL'
do $check$ begin
 if (select count(*) from public.atribuicoes_humanas a
     where a.caso_id='60550000-0000-4000-8000-000000000001'
     and a.encerrada_em is null
     and a.operador_id='60110000-0000-4000-8000-000000000001')<>1
 or (select count(*) from public.atribuicoes_humanas a
     where a.caso_id='60550000-0000-4000-8000-000000000002'
     and a.encerrada_em is null
     and a.operador_id='60110000-0000-4000-8000-000000000004')<>1
 or exists(select 1 from public.atribuicoes_humanas a
     where a.caso_id='60550000-0000-4000-8000-000000000003')
 or (select count(*) from public.atribuicoes_humanas
     where caso_id::text like '60550000-%' and encerrada_em is null)<>2
 or (select count(*) from public.s1_fila_novos_59
     where estado='PENDENTE')<>1
 or (select count(*) from public.s1_fila_novos_59
     where estado='ATRIBUIDO' and versao=2 and atribuicao_id is not null)<>2
 or (select estado from public.equipe_prumo_s1
     where ator_id='60110000-0000-4000-8000-000000000004')<>'ativo'
 then raise exception 'I40-VERIFY: ownership, fila, CAS ou conta divergentes';end if;
end $check$;
SQL
echo 'PASS I40-03/04: Gestor nao autorizado negado, fila remanescente, dois casos com titular unico'
echo 'PASS I40: 2 corridas reais em sessoes independentes, PG17 descartavel, nenhuma migration/deploy'
