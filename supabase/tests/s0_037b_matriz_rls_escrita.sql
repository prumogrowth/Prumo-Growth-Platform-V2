\set ON_ERROR_STOP on
-- S0-037B: privilege capability matrix, RLS and scoped DML NEGATIVE/EXPLORATORY tests.
-- ALL role grants/policies/fixtures revert on ROLLBACK in disposable PG17.
-- Deliberately NOT a signed worker or authorization mechanism for production.
begin;
create role prumo_s0_probe_037b nologin noinherit
 nosuperuser nocreatedb nocreaterole noreplication nobypassrls;
grant usage on schema public to prumo_s0_probe_037b;

-- Deliberately separate stores, including the same client telephone.
insert into public.concessionarias(id,nome_operacional) values
 ('c3800000-0000-4000-8000-000000000001','OWNER37B A ficticia'),
 ('c3800000-0000-4000-8000-000000000002','OWNER37B B ficticia');
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado) values
 ('c3810000-0000-4000-8000-000000000001','c3800000-0000-4000-8000-000000000001','+5581900038383'),
 ('c3810000-0000-4000-8000-000000000002','c3800000-0000-4000-8000-000000000002','+5581900038383');
insert into public.ciclos_comerciais(id,concessionaria_id,lead_id) values
 ('c3820000-0000-4000-8000-000000000001','c3800000-0000-4000-8000-000000000001','c3810000-0000-4000-8000-000000000001'),
 ('c3820000-0000-4000-8000-000000000002','c3800000-0000-4000-8000-000000000002','c3810000-0000-4000-8000-000000000002');
insert into public.canais_loja(id,concessionaria_id,identificador_emissor) values
 ('c3830000-0000-4000-8000-000000000001','c3800000-0000-4000-8000-000000000001','OWNER37B_EMISSOR_A'),
 ('c3830000-0000-4000-8000-000000000002','c3800000-0000-4000-8000-000000000002','OWNER37B_EMISSOR_B');
insert into public.planos_recontato_sinteticos(
 id,concessionaria_id,lead_id,ciclo_id,canal_id,chave_idempotencia,fingerprint)
 values
 ('c3840000-0000-4000-8000-000000000001','c3800000-0000-4000-8000-000000000001',
  'c3810000-0000-4000-8000-000000000001','c3820000-0000-4000-8000-000000000001',
  'c3830000-0000-4000-8000-000000000001','OWNER37B_PLAN_A',repeat('a',64)),
 ('c3840000-0000-4000-8000-000000000002','c3800000-0000-4000-8000-000000000002',
  'c3810000-0000-4000-8000-000000000002','c3820000-0000-4000-8000-000000000002',
  'c3830000-0000-4000-8000-000000000002','OWNER37B_PLAN_B',repeat('b',64));
insert into public.catalogo_templates_sinteticos(id,concessionaria_id,codigo,versao) values
 ('c3850000-0000-4000-8000-000000000001','c3800000-0000-4000-8000-000000000001','OWNER37B',1),
 ('c3850000-0000-4000-8000-000000000002','c3800000-0000-4000-8000-000000000002','OWNER37B',1);
insert into public.envios_template_sinteticos(
 id,concessionaria_id,plano_id,template_id,ordem,agendado_em,chave_idempotencia)
 values
 ('c3860000-0000-4000-8000-000000000001','c3800000-0000-4000-8000-000000000001',
 'c3840000-0000-4000-8000-000000000001','c3850000-0000-4000-8000-000000000001',1,
 statement_timestamp()+interval '1 day','OWNER37B_ENV_A'),
 ('c3860000-0000-4000-8000-000000000002','c3800000-0000-4000-8000-000000000002',
 'c3840000-0000-4000-8000-000000000002','c3850000-0000-4000-8000-000000000002',1,
 statement_timestamp()+interval '1 day','OWNER37B_ENV_B');
insert into auth.users(id) values
 ('c3870000-0000-4000-8000-000000000001'),
 ('c3870000-0000-4000-8000-000000000002');
