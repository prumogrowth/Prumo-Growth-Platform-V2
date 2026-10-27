\set ON_ERROR_STOP on
-- S0-037D: disposable authorization-capability proof.
-- NO production token, gateway authorization, owner transfer, or migration.
-- ALL ROLE, GRANT, POLICY, capability rows and fixtures ROLLBACK.
begin;
create role prumo_s0_probe_037d nologin noinherit
 nosuperuser nocreatedb nocreaterole noreplication nobypassrls;
grant usage on schema public to prumo_s0_probe_037d;

insert into auth.users(id) values
 ('c4050000-0000-4000-8000-000000000001');
insert into public.atores(id) values
 ('c4050000-0000-4000-8000-000000000001');
insert into public.concessionarias(id,nome_operacional) values
 ('c4000000-0000-4000-8000-000000000001','037D loja A'),
 ('c4000000-0000-4000-8000-000000000002','037D loja B');
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado) values
 ('c4010000-0000-4000-8000-000000000001','c4000000-0000-4000-8000-000000000001','+5581999003737'),
 ('c4010000-0000-4000-8000-000000000002','c4000000-0000-4000-8000-000000000002','+5581999003737');
insert into public.ciclos_comerciais(id,concessionaria_id,lead_id) values
 ('c4020000-0000-4000-8000-000000000001','c4000000-0000-4000-8000-000000000001','c4010000-0000-4000-8000-000000000001'),
 ('c4020000-0000-4000-8000-000000000002','c4000000-0000-4000-8000-000000000002','c4010000-0000-4000-8000-000000000002');
insert into public.canais_loja(id,concessionaria_id,identificador_emissor) values
 ('c4030000-0000-4000-8000-000000000001','c4000000-0000-4000-8000-000000000001','037D_EMISSOR_A'),
 ('c4030000-0000-4000-8000-000000000002','c4000000-0000-4000-8000-000000000002','037D_EMISSOR_B');
insert into public.planos_recontato_sinteticos(
 id,concessionaria_id,lead_id,ciclo_id,canal_id,chave_idempotencia,fingerprint)
 values
 ('c4040000-0000-4000-8000-000000000001','c4000000-0000-4000-8000-000000000001',
 'c4010000-0000-4000-8000-000000000001','c4020000-0000-4000-8000-000000000001',
 'c4030000-0000-4000-8000-000000000001','037D_A',repeat('a',64)),
 ('c4040000-0000-4000-8000-000000000002','c4000000-0000-4000-8000-000000000002',
 'c4010000-0000-4000-8000-000000000002','c4020000-0000-4000-8000-000000000002',
 'c4030000-0000-4000-8000-000000000002','037D_B',repeat('b',64));
select prumo_private.registrar_callback_c07_sintetico(
 'c4030000-0000-4000-8000-000000000001','037D_A_CLOSE',
 '037D_EVT_CLOSE','INCERTO_SIMULADO',statement_timestamp());
select prumo_private.registrar_callback_c07_sintetico(
 'c4030000-0000-4000-8000-000000000001','037D_A_LINK',
 '037D_EVT_LINK','ENTREGUE_SIMULADO',statement_timestamp());
select prumo_private.registrar_callback_c07_sintetico(
 'c4030000-0000-4000-8000-000000000002','037D_B',
 '037D_EVT_B','INCERTO_SIMULADO',statement_timestamp());

-- Test-only capability ledger. It is NOT an operational trust root.
-- Only test postgres can INSERT or change it; the probe can SELECT.
create temporary table issued_scope_037d(
 acao text not null, concessionaria_id uuid not null, alvo_id uuid not null,
 versao_esperada bigint not null, txid bigint not null, autorizado_por text not null,
 primary key(acao,concessionaria_id,alvo_id,versao_esperada)
) on commit drop;
revoke all on pg_temp.issued_scope_037d from public;
grant select on pg_temp.issued_scope_037d to prumo_s0_probe_037d;

