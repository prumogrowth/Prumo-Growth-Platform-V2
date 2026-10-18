\set ON_ERROR_STOP on
-- S0-037F: isolated signed-executor model, NEVER an operational migration.
-- No real credentials, no changes to commercial owners or hosted Supabase.
-- All roles, schema, permissions, fixtures, proof and audit rows ROLLBACK.
begin;
create role prumo_s0_probe_037f_exec nologin noinherit
 nosuperuser nocreatedb nocreaterole noreplication nobypassrls;
create schema prumo_037f_lab;
revoke all on schema prumo_037f_lab from public,anon,authenticated,service_role;
grant usage on schema prumo_037f_lab to
 prumo_s0_probe_037f_exec,prumo_s0_gateway;
grant usage on schema prumo_private to prumo_s0_probe_037f_exec;
grant execute on function prumo_private.gateway_validar_prova_s0(
 text,uuid,uuid,uuid,uuid,bigint,text,text,uuid,uuid,bigint,uuid,text)
 to prumo_s0_probe_037f_exec;

create table prumo_037f_lab.sessoes_mock(
 id uuid primary key,ator uuid not null,ativa boolean not null default true);
create table prumo_037f_lab.vinculos_mock(
 ator uuid not null,loja uuid not null,ativo boolean not null default true,
 primary key(ator,loja));
create table prumo_037f_lab.trabalho_mock(
 id uuid primary key,loja uuid not null,acao text not null
  check(acao in ('cancelar_plano','conciliar_c07')),
 versao bigint not null default 1,estado text not null default 'READY'
  check(estado in ('READY','APPLIED')));
create table prumo_037f_lab.capacidade_mock(
 nonce uuid primary key,acao text not null,loja uuid not null,
 alvo uuid not null,versao bigint not null,txid bigint not null);
create table prumo_037f_lab.auditoria_mock(
 nonce uuid primary key,acao text not null,ator uuid not null,
 loja uuid not null,alvo uuid not null,versao_de bigint not null,
 criado_em timestamptz not null default clock_timestamp());
revoke all on all tables in schema prumo_037f_lab
 from public,anon,authenticated,service_role,prumo_s0_gateway;
grant select on prumo_037f_lab.sessoes_mock,prumo_037f_lab.vinculos_mock,
 prumo_037f_lab.trabalho_mock,prumo_037f_lab.capacidade_mock
 to prumo_s0_probe_037f_exec;
grant insert,delete on prumo_037f_lab.capacidade_mock
 to prumo_s0_probe_037f_exec;
grant update(versao,estado) on prumo_037f_lab.trabalho_mock
 to prumo_s0_probe_037f_exec;
grant insert on prumo_037f_lab.auditoria_mock to prumo_s0_probe_037f_exec;

-- RLS is bound to protected capability rows minted *inside* the definer.
-- This still does not represent a tested Supabase Auth policy.
alter table prumo_037f_lab.trabalho_mock enable row level security;
create policy probe037f_read on prumo_037f_lab.trabalho_mock
 for select to prumo_s0_probe_037f_exec using(
 exists(select 1 from prumo_037f_lab.capacidade_mock c
  where c.alvo=trabalho_mock.id and c.loja=trabalho_mock.loja
   and c.acao=trabalho_mock.acao and c.txid=txid_current()
   and trabalho_mock.versao in(c.versao,c.versao+1))
);
create policy probe037f_write on prumo_037f_lab.trabalho_mock
 for update to prumo_s0_probe_037f_exec using(
 trabalho_mock.estado='READY' and exists(
 select 1 from prumo_037f_lab.capacidade_mock c
 where c.alvo=trabalho_mock.id and c.loja=trabalho_mock.loja
  and c.acao=trabalho_mock.acao and c.versao=trabalho_mock.versao
  and c.txid=txid_current()))
 with check(
 trabalho_mock.estado='APPLIED' and exists(
 select 1 from prumo_037f_lab.capacidade_mock c
 where c.alvo=trabalho_mock.id and c.loja=trabalho_mock.loja
  and c.acao=trabalho_mock.acao and c.versao+1=trabalho_mock.versao
  and c.txid=txid_current())
);

-- The only gateway-callable lab operation. It runs as a dedicated NOLOGIN
-- definer rather than postgres; its direct table grants are narrow and scoped
-- through the issuer/checks. No client-supplied GUC is treated as identity.
create function prumo_037f_lab.executar_assinado(
 p_acao text,p_ator uuid,p_sessao uuid,p_loja uuid,p_alvo uuid,
 p_versao bigint,p_decisao text,
 p_chave uuid,p_emitido bigint,p_nonce uuid,p_assinatura text)
 returns jsonb language plpgsql security definer set search_path='' as $fn$