insert into public.atores(id) values
 ('c3870000-0000-4000-8000-000000000001'),
 ('c3870000-0000-4000-8000-000000000002');
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel) values
 ('c3870000-0000-4000-8000-000000000001','c3800000-0000-4000-8000-000000000001','gestor'),
 ('c3870000-0000-4000-8000-000000000002','c3800000-0000-4000-8000-000000000002','gestor');
-- Unknown callbacks are triaged into distinct shop-scoped C07 pendencies.
select prumo_private.registrar_callback_c07_sintetico(
 'c3830000-0000-4000-8000-000000000001','OWNER37B_UNKNOWN_A',
 'OWNER37B_CALLBACK_A','INCERTO_SIMULADO',statement_timestamp());
select prumo_private.registrar_callback_c07_sintetico(
 'c3830000-0000-4000-8000-000000000002','OWNER37B_UNKNOWN_B',
 'OWNER37B_CALLBACK_B','INCERTO_SIMULADO',statement_timestamp());

-- The private gateway audit and auth.sessions lack a safe dedicated
-- per-tenant commercial policy today. Grant neither to the probe.
do $m$
begin
 if has_table_privilege('prumo_s0_probe_037b','prumo_private.auditoria_gateway_s0','INSERT')
 or (to_regclass('auth.sessions') is not null and
     has_table_privilege('prumo_s0_probe_037b','auth.sessions','SELECT'))
 then raise exception 'FAIL OWNER37B-01: private audit/session exposed';end if;
 if (select count(*) from public.pendencias_reconciliacao_c07_sinteticas
  where concessionaria_id in ('c3800000-0000-4000-8000-000000000001',
  'c3800000-0000-4000-8000-000000000002'))<>2
 then raise exception 'FAIL OWNER37B-01: callback fixtures missing';end if;
end $m$;
\echo 'PASS OWNER37B-01: two shops and separate C07 pendencies; session/audit gates closed'

-- Trial RLS policies bind to the literal synthetic store A only.
-- NO arbitrary SQL GUC such as a spoofable "current tenant" is trusted.
grant select on public.leads_loja,public.planos_recontato_sinteticos,
 public.envios_template_sinteticos,public.pendencias_reconciliacao_c07_sinteticas
 to prumo_s0_probe_037b;
grant update(estado,versao,motivo_cancelamento,cancelado_em)
 on public.planos_recontato_sinteticos to prumo_s0_probe_037b;
grant update(estado,cancelado_em) on public.envios_template_sinteticos
 to prumo_s0_probe_037b;
grant update(estado,versao,decisao,justificativa,revisado_por,encerrado_em)
 on public.pendencias_reconciliacao_c07_sinteticas to prumo_s0_probe_037b;
grant insert(concessionaria_id,envio_id,estado_anterior,estado_posterior,motivo)
 on public.eventos_envio_template_sinteticos to prumo_s0_probe_037b;
grant insert(concessionaria_id,pendencia_id,ator_id,versao_anterior,
 decisao,justificativa,envio_associado_id)
 on public.auditoria_reconciliacao_c07_sintetica to prumo_s0_probe_037b;
grant select on public.eventos_envio_template_sinteticos,
 public.auditoria_reconciliacao_c07_sintetica to prumo_s0_probe_037b;

create policy owner37b_leads_read on public.leads_loja
 for select to prumo_s0_probe_037b
 using(concessionaria_id='c3800000-0000-4000-8000-000000000001');
create policy owner37b_plans_read on public.planos_recontato_sinteticos
 for select to prumo_s0_probe_037b
 using(concessionaria_id='c3800000-0000-4000-8000-000000000001');
create policy owner37b_plans_write on public.planos_recontato_sinteticos
 for update to prumo_s0_probe_037b
 using(concessionaria_id='c3800000-0000-4000-8000-000000000001')
 with check(concessionaria_id='c3800000-0000-4000-8000-000000000001');
create policy owner37b_sends_read on public.envios_template_sinteticos
 for select to prumo_s0_probe_037b
 using(concessionaria_id='c3800000-0000-4000-8000-000000000001');
create policy owner37b_sends_write on public.envios_template_sinteticos
 for update to prumo_s0_probe_037b
 using(concessionaria_id='c3800000-0000-4000-8000-000000000001')
 with check(concessionaria_id='c3800000-0000-4000-8000-000000000001');
