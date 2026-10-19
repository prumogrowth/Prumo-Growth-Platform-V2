\set ON_ERROR_STOP on
-- S1P-01..10: aprovação nova do usuário, só política SEM ações reais.
begin;
insert into auth.users(id)
 select ('de020000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid
 from generate_series(1,9) i;
insert into public.atores(id) select id from auth.users where id::text like 'de020000-%';
insert into public.concessionarias(id,nome_operacional) values
 ('df020000-0000-4000-8000-000000000001','S1P loja A'),
 ('df020000-0000-4000-8000-000000000002','S1P loja B');
insert into public.equipe_prumo_s1(ator_id,estado)
 select id,case when id::text like '%000000000005' then 'suspenso'
 when id::text like '%000000000006' then 'pendente'
 else 'ativo' end
 from public.atores where id::text like 'de020000-%' and id::text not like '%000000000009';
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel)
 select ('de020000-0000-4000-8000-'||lpad(ator::text,12,'0'))::uuid,
 ('df020000-0000-4000-8000-'||lpad(loja::text,12,'0'))::uuid,papel
 from (values (1,1,'responsavel'),(2,1,'gestor'),(3,1,'operador'),
 (3,2,'operador'),(4,2,'gestor'),(5,1,'gestor'),(6,1,'operador'),
 (7,1,'operador'),(7,1,'gestor'),(8,2,'operador')) x(ator,loja,papel);
\echo 'PASS S1P-01: responsavel A, gestores A/B, operador A+B, misto gestor/operador'
do $t$ begin
 if not prumo_private.s1_pode_administrar_operador(
  'de020000-0000-4000-8000-000000000001',
  'df020000-0000-4000-8000-000000000001','adicionar_operador',
  'de020000-0000-4000-8000-000000000009')
 or not prumo_private.s1_pode_administrar_operador(
  'de020000-0000-4000-8000-000000000001',
  'df020000-0000-4000-8000-000000000001','adicionar_gestor',
  'de020000-0000-4000-8000-000000000009')
 then raise exception 'S1P-02 responsavel nao pode incluir';end if;
end $t$;
\echo 'PASS S1P-02: so responsavel pode adicionar operador e gestor'
do $t$ begin
 if not prumo_private.s1_pode_administrar_operador(
  'de020000-0000-4000-8000-000000000001',
  'df020000-0000-4000-8000-000000000001','desligar_definitivo_operador',
  'de020000-0000-4000-8000-000000000003')
 or not prumo_private.s1_pode_administrar_operador(
  'de020000-0000-4000-8000-000000000001',
  'df020000-0000-4000-8000-000000000001','desligar_definitivo_gestor',
  'de020000-0000-4000-8000-000000000002')
 then raise exception 'S1P-03 responsavel sem desligamento definitivo';end if;
end $t$;
\echo 'PASS S1P-03: desligar definitivamente exige responsável'
do $t$ begin
 if prumo_private.s1_pode_administrar_operador(
  'de020000-0000-4000-8000-000000000002',
  'df020000-0000-4000-8000-000000000001','adicionar_operador',
  'de020000-0000-4000-8000-000000000009')
 or prumo_private.s1_pode_administrar_operador(
  'de020000-0000-4000-8000-000000000002',
  'df020000-0000-4000-8000-000000000001','adicionar_gestor',
  'de020000-0000-4000-8000-000000000009')
 or prumo_private.s1_pode_administrar_operador(
  'de020000-0000-4000-8000-000000000002',
  'df020000-0000-4000-8000-000000000001','desligar_definitivo_operador',
  'de020000-0000-4000-8000-000000000003')
 then raise exception 'S1P-04 gestor adquiriu poder de responsavel';end if;
end $t$;
\echo 'PASS S1P-04: gestor nao inclui nem desliga definitivamente'
do $t$ begin
 if not (
  select bool_and(prumo_private.s1_pode_administrar_operador(
   'de020000-0000-4000-8000-000000000002',
   'df020000-0000-4000-8000-000000000001',acao,
   'de020000-0000-4000-8000-000000000003'))
  from (values('suspender_temporariamente'),('reativar_temporariamente'),
   ('mover_atendimento'),('redistribuir_carteira'),('ajustar_distribuicao')) v(acao)
 ) then raise exception 'S1P-05 gestor sem poder administrativo de operador';end if;