grant select on public.planos_recontato_sinteticos,
 public.pendencias_reconciliacao_c07_sinteticas to prumo_s0_probe_037d;
grant update(estado,versao,motivo_cancelamento,cancelado_em)
 on public.planos_recontato_sinteticos to prumo_s0_probe_037d;
grant update(estado,versao,decisao,justificativa,revisado_por,encerrado_em)
 on public.pendencias_reconciliacao_c07_sinteticas to prumo_s0_probe_037d;

-- Policy checks a protected row plus transaction identity, never client GUC.
-- UPDATE predicate matches OLD version; WITH CHECK matches NEW version.
create policy owner37d_plan_read on public.planos_recontato_sinteticos
 for select to prumo_s0_probe_037d using (
 exists(select 1 from pg_temp.issued_scope_037d c
 where c.acao='C08_CANCELAR' and c.concessionaria_id=planos_recontato_sinteticos.concessionaria_id
 and c.alvo_id=planos_recontato_sinteticos.id and c.txid=txid_current())
);
create policy owner37d_plan_write on public.planos_recontato_sinteticos
 for update to prumo_s0_probe_037d using (
 exists(select 1 from pg_temp.issued_scope_037d c
 where c.acao='C08_CANCELAR' and c.concessionaria_id=planos_recontato_sinteticos.concessionaria_id
 and c.alvo_id=planos_recontato_sinteticos.id and c.versao_esperada=planos_recontato_sinteticos.versao and c.txid=txid_current())
) with check (
 estado='cancelado' and motivo_cancelamento='cancelamento_gestor'
 and exists(select 1 from pg_temp.issued_scope_037d c
 where c.acao='C08_CANCELAR' and c.concessionaria_id=planos_recontato_sinteticos.concessionaria_id
 and c.alvo_id=planos_recontato_sinteticos.id and planos_recontato_sinteticos.versao=c.versao_esperada+1 and c.txid=txid_current())
);
create policy owner37d_pending_read on public.pendencias_reconciliacao_c07_sinteticas
 for select to prumo_s0_probe_037d using(
 exists(select 1 from pg_temp.issued_scope_037d c
 where c.acao in ('C07_ENCERRAR','C07_VINCULAR')
 and c.concessionaria_id=pendencias_reconciliacao_c07_sinteticas.concessionaria_id and c.alvo_id=pendencias_reconciliacao_c07_sinteticas.id
 and c.txid=txid_current())
);
create policy owner37d_pending_write on public.pendencias_reconciliacao_c07_sinteticas
 for update to prumo_s0_probe_037d using(
 exists(select 1 from pg_temp.issued_scope_037d c
 where c.acao in ('C07_ENCERRAR','C07_VINCULAR')
 and c.concessionaria_id=pendencias_reconciliacao_c07_sinteticas.concessionaria_id and c.alvo_id=pendencias_reconciliacao_c07_sinteticas.id
 and c.versao_esperada=pendencias_reconciliacao_c07_sinteticas.versao and c.txid=txid_current())
) with check(
 estado='encerrada' and exists(select 1 from pg_temp.issued_scope_037d c
 where c.concessionaria_id=pendencias_reconciliacao_c07_sinteticas.concessionaria_id and c.alvo_id=pendencias_reconciliacao_c07_sinteticas.id
 and c.versao_esperada+1=pendencias_reconciliacao_c07_sinteticas.versao and c.txid=txid_current()
 and ((c.acao='C07_ENCERRAR' and decisao='ENCERRAR_SEM_PROVA')
  or (c.acao='C07_VINCULAR' and decisao='VINCULAR_SINTETICAMENTE')))
);

