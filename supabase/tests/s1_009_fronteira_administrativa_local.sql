\set ON_ERROR_STOP on
-- S1A-01..09: autorizacao administrativa NEGADA em ambiente PG17 fake auth.
-- Nenhuma sessao GoTrue, JWT valido, REST ou Supabase hospedado envolvido.
begin;
insert into auth.users(id) values
 ('b9020000-0000-4000-8000-000000000001'),
 ('b9020000-0000-4000-8000-000000000002'),
 ('b9020000-0000-4000-8000-000000000003');
insert into public.atores(id) select id from auth.users where id::text like 'b9020000-%';
insert into public.concessionarias(id,nome_operacional) values
 ('ba020000-0000-4000-8000-000000000001','S1A loja sintética A'),
 ('ba020000-0000-4000-8000-000000000002','S1A loja sintética B');
insert into public.equipe_prumo_s1(ator_id,estado) values
 ('b9020000-0000-4000-8000-000000000001','ativo'),
 ('b9020000-0000-4000-8000-000000000002','ativo'),
 ('b9020000-0000-4000-8000-000000000003','pendente');
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel) values
 ('b9020000-0000-4000-8000-000000000001','ba020000-0000-4000-8000-000000000001','gestor'),
 ('b9020000-0000-4000-8000-000000000002','ba020000-0000-4000-8000-000000000001','operador'),
 ('b9020000-0000-4000-8000-000000000003','ba020000-0000-4000-8000-000000000002','gestor');
do $t$ begin
 if (select count(*) from public.equipe_prumo_eventos_s1
   where ator_id::text like 'b9020000-%')<>3
 or (select count(*) from public.equipe_prumo_s1
   where ator_id::text like 'b9020000-%')<>3
 then raise exception 'S1A-01 inserts internos interrompidos';end if;
end $t$;
\echo 'PASS S1A-01: somente postgres interno criou equipe e auditou'
do $t$ begin
 if pg_catalog.has_table_privilege('anon',
   'public.equipe_prumo_s1','UPDATE')
 or pg_catalog.has_table_privilege('authenticated',
   'public.equipe_prumo_s1','UPDATE')
 or pg_catalog.has_table_privilege('service_role',
   'public.equipe_prumo_s1','UPDATE')
 or pg_catalog.has_table_privilege('service_role',
   'public.equipe_prumo_s1','INSERT')
 then raise exception 'S1A-02 escrita concedida diretamente a cliente';end if;
end $t$;
\echo 'PASS S1A-02: cliente anon, autenticado e service_role sem DML de equipe'
set local role authenticated;
select pg_catalog.set_config('request.jwt.claim.sub',
 'b9020000-0000-4000-8000-000000000001',true);
do $t$ begin
 if (select count(*) from public.equipe_prumo_s1)<>1 then
  raise exception 'S1A-03 gestor consegue ler outra identidade';end if;
 begin
  update public.equipe_prumo_s1 set estado='desligado'
   where ator_id='b9020000-0000-4000-8000-000000000002';
  raise exception 'S1A-03 gestor mudou equipe';
 exception when insufficient_privilege then null;end;
end $t$;
\echo 'PASS S1A-03: gestor autenticado apenas sua propria linha, sem atualizar equipe'
select pg_catalog.set_config('request.jwt.claim.sub',
 'b9020000-0000-4000-8000-000000000002',true);
do $t$ begin
 if (select count(*) from public.equipe_prumo_s1)<>1 then
  raise exception 'S1A-04 operador consegue ler outra identidade';end if;
 begin
  insert into public.equipe_prumo_s1(ator_id,estado) values
   ('b9020000-0000-4000-8000-000000000002','ativo');
  raise exception 'S1A-04 operador se autocadastrou';
 exception when insufficient_privilege then null;end;
end $t$;
\echo 'PASS S1A-04: operador autenticado nao cria proprio cadastro'
-- O campo user_metadata e controlado pelo usuario, e nao pode liberar equipe:
-- o mock auth.uid() usa apenas sub fornecido pelo gateway de testes.
select pg_catalog.set_config('request.jwt.claims',
 '{"user_metadata":{"role":"rh_admin","tenant":"*","equipe_estado":"ativo"}, "app_metadata":{"role":"owner"}}',true);
do $t$ begin
 if (select count(*) from public.equipe_prumo_s1)<>1
 or (select count(*) from public.equipe_prumo_s1
  where ator_id='b9020000-0000-4000-8000-000000000001')<>0
 then raise exception 'S1A-05 metadados injetados ampliaram leitura';end if;
end $t$;
\echo 'PASS S1A-05: metadados injetados nao elevam identidade RLS'
select pg_catalog.set_config('request.jwt.claim.sub',
 'b9020000-0000-4000-8000-000000000003',true);
do $t$ begin
 if (select count(*) from public.equipe_prumo_s1)<>1 then
  raise exception 'S1A-06 pendente viu dados de outros';end if;
 if (select estado from public.equipe_prumo_s1) <> 'pendente' then
  raise exception 'S1A-06 pendente alterou estado';end if;
end $t$;
\echo 'PASS S1A-06: pendente ve apenas seu proprio estado'
reset role;
-- Simulacao local do service_role real: BYPASSRLS + permissao acidental.
-- Guard deve continuar negando mesmo quando RLS esta desligada para a role.
grant usage on schema public to service_role;
grant insert,update,delete on public.equipe_prumo_s1 to service_role;
grant insert on public.equipe_prumo_eventos_s1 to service_role;
alter role service_role bypassrls;
set local role service_role;
do $t$ begin
 begin
  update public.equipe_prumo_s1 set estado='suspenso'
  where ator_id='b9020000-0000-4000-8000-000000000001';
  raise exception 'S1A-07 service_role bypassrls fez UPDATE';
 exception when insufficient_privilege then null;end;
 begin
  insert into public.equipe_prumo_s1(ator_id,estado) values
   ('b9020000-0000-4000-8000-000000000001','ativo');
  raise exception 'S1A-07 service_role bypassrls fez INSERT';
 exception when insufficient_privilege then null;end;
 begin
  delete from public.equipe_prumo_s1
   where ator_id='b9020000-0000-4000-8000-000000000003';
  raise exception 'S1A-07 service_role bypassrls fez DELETE';
 exception when insufficient_privilege then null;end;
end $t$;
\echo 'PASS S1A-07: service_role BYPASSRLS com GRANT artificial rejeitado por trigger'
do $t$ begin
 begin
  insert into public.equipe_prumo_eventos_s1(
   ator_id,estado_anterior,estado_posterior)
  values('b9020000-0000-4000-8000-000000000001','ativo','suspenso');
  raise exception 'S1A-08 service_role escreveu evento RH';
 exception when insufficient_privilege then null;end;
end $t$;
\echo 'PASS S1A-08: evento RH nao aceita INSERT por service_role'
reset role;
do $t$ begin
 if (select count(*) from public.equipe_prumo_eventos_s1
   where ator_id::text like 'b9020000-%')<>3
 or (select count(*) from public.equipe_prumo_s1
   where ator_id::text like 'b9020000-%' and estado='ativo')<>2
 then raise exception 'S1A-09 ataques alteraram historico/equipe';end if;
end $t$;
\echo 'PASS S1A-09: estado e historia intactos apos tentativas negadas'
rollback;