declare n int;
begin
 if p_acao not in ('cancelar_plano','conciliar_c07')
 or p_versao is null or p_versao<1
 or (p_acao='cancelar_plano' and p_decisao is not null)
 or (p_acao='conciliar_c07' and p_decisao<>'ENCERRAR_SEM_PROVA')
 then raise exception 'INVALID_OPERATION' using errcode='22023';end if;
 perform prumo_private.gateway_validar_prova_s0(
  p_acao,p_ator,p_sessao,p_loja,p_alvo,p_versao,p_decisao,
  null,null,p_chave,p_emitido,p_nonce,p_assinatura);
 if not exists(select 1 from prumo_037f_lab.sessoes_mock s
  where s.id=p_sessao and s.ator=p_ator and s.ativa)
 then raise exception 'SESSAO_INATIVA' using errcode='42501';end if;
 if not exists(select 1 from prumo_037f_lab.vinculos_mock v
  where v.ator=p_ator and v.loja=p_loja and v.ativo)
 then raise exception 'FORBIDDEN_SCOPE' using errcode='42501';end if;
 insert into prumo_037f_lab.capacidade_mock(
  nonce,acao,loja,alvo,versao,txid)
 values(p_nonce,p_acao,p_loja,p_alvo,p_versao,txid_current());
 update prumo_037f_lab.trabalho_mock w
 set estado='APPLIED',versao=w.versao+1
 where w.id=p_alvo and w.loja=p_loja and w.acao=p_acao
  and w.versao=p_versao and w.estado='READY';
 get diagnostics n=row_count;
 if n<>1 then raise exception 'CONFLICT_VERSION_OR_SCOPE'
  using errcode='40001';end if;
 insert into prumo_037f_lab.auditoria_mock(
  nonce,acao,ator,loja,alvo,versao_de)
 values(p_nonce,p_acao,p_ator,p_loja,p_alvo,p_versao);
 delete from prumo_037f_lab.capacidade_mock where nonce=p_nonce;
 return jsonb_build_object('outcome','APPLIED','nova_versao',p_versao+1);
end $fn$;
revoke all on function prumo_037f_lab.executar_assinado(
 text,uuid,uuid,uuid,uuid,bigint,text,uuid,bigint,uuid,text)
 from public,anon,authenticated,service_role,prumo_s0_gateway;
grant create on schema prumo_037f_lab to prumo_s0_probe_037f_exec;
alter function prumo_037f_lab.executar_assinado(
 text,uuid,uuid,uuid,uuid,bigint,text,uuid,bigint,uuid,text)
 owner to prumo_s0_probe_037f_exec;
revoke create on schema prumo_037f_lab from prumo_s0_probe_037f_exec;
grant execute on function prumo_037f_lab.executar_assinado(
 text,uuid,uuid,uuid,uuid,bigint,text,uuid,bigint,uuid,text)
 to prumo_s0_gateway;

-- Dedicated, transaction-only fixture. Never a real secret.
insert into prumo_private.gateway_chaves_assinatura_s0(
 chave_id,segredo,valido_desde,valido_ate,ativo)
 values('c4190000-0000-4000-8000-000000000001',
  decode(repeat('f7',32),'hex'),
  statement_timestamp()-interval '1 hour',
  statement_timestamp()+interval '1 hour',false);
select prumo_private.alterar_estado_chave_gateway_s0(
 'c4190000-0000-4000-8000-000000000001',1,true,
 'Somente fixture descartavel de assinatura 037F');

insert into prumo_037f_lab.sessoes_mock(id,ator) values
 ('c4110000-0000-4000-8000-000000000001','c4100000-0000-4000-8000-000000000001'),
 ('c4110000-0000-4000-8000-000000000002','c4100000-0000-4000-8000-000000000002');
insert into prumo_037f_lab.vinculos_mock(ator,loja) values
 ('c4100000-0000-4000-8000-000000000001','c4120000-0000-4000-8000-000000000001'),
 ('c4100000-0000-4000-8000-000000000002','c4120000-0000-4000-8000-000000000002');