create policy owner37b_send_audit_read on public.eventos_envio_template_sinteticos
 for select to prumo_s0_probe_037b
 using(concessionaria_id='c3800000-0000-4000-8000-000000000001');
create policy owner37b_send_audit_insert on public.eventos_envio_template_sinteticos
 for insert to prumo_s0_probe_037b
 with check(concessionaria_id='c3800000-0000-4000-8000-000000000001');
create policy owner37b_pending_read on public.pendencias_reconciliacao_c07_sinteticas
 for select to prumo_s0_probe_037b
 using(concessionaria_id='c3800000-0000-4000-8000-000000000001');
create policy owner37b_pending_write on public.pendencias_reconciliacao_c07_sinteticas
 for update to prumo_s0_probe_037b
 using(concessionaria_id='c3800000-0000-4000-8000-000000000001')
 with check(concessionaria_id='c3800000-0000-4000-8000-000000000001');
create policy owner37b_c07audit_read on public.auditoria_reconciliacao_c07_sintetica
 for select to prumo_s0_probe_037b
 using(concessionaria_id='c3800000-0000-4000-8000-000000000001');
create policy owner37b_c07audit_write on public.auditoria_reconciliacao_c07_sintetica
 for insert to prumo_s0_probe_037b
 with check(concessionaria_id='c3800000-0000-4000-8000-000000000001');

set local role prumo_s0_probe_037b;
do $probe$
declare v_rows integer;
begin
 if (select count(*) from public.leads_loja where id in
 ('c3810000-0000-4000-8000-000000000001',
 'c3810000-0000-4000-8000-000000000002'))<>1
 or (select count(*) from public.planos_recontato_sinteticos
  where id in ('c3840000-0000-4000-8000-000000000001',
   'c3840000-0000-4000-8000-000000000002'))<>1
 or (select count(*) from public.pendencias_reconciliacao_c07_sinteticas
  where concessionaria_id in ('c3800000-0000-4000-8000-000000000001',
                              'c3800000-0000-4000-8000-000000000002'))<>1
 then raise exception 'FAIL OWNER37B-02: RLS read tenant isolation';end if;
 -- Test that a *direct* DML command can update only the allowed shop,
 -- which is also why these grants MUST NOT be promoted to signed gateway.
 update public.planos_recontato_sinteticos
 set estado='cancelado',motivo_cancelamento='cancelamento_gestor',
     cancelado_em=statement_timestamp(),versao=versao+1
 where id='c3840000-0000-4000-8000-000000000002';
 get diagnostics v_rows=row_count;
 if v_rows<>0 then raise exception 'FAIL OWNER37B-02: cross-shop plan update';end if;
 update public.planos_recontato_sinteticos
 set estado='cancelado',motivo_cancelamento='cancelamento_gestor',
     cancelado_em=statement_timestamp(),versao=versao+1
 where id='c3840000-0000-4000-8000-000000000001' and versao=1;
 get diagnostics v_rows=row_count;
 if v_rows<>1 then raise exception 'FAIL OWNER37B-02: own plan CAS update';end if;
 update public.envios_template_sinteticos
 set estado='cancelado',cancelado_em=statement_timestamp()
 where id='c3860000-0000-4000-8000-000000000001' and estado='programado';
 get diagnostics v_rows=row_count;
 if v_rows<>1 then raise exception 'FAIL OWNER37B-02: own outbound cancel';end if;
 insert into public.eventos_envio_template_sinteticos(
  concessionaria_id,envio_id,estado_anterior,estado_posterior,motivo)
 values('c3800000-0000-4000-8000-000000000001',
 'c3860000-0000-4000-8000-000000000001',
 'programado','cancelado','cancelamento_gestor');
 if (select count(*) from public.eventos_envio_template_sinteticos
  where envio_id='c3860000-0000-4000-8000-000000000001')<>1
 then raise exception 'FAIL OWNER37B-02: append audit not visible';end if;
end $probe$;
reset role;
\echo 'PASS OWNER37B-02: tenant-bound RLS reads, C08 plan/send CAS and audit DML (simulation only)'