-- Deliberately falsify application-provided GUC: it is NOT authorization.
set local role prumo_s0_probe_037d;
select set_config('prumo.user_loja','c4000000-0000-4000-8000-000000000002',true);
select set_config('prumo.user_acao','C08_CANCELAR',true);
do $negative$
declare n int;
begin
 if (select count(*) from public.planos_recontato_sinteticos
    where id='c4040000-0000-4000-8000-000000000002')<>0
 then raise exception 'FAIL OWNER37D-01: client GUC opened tenant B';end if;
 update public.planos_recontato_sinteticos set estado='cancelado',
  motivo_cancelamento='cancelamento_gestor',versao=versao+1
 where id='c4040000-0000-4000-8000-000000000002';
 get diagnostics n=row_count;
 if n<>0 then raise exception 'FAIL OWNER37D-01: forged GUC allowed write';end if;
 begin
  insert into pg_temp.issued_scope_037d
   values('C08_CANCELAR','c4000000-0000-4000-8000-000000000002',
   'c4040000-0000-4000-8000-000000000002',1,txid_current(),'FORGED');
  raise exception 'FAIL OWNER37D-01: probe forged capability';
 exception when insufficient_privilege then null;end;
end $negative$;
reset role;
\echo 'PASS OWNER37D-01: forged GUC and direct capability insertion denied'

-- Fixtures deliberately issued by postgres ONLY. This does not prove
-- future HMAC/session issuer, which remains a blocker for a real design.
insert into pg_temp.issued_scope_037d values
 ('C08_CANCELAR','c4000000-0000-4000-8000-000000000001',
  'c4040000-0000-4000-8000-000000000001',1,txid_current(),'FIXTURE_POSTGRES');
insert into pg_temp.issued_scope_037d
select 'C07_ENCERRAR',p.concessionaria_id,p.id,p.versao,txid_current(),'FIXTURE_POSTGRES'
 from public.pendencias_reconciliacao_c07_sinteticas p
 join public.eventos_callback_sinteticos e
  on e.concessionaria_id=p.concessionaria_id and e.id=p.evento_id
 where e.evento_externo_ficticio='037D_EVT_CLOSE';
insert into pg_temp.issued_scope_037d
select 'C07_VINCULAR',p.concessionaria_id,p.id,p.versao,txid_current(),'FIXTURE_POSTGRES'
 from public.pendencias_reconciliacao_c07_sinteticas p
 join public.eventos_callback_sinteticos e
  on e.concessionaria_id=p.concessionaria_id and e.id=p.evento_id
 where e.evento_externo_ficticio='037D_EVT_LINK';

do $check$
begin
 if (select count(*) from pg_temp.issued_scope_037d)<>3
 then raise exception 'FAIL OWNER37D-02: incorrect fixture capabilities';end if;
end $check$;
set local role prumo_s0_probe_037d;
do $apply$
declare n integer;
begin
 -- Even with a capability for A, altered GUC still cannot open B.
 update public.planos_recontato_sinteticos
 set estado='cancelado',motivo_cancelamento='cancelamento_gestor',
     versao=versao+1,cancelado_em=statement_timestamp()
 where id='c4040000-0000-4000-8000-000000000002' and versao=1;
 get diagnostics n=row_count;
 if n<>0 then raise exception 'FAIL OWNER37D-02: cross-shop plan update';end if;
 update public.planos_recontato_sinteticos
 set estado='cancelado',motivo_cancelamento='cancelamento_gestor',
     versao=versao+1,cancelado_em=statement_timestamp()
 where id='c4040000-0000-4000-8000-000000000001' and versao=1;
 get diagnostics n=row_count;
 if n<>1 then raise exception 'FAIL OWNER37D-02: scoped versioned C08';end if;
 update public.planos_recontato_sinteticos
 set estado='cancelado',motivo_cancelamento='cancelamento_gestor',
     versao=versao+1,cancelado_em=statement_timestamp()
 where id='c4040000-0000-4000-8000-000000000001' and versao=1;
 get diagnostics n=row_count;
 if n<>0 then raise exception 'FAIL OWNER37D-02: replay not blocked';end if;