insert into prumo_037f_lab.trabalho_mock(id,loja,acao) values
 ('c4130000-0000-4000-8000-000000000001','c4120000-0000-4000-8000-000000000001','cancelar_plano'),
 ('c4130000-0000-4000-8000-000000000002','c4120000-0000-4000-8000-000000000002','cancelar_plano'),
 ('c4130000-0000-4000-8000-000000000003','c4120000-0000-4000-8000-000000000001','conciliar_c07'),
 ('c4130000-0000-4000-8000-000000000004','c4120000-0000-4000-8000-000000000001','cancelar_plano'),
 ('c4130000-0000-4000-8000-000000000005','c4120000-0000-4000-8000-000000000001','cancelar_plano');

-- Signing only in privileged test setup, using the same canonical HMAC
-- schema used by the existing gateway verifier.
create function pg_temp.assinar_037f(
 p_acao text,p_ator uuid,p_sessao uuid,p_loja uuid,p_alvo uuid,
 p_versao bigint,p_decisao text,p_emitido bigint,p_nonce uuid
) returns text language plpgsql security invoker set search_path='' as $sig$
declare v_schema text;v_material text;v_bytes bytea;
begin
 select n.nspname into v_schema from pg_catalog.pg_extension e
 join pg_catalog.pg_namespace n on n.oid=e.extnamespace where e.extname='pgcrypto';
 v_material:=prumo_private.gateway_material_assinatura_s0(
  p_acao,p_ator,p_sessao,p_loja,p_alvo,p_versao,
  p_decisao,null,null,p_emitido,p_nonce);
 execute pg_catalog.format('select %I.hmac($1,$2,''sha256'')',v_schema)
 into v_bytes using convert_to(v_material,'UTF8'),decode(repeat('f7',32),'hex');
 return pg_catalog.encode(v_bytes,'hex');
end $sig$;
select set_config('prumo.test037f.issue',
 (extract(epoch from clock_timestamp())::bigint)::text,true);
select set_config('prumo.test037f.good',pg_temp.assinar_037f(
 'cancelar_plano','c4100000-0000-4000-8000-000000000001',
 'c4110000-0000-4000-8000-000000000001',
 'c4120000-0000-4000-8000-000000000001',
 'c4130000-0000-4000-8000-000000000001',1,null,
 current_setting('prumo.test037f.issue')::bigint,
 'c4140000-0000-4000-8000-000000000001'),true);
select set_config('prumo.test037f.c07',pg_temp.assinar_037f(
 'conciliar_c07','c4100000-0000-4000-8000-000000000001',
 'c4110000-0000-4000-8000-000000000001',
 'c4120000-0000-4000-8000-000000000001',
 'c4130000-0000-4000-8000-000000000003',1,'ENCERRAR_SEM_PROVA',
 current_setting('prumo.test037f.issue')::bigint,
 'c4140000-0000-4000-8000-000000000002'),true);
select set_config('prumo.test037f.cross',pg_temp.assinar_037f(
 'cancelar_plano','c4100000-0000-4000-8000-000000000001',
 'c4110000-0000-4000-8000-000000000001',
 'c4120000-0000-4000-8000-000000000002',
 'c4130000-0000-4000-8000-000000000002',1,null,
 current_setting('prumo.test037f.issue')::bigint,
 'c4140000-0000-4000-8000-000000000003'),true);
select set_config('prumo.test037f.fail',pg_temp.assinar_037f(
 'cancelar_plano','c4100000-0000-4000-8000-000000000001',
 'c4110000-0000-4000-8000-000000000001',
 'c4120000-0000-4000-8000-000000000001',
 'c4130000-0000-4000-8000-000000000004',1,null,
 current_setting('prumo.test037f.issue')::bigint,
 'c4140000-0000-4000-8000-000000000004'),true);
select set_config('prumo.test037f.revoke',pg_temp.assinar_037f(
 'cancelar_plano','c4100000-0000-4000-8000-000000000001',
 'c4110000-0000-4000-8000-000000000001',
 'c4120000-0000-4000-8000-000000000001',
 'c4130000-0000-4000-8000-000000000005',1,null,
 current_setting('prumo.test037f.issue')::bigint,
 'c4140000-0000-4000-8000-000000000005'),true);