set local role prumo_s0_probe_037b;
do $probe$
declare v_rows integer;
begin
 update public.pendencias_reconciliacao_c07_sinteticas
 set estado='encerrada',versao=versao+1,decisao='ENCERRAR_SEM_PROVA',
  justificativa='Decisao meramente sintetica e auditavel',
  revisado_por='c3870000-0000-4000-8000-000000000001',
  encerrado_em=statement_timestamp()
 where concessionaria_id='c3800000-0000-4000-8000-000000000002'
 and versao=1;
 get diagnostics v_rows=row_count;
 if v_rows<>0 then raise exception 'FAIL OWNER37B-03: B C07 modified';end if;
 update public.pendencias_reconciliacao_c07_sinteticas
 set estado='encerrada',versao=versao+1,decisao='ENCERRAR_SEM_PROVA',
  justificativa='Decisao meramente sintetica e auditavel',
  revisado_por='c3870000-0000-4000-8000-000000000001',
  encerrado_em=statement_timestamp()
 where concessionaria_id='c3800000-0000-4000-8000-000000000001'
 and versao=1 and estado='pendente';
 get diagnostics v_rows=row_count;
 if v_rows<>1 then raise exception 'FAIL OWNER37B-03: A C07 CAS';end if;
 insert into public.auditoria_reconciliacao_c07_sintetica(
  concessionaria_id,pendencia_id,ator_id,versao_anterior,
  decisao,justificativa)
 select concessionaria_id,id,
 'c3870000-0000-4000-8000-000000000001',1,
 'ENCERRAR_SEM_PROVA','Decisao meramente sintetica e auditavel'
 from public.pendencias_reconciliacao_c07_sinteticas
 where concessionaria_id='c3800000-0000-4000-8000-000000000001'
 and estado='encerrada';
 if (select count(*) from public.auditoria_reconciliacao_c07_sintetica
  where concessionaria_id='c3800000-0000-4000-8000-000000000001')<>1
 then raise exception 'FAIL OWNER37B-03: audit C07';end if;
end $probe$;
reset role;
\echo 'PASS OWNER37B-03: C07 tenant-bound optimistic update plus append-only audit (simulation only)'

-- Negative gates: the role can mutate shop A ONLY because of TEMPORARY
-- direct grants; this must never serve as the authenticated business API.
set local role prumo_s0_probe_037b;
do $probe$
begin
 begin
  perform 1 from prumo_private.auditoria_gateway_s0;
  raise exception 'FAIL OWNER37B-04: private audit readable';
 exception when insufficient_privilege then null;end;
 begin
  perform prumo_private.cancelar_plano_gestor_sintetico(null,null,null,null);
  raise exception 'FAIL OWNER37B-04: raw domain callable';
 exception when insufficient_privilege then null;end;
 if (select count(*) from public.planos_recontato_sinteticos
    where id='c3840000-0000-4000-8000-000000000002')<>0
 then raise exception 'FAIL OWNER37B-04: cross tenant plan surfaced';end if;
end $probe$;
reset role;
\echo 'PASS OWNER37B-04: no private audit read or raw domain EXECUTE; B remains hidden'

do $gate$
begin
 if has_table_privilege('prumo_s0_gateway','public.planos_recontato_sinteticos','UPDATE')
 or has_table_privilege('prumo_s0_gateway','public.pendencias_reconciliacao_c07_sinteticas','UPDATE')
 or has_table_privilege('prumo_s0_signed_executor','public.leads_loja','SELECT')
 or has_table_privilege('prumo_s0_signed_executor','prumo_private.auditoria_gateway_s0','INSERT')
 then raise exception 'FAIL OWNER37B-05: persisted gateway/executor rights were changed';end if;
 if not exists(select 1 from pg_catalog.pg_roles where
  rolname='prumo_s0_probe_037b' and not rolcanlogin and not rolbypassrls)
 then raise exception 'FAIL OWNER37B-05: probe role security';end if;
end $gate$;
\echo 'PASS OWNER37B-05: temporary grants do not touch actual signed roles'
rollback;