end $apply$;
reset role;
\echo 'PASS OWNER37D-02: capability permits only A target/version and rejects replay/B'

set local role prumo_s0_probe_037d;
do $apply$
declare n integer;v_id uuid;
begin
 update public.pendencias_reconciliacao_c07_sinteticas p
 set estado='encerrada',versao=p.versao+1,decisao='ENCERRAR_SEM_PROVA',
  justificativa='Teste 037D de encerramento sem prova',
  revisado_por='c4050000-0000-4000-8000-000000000001',encerrado_em=statement_timestamp()
 where p.id in (
  select x.alvo_id from pg_temp.issued_scope_037d x
  where x.acao='C07_ENCERRAR'
 ) and p.versao=1;
 get diagnostics n=row_count;
 if n<>1 then raise exception 'FAIL OWNER37D-03: C07 close capability';end if;
 begin
  update public.pendencias_reconciliacao_c07_sinteticas p
  set estado='encerrada',versao=p.versao+1,decisao='ENCERRAR_SEM_PROVA',
   justificativa='Wrong action for link',
   revisado_por='c4050000-0000-4000-8000-000000000001',encerrado_em=statement_timestamp()
  where p.id in (
   select x.alvo_id from pg_temp.issued_scope_037d x
   where x.acao='C07_VINCULAR'
  ) and p.versao=1;
  get diagnostics n=row_count;
  if n<>0 then raise exception 'FAIL OWNER37D-03: wrong action accepted';end if;
 exception when insufficient_privilege then null;end;
 update public.pendencias_reconciliacao_c07_sinteticas p
 set estado='encerrada',versao=p.versao+1,decisao='VINCULAR_SINTETICAMENTE',
  justificativa='Teste 037D de vinculo ficticio',
  revisado_por='c4050000-0000-4000-8000-000000000001',encerrado_em=statement_timestamp()
 where p.id in (
  select x.alvo_id from pg_temp.issued_scope_037d x
  where x.acao='C07_VINCULAR'
 ) and p.versao=1;
 get diagnostics n=row_count;
 if n<>1 then raise exception 'FAIL OWNER37D-03: C07 link capability';end if;
 update public.pendencias_reconciliacao_c07_sinteticas
 set estado='encerrada',versao=versao+1,decisao='ENCERRAR_SEM_PROVA'
 where concessionaria_id='c4000000-0000-4000-8000-000000000002';
 get diagnostics n=row_count;
 if n<>0 then raise exception 'FAIL OWNER37D-03: C07 tenant B update';end if;
end $apply$;
reset role;
\echo 'PASS OWNER37D-03: C07 close/link action-bound updates and B isolation'

-- This deliberately FAIL-CLOSED for use as production: capabilities are
-- issued by postgres test code and direct UPDATE still lacks business
-- transaction, session lock, HMAC, private audit and callback link integrity.
do $gate$
begin
 if (select count(*) from pg_temp.issued_scope_037d)<>3
 or exists(select 1 from public.planos_recontato_sinteticos
  where id='c4040000-0000-4000-8000-000000000002' and estado<>'ativo')
 or (select count(*) from public.pendencias_reconciliacao_c07_sinteticas
  where concessionaria_id='c4000000-0000-4000-8000-000000000002'
    and estado='pendente')<>1
 or has_table_privilege('prumo_s0_gateway','public.planos_recontato_sinteticos','UPDATE')
 or has_table_privilege('prumo_s0_signed_executor','public.planos_recontato_sinteticos','UPDATE')
 then raise exception 'FAIL OWNER37D-04: real privileges or tenant B changed';end if;
 if (select pg_catalog.count(*) from pg_catalog.pg_roles where rolname='prumo_s0_probe_037d')<>1
 then raise exception 'FAIL OWNER37D-04: expected transaction-only probe';end if;
end $gate$;
\echo 'PASS OWNER37D-04: real gateway/executor stay locked; test role/grants will rollback'
rollback;