do $acl$
begin
 if has_table_privilege('prumo_s0_gateway','prumo_037f_lab.trabalho_mock','UPDATE')
 or has_table_privilege('prumo_s0_gateway','prumo_037f_lab.auditoria_mock','INSERT')
 or has_table_privilege('prumo_s0_probe_037f_exec',
   'prumo_private.gateway_chaves_assinatura_s0','SELECT')
 or (case when to_regclass('auth.sessions') is not null
 then has_table_privilege('prumo_s0_probe_037f_exec',
      to_regclass('auth.sessions'),'SELECT') else false end)
 or not (select p.prosecdef and
   pg_catalog.pg_get_userbyid(p.proowner)='prumo_s0_probe_037f_exec'
   from pg_catalog.pg_proc p where p.oid=
   'prumo_037f_lab.executar_assinado(text,uuid,uuid,uuid,uuid,bigint,text,uuid,bigint,uuid,text)'::regprocedure)
 then raise exception 'FAIL ISSUERF-01: unsafe owner or direct grants';end if;
end $acl$;
\echo 'PASS ISSUERF-01: lab executor NOLOGIN owned, no direct gateway DML or secret access'

set local role prumo_s0_gateway;
do $apply$
declare v jsonb;
begin
 begin
  perform 1 from prumo_037f_lab.sessoes_mock;
  raise exception 'FAIL ISSUERF-02: gateway reads mock sessions';
 exception when insufficient_privilege then null;end;
 begin
  perform prumo_037f_lab.executar_assinado(
   'cancelar_plano','c4100000-0000-4000-8000-000000000001',
   'c4110000-0000-4000-8000-000000000001',
   'c4120000-0000-4000-8000-000000000001',
   'c4130000-0000-4000-8000-000000000001',1,null,
   'c4190000-0000-4000-8000-000000000001',
   current_setting('prumo.test037f.issue')::bigint,
   'c4140000-0000-4000-8000-000000000009',repeat('0',64));
  raise exception 'FAIL ISSUERF-02: forged HMAC accepted';
 exception when insufficient_privilege then
  if SQLERRM<>'PROVA_INVALIDA' then raise;end if;end;
 v:=prumo_037f_lab.executar_assinado(
  'cancelar_plano','c4100000-0000-4000-8000-000000000001',
  'c4110000-0000-4000-8000-000000000001',
  'c4120000-0000-4000-8000-000000000001',
  'c4130000-0000-4000-8000-000000000001',1,null,
  'c4190000-0000-4000-8000-000000000001',
  current_setting('prumo.test037f.issue')::bigint,
  'c4140000-0000-4000-8000-000000000001',
  current_setting('prumo.test037f.good'));
 if v->>'outcome'<>'APPLIED' then raise exception 'FAIL ISSUERF-02: C08 mock';end if;
 v:=prumo_037f_lab.executar_assinado(
  'conciliar_c07','c4100000-0000-4000-8000-000000000001',
  'c4110000-0000-4000-8000-000000000001',
  'c4120000-0000-4000-8000-000000000001',
  'c4130000-0000-4000-8000-000000000003',1,'ENCERRAR_SEM_PROVA',
  'c4190000-0000-4000-8000-000000000001',
  current_setting('prumo.test037f.issue')::bigint,
  'c4140000-0000-4000-8000-000000000002',
  current_setting('prumo.test037f.c07'));
 if v->>'outcome'<>'APPLIED' then raise exception 'FAIL ISSUERF-02: C07 mock';end if;
 begin
  perform prumo_037f_lab.executar_assinado(
   'cancelar_plano','c4100000-0000-4000-8000-000000000001',
   'c4110000-0000-4000-8000-000000000001',
   'c4120000-0000-4000-8000-000000000002',
   'c4130000-0000-4000-8000-000000000002',1,null,
   'c4190000-0000-4000-8000-000000000001',
   current_setting('prumo.test037f.issue')::bigint,
   'c4140000-0000-4000-8000-000000000003',
   current_setting('prumo.test037f.cross'));
  raise exception 'FAIL ISSUERF-02: cross tenant accepted';
 exception when insufficient_privilege then
  if SQLERRM<>'FORBIDDEN_SCOPE' then raise;end if;end;
end $apply$;
reset role;
do $check$
begin
 if (select count(*) from prumo_037f_lab.auditoria_mock)<>2
 or (select count(*) from prumo_037f_lab.trabalho_mock
  where estado='APPLIED')<>2
 or (select count(*) from prumo_037f_lab.capacidade_mock)<>0
 or (select count(*) from prumo_private.gateway_provas_usadas_s0
  where chave_id='c4190000-0000-4000-8000-000000000001')<>2
 then raise exception 'FAIL ISSUERF-02: unexpected domain, capability or nonce';end if;
end $check$;
\echo 'PASS ISSUERF-02: signed mock C08/C07, cross-store and HMAC negatives atomic'