end $t$;
\echo 'PASS S1P-05: gestor gerencia, suspende, reativa, move e redistribui operador'
do $t$ begin
 if prumo_private.s1_pode_administrar_operador(
  'de020000-0000-4000-8000-000000000002',
  'df020000-0000-4000-8000-000000000002','redistribuir_carteira',
  'de020000-0000-4000-8000-000000000003')
 or prumo_private.s1_pode_administrar_operador(
  'de020000-0000-4000-8000-000000000001',
  'df020000-0000-4000-8000-000000000002','adicionar_operador',
  'de020000-0000-4000-8000-000000000009')
 or not prumo_private.s1_pode_administrar_operador(
  'de020000-0000-4000-8000-000000000004',
  'df020000-0000-4000-8000-000000000002','mover_atendimento',
  'de020000-0000-4000-8000-000000000003')
 then raise exception 'S1P-06 quebra isolamento de concessionaria';end if;
end $t$;
\echo 'PASS S1P-06: administração não transborda para outras lojas'
do $t$ begin
 if prumo_private.s1_pode_administrar_operador(
  'de020000-0000-4000-8000-000000000002',
  'df020000-0000-4000-8000-000000000001','suspender_temporariamente',
  'de020000-0000-4000-8000-000000000007')
 or prumo_private.s1_pode_administrar_operador(
  'de020000-0000-4000-8000-000000000002',
  'df020000-0000-4000-8000-000000000001','redistribuir_carteira',
  'de020000-0000-4000-8000-000000000001')
 then raise exception 'S1P-07 gestor afetou nivel igual/superior';end if;
end $t$;
\echo 'PASS S1P-07: gestor nao modifica outro gestor nem responsavel'
do $t$ begin
 if prumo_private.s1_pode_administrar_operador(
  'de020000-0000-4000-8000-000000000005',
  'df020000-0000-4000-8000-000000000001','mover_atendimento',
  'de020000-0000-4000-8000-000000000003')
 or prumo_private.s1_pode_administrar_operador(
  'de020000-0000-4000-8000-000000000003',
  'df020000-0000-4000-8000-000000000001','redistribuir_carteira',
  'de020000-0000-4000-8000-000000000006')
 or prumo_private.s1_pode_administrar_operador(
  'de020000-0000-4000-8000-000000000002',
  'df020000-0000-4000-8000-000000000001','reativar_temporariamente',
  'de020000-0000-4000-8000-000000000006')
 then raise exception 'S1P-08 pendente/inativo/operador obteve admin';end if;
end $t$;
\echo 'PASS S1P-08: gestor suspenso, operador e alvo pendente sem elevação'
do $t$ begin
 if prumo_private.s1_pode_administrar_operador(
  'de020000-0000-4000-8000-000000000002',
  'df020000-0000-4000-8000-000000000001','promover_gestor',
  'de020000-0000-4000-8000-000000000003')
 or prumo_private.s1_pode_administrar_operador(
  'de020000-0000-4000-8000-000000000002',
  'df020000-0000-4000-8000-000000000001','suspender_temporariamente',
  'de020000-0000-4000-8000-000000000002')
 then raise exception 'S1P-09 operacao nao homologada ou autoaprovação';end if;
end $t$;
\echo 'PASS S1P-09: ações desconhecidas e auto-administração rejeitadas'
set local role authenticated;
select pg_catalog.set_config('request.jwt.claim.sub',
 'de020000-0000-4000-8000-000000000002',true);
do $t$ begin
 begin
  perform prumo_private.s1_pode_administrar_operador(
   'de020000-0000-4000-8000-000000000001',
   'df020000-0000-4000-8000-000000000001','adicionar_operador',
   'de020000-0000-4000-8000-000000000009');
  raise exception 'S1P-10 predicado com p_solicitante forjado ficou público';
 exception when insufficient_privilege then null;end;
end $t$;
\echo 'PASS S1P-10: função com identidade parametrizada não exposta a authenticated'
reset role;
rollback;