-- Force audit to fail after work UPDATE. Same nonce must be valid on retry.
create function prumo_037f_lab.falhar_audit_mock()
returns trigger language plpgsql security invoker set search_path='' as $fault$
begin
 raise exception 'FAULT_AUDIT_037F' using errcode='P0001';
end $fault$;
create trigger audit_fault_037f before insert on prumo_037f_lab.auditoria_mock
 for each row execute function prumo_037f_lab.falhar_audit_mock();
set local role prumo_s0_gateway;
do $fault$
begin
 begin
  perform prumo_037f_lab.executar_assinado(
   'cancelar_plano','c4100000-0000-4000-8000-000000000001',
   'c4110000-0000-4000-8000-000000000001',
   'c4120000-0000-4000-8000-000000000001',
   'c4130000-0000-4000-8000-000000000004',1,null,
   'c4190000-0000-4000-8000-000000000001',
   current_setting('prumo.test037f.issue')::bigint,
   'c4140000-0000-4000-8000-000000000004',
   current_setting('prumo.test037f.fail'));
  raise exception 'FAIL ISSUERF-03: audit failure accepted';
 exception when raise_exception then
  if SQLERRM<>'FAULT_AUDIT_037F' then raise;end if;end;
end $fault$;
reset role;
do $check$
begin
 if exists(select 1 from prumo_037f_lab.trabalho_mock
    where id='c4130000-0000-4000-8000-000000000004' and estado<>'READY')
 or exists(select 1 from prumo_private.gateway_provas_usadas_s0
    where nonce='c4140000-0000-4000-8000-000000000004')
 or exists(select 1 from prumo_037f_lab.capacidade_mock)
 then raise exception 'FAIL ISSUERF-03: audit failure left domain/nonce/cap';end if;
end $check$;
drop trigger audit_fault_037f on prumo_037f_lab.auditoria_mock;
set local role prumo_s0_gateway;
do $retry$
declare v jsonb;
begin
 v:=prumo_037f_lab.executar_assinado(
  'cancelar_plano','c4100000-0000-4000-8000-000000000001',
  'c4110000-0000-4000-8000-000000000001',
  'c4120000-0000-4000-8000-000000000001',
  'c4130000-0000-4000-8000-000000000004',1,null,
  'c4190000-0000-4000-8000-000000000001',
  current_setting('prumo.test037f.issue')::bigint,
  'c4140000-0000-4000-8000-000000000004',
  current_setting('prumo.test037f.fail'));
 if v->>'outcome'<>'APPLIED' then raise exception 'FAIL ISSUERF-03: retry failed';end if;
end $retry$;
reset role;
\echo 'PASS ISSUERF-03: audit failure rollback includes HMAC nonce and retry succeeds'

update prumo_037f_lab.sessoes_mock set ativa=false
 where id='c4110000-0000-4000-8000-000000000001';
set local role prumo_s0_gateway;
do $revoked$
begin
 begin
  perform prumo_037f_lab.executar_assinado(
   'cancelar_plano','c4100000-0000-4000-8000-000000000001',
   'c4110000-0000-4000-8000-000000000001',
   'c4120000-0000-4000-8000-000000000001',
   'c4130000-0000-4000-8000-000000000005',1,null,
   'c4190000-0000-4000-8000-000000000001',
   current_setting('prumo.test037f.issue')::bigint,
   'c4140000-0000-4000-8000-000000000005',
   current_setting('prumo.test037f.revoke'));
  raise exception 'FAIL ISSUERF-04: inactive mock session allowed';
 exception when insufficient_privilege then
  if SQLERRM<>'SESSAO_INATIVA' then raise;end if;end;
end $revoked$;
reset role;
do $end$
begin
 if (select count(*) from prumo_037f_lab.auditoria_mock)<>3
 or (select count(*) from prumo_037f_lab.trabalho_mock where estado='APPLIED')<>3
 or (select count(*) from prumo_private.gateway_provas_usadas_s0
  where chave_id='c4190000-0000-4000-8000-000000000001')<>3
 or exists(select 1 from prumo_037f_lab.trabalho_mock
   where loja='c4120000-0000-4000-8000-000000000002'
     and estado<>'READY')
 or exists(select 1 from prumo_037f_lab.capacidade_mock)
 then raise exception 'FAIL ISSUERF-04: final lab invariants';end if;
end $end$;
\echo 'PASS ISSUERF-04: mock session revocation, cross-tenant isolation and audit intact'
rollback;
