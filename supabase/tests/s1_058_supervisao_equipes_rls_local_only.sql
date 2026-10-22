\set ON_ERROR_STOP on
-- S1-002/I38 AUD-RLS-01: prova de divergencia e proposta local, nao migration.
-- Somente PostgreSQL 17 descartavel apos S0 e S1 migrations 038..052.
-- As policies candidatas sao ROLLBACK no final; NAO alterar a S0.
-- Sem Meta, Supabase hospedado, dados reais ou credenciais externas.
begin;
insert into auth.users(id)
select ('58110000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid
from generate_series(1,6) i;
insert into public.atores(id)
select id from auth.users where id::text like '58110000-%';
insert into public.equipe_prumo_s1(ator_id,estado)
select id,'ativo' from public.atores where id::text like '58110000-%';
insert into prumo_private.s1_gestor_operadores(gestor_id,operador_id) values
('58110000-0000-4000-8000-000000000001','58110000-0000-4000-8000-000000000004'),
('58110000-0000-4000-8000-000000000002','58110000-0000-4000-8000-000000000005'),
('58110000-0000-4000-8000-000000000003','58110000-0000-4000-8000-000000000006');
insert into public.concessionarias(id,nome_operacional)
values('58220000-0000-4000-8000-000000000001','S1 I38 Loja ficticia');
-- Gestores 1 e 2 possuem grant de mesma loja; Gestor 3 NAO tem grant.
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel) values
('58110000-0000-4000-8000-000000000001','58220000-0000-4000-8000-000000000001','gestor'),
('58110000-0000-4000-8000-000000000002','58220000-0000-4000-8000-000000000001','gestor'),
('58110000-0000-4000-8000-000000000004','58220000-0000-4000-8000-000000000001','operador'),
('58110000-0000-4000-8000-000000000005','58220000-0000-4000-8000-000000000001','operador'),
('58110000-0000-4000-8000-000000000006','58220000-0000-4000-8000-000000000001','operador');
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado)
select ('58330000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
'58220000-0000-4000-8000-000000000001','+558188888'||lpad(i::text,4,'0')
from generate_series(1,3) i;
insert into public.ciclos_comerciais(id,concessionaria_id,lead_id,status_comercial)
select ('58440000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
'58220000-0000-4000-8000-000000000001',
('58330000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
'em atendimento pelo operador' from generate_series(1,3) i;
insert into public.casos_humanos(id,concessionaria_id,lead_id,ciclo_id)
select ('58550000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
'58220000-0000-4000-8000-000000000001',
('58330000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
('58440000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid
from generate_series(1,3) i;
insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id)
select '58220000-0000-4000-8000-000000000001',
('58550000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
('58110000-0000-4000-8000-'||lpad((i+3)::text,12,'0'))::uuid
from generate_series(1,3) i;
insert into public.canais_loja(id,concessionaria_id,identificador_emissor)
values('58660000-0000-4000-8000-000000000001',
'58220000-0000-4000-8000-000000000001','S1-I38-SINTETICO');
insert into public.conversas(id,concessionaria_id,lead_id,canal_id,caso_id)
select ('58770000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
'58220000-0000-4000-8000-000000000001',
('58330000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
'58660000-0000-4000-8000-000000000001',
('58550000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid
from generate_series(1,3) i;
insert into public.mensagens(concessionaria_id,conversa_id,canal_id,caso_id,
direcao,origem,conteudo_sintetico,id_externo)
select '58220000-0000-4000-8000-000000000001',
('58770000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
'58660000-0000-4000-8000-000000000001',
('58550000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
'entrada','simulado','Inbound ficticio I38 '||i,'i38-in-'||i
from generate_series(1,3) i;

-- Demonstracao RED: duas equipes com grant da mesma loja veem outras carteiras.
set local role authenticated;
select pg_catalog.set_config('request.jwt.claim.sub',
 '58110000-0000-4000-8000-000000000001',true);
do $audit$ begin
 if (select count(*) from public.casos_humanos)<>3
 or (select count(*) from public.conversas)<>3
 or (select count(*) from public.mensagens)<>3 then
 raise exception 'I38-RED01 nao reproduziu visibilidade por loja';end if;
end $audit$;
\echo 'OBSERVED I38-RED01: gestor da equipe 1 ve casos de outras equipes na S0 atual'
select pg_catalog.set_config('request.jwt.claim.sub',
 '58110000-0000-4000-8000-000000000003',true);
do $audit$ begin
 if exists(select 1 from public.casos_humanos)
 or exists(select 1 from public.atribuicoes_humanas) then
 raise exception 'I38-RED02 baseline inesperado, rever contrato';end if;
end $audit$;
\echo 'OBSERVED I38-RED02: gestor da equipe 3 nao ve seus casos sem grant da loja'
reset role;

-- Somente CANDIDATO TRANSITORIO do laboratorio, sem aprovacao para S0.
-- Schema dedicado impede USAGE amplo no prumo_private.
create schema prumo_s1_i38_test authorization postgres;
-- SECURITY DEFINER deve ser auditado antes de qualquer uso real.
create function prumo_s1_i38_test.s1_58_eh_supervisor()
returns boolean language sql stable security definer set search_path='' as $fn$
 select exists(select 1 from prumo_private.s1_gestor_operadores g
               where g.gestor_id=(select auth.uid()) and g.encerrado_em is null)
 or exists(select 1 from public.vinculos_papel_escopo v
               where v.ator_id=(select auth.uid()) and v.papel='gestor'
               and v.valido_desde<=pg_catalog.statement_timestamp()
               and (v.valido_ate is null or v.valido_ate>pg_catalog.statement_timestamp()));
$fn$;
create function prumo_s1_i38_test.s1_58_caso_do_ator(p_loja uuid,p_caso uuid)
returns boolean language sql stable security definer set search_path='' as $fn$
 select exists(
   select 1 from public.atribuicoes_humanas a
   join public.equipe_prumo_s1 e on e.ator_id=a.operador_id and e.estado='ativo'
   where a.concessionaria_id=p_loja and a.caso_id=p_caso
    and a.encerrada_em is null and a.operador_id=(select auth.uid())
 ) or exists(
   select 1 from public.atribuicoes_humanas a
   join prumo_private.s1_gestor_operadores g on g.operador_id=a.operador_id
        and g.gestor_id=(select auth.uid()) and g.encerrado_em is null
   join public.equipe_prumo_s1 chefe on chefe.ator_id=g.gestor_id and chefe.estado='ativo'
   where a.concessionaria_id=p_loja and a.caso_id=p_caso and a.encerrada_em is null
 );
$fn$;
-- O teste usa apenas authenticated e helper sem argumentos de ator browser.
revoke all on function prumo_s1_i38_test.s1_58_eh_supervisor(),
 prumo_s1_i38_test.s1_58_caso_do_ator(uuid,uuid) from public,anon,service_role;
grant usage on schema prumo_s1_i38_test to authenticated;
grant execute on function prumo_s1_i38_test.s1_58_eh_supervisor(),
 prumo_s1_i38_test.s1_58_caso_do_ator(uuid,uuid) to authenticated;

create policy s1_58_casos_equipe on public.casos_humanos
 for select to authenticated
 using (prumo_s1_i38_test.s1_58_caso_do_ator(concessionaria_id,id));
create policy s1_58_atribuicoes_equipe on public.atribuicoes_humanas
 for select to authenticated
 using (prumo_s1_i38_test.s1_58_caso_do_ator(concessionaria_id,caso_id));
create policy s1_58_conversas_equipe on public.conversas
 for select to authenticated
 using (caso_id is not null and
        prumo_s1_i38_test.s1_58_caso_do_ator(concessionaria_id,caso_id));

create policy s1_58_casos_restrict on public.casos_humanos
 as restrictive for select to authenticated using (
 not prumo_s1_i38_test.s1_58_eh_supervisor()
 or prumo_s1_i38_test.s1_58_caso_do_ator(concessionaria_id,id));
create policy s1_58_atribuicoes_restrict on public.atribuicoes_humanas
 as restrictive for select to authenticated using (
 not prumo_s1_i38_test.s1_58_eh_supervisor()
 or prumo_s1_i38_test.s1_58_caso_do_ator(concessionaria_id,caso_id));
create policy s1_58_conversas_restrict on public.conversas
 as restrictive for select to authenticated using (
 not prumo_s1_i38_test.s1_58_eh_supervisor()
 or (caso_id is not null and
     prumo_s1_i38_test.s1_58_caso_do_ator(concessionaria_id,caso_id)));
create policy s1_58_mensagens_restrict on public.mensagens
 as restrictive for select to authenticated using (
 not prumo_s1_i38_test.s1_58_eh_supervisor()
 or (caso_id is not null and
     prumo_s1_i38_test.s1_58_caso_do_ator(concessionaria_id,caso_id)));

set local role authenticated;
select pg_catalog.set_config('request.jwt.claim.sub',
 '58110000-0000-4000-8000-000000000001',true);
do $audit$ begin
 if (select count(*) from public.casos_humanos)<>1
 or (select count(*) from public.atribuicoes_humanas)<>1
 or (select count(*) from public.conversas)<>1
 or (select count(*) from public.mensagens)<>1 then
 raise exception 'I38-GREEN01 equipe 1 vaza dados de outra equipe';end if;
end $audit$;
\echo 'PASS I38-GREEN01: gestor 1 somente equipe 1, casos/atribuicoes/conversas/mensagens'
select pg_catalog.set_config('request.jwt.claim.sub',
 '58110000-0000-4000-8000-000000000002',true);
do $audit$ begin
 if (select count(*) from public.casos_humanos)<>1
 or (select count(*) from public.mensagens)<>1 then
 raise exception 'I38-GREEN02 equipe 2 vaza';end if;
end $audit$;
\echo 'PASS I38-GREEN02: gestor 2 somente equipe 2 mesmo com grant da mesma loja'
select pg_catalog.set_config('request.jwt.claim.sub',
 '58110000-0000-4000-8000-000000000003',true);
do $audit$ begin
 if (select count(*) from public.casos_humanos)<>1
 or (select count(*) from public.atribuicoes_humanas)<>1
 or (select count(*) from public.conversas)<>1
 or (select count(*) from public.mensagens)<>1 then
 raise exception 'I38-GREEN03 gestor sem grant nao ve equipe';end if;
end $audit$;
\echo 'PASS I38-GREEN03: gestor 3 ve equipe propria sem grant geral de loja'
select pg_catalog.set_config('request.jwt.claim.sub',
 '58110000-0000-4000-8000-000000000004',true);
do $audit$ begin
 if (select count(*) from public.casos_humanos)<>1
 or (select count(*) from public.mensagens)<>1 then
 raise exception 'I38-GREEN04 consultor fora da sua carteira';end if;
end $audit$;
\echo 'PASS I38-GREEN04: consultor continua vendo apenas caso atribuido'
reset role;
rollback;
\echo 'PASS I38-ROLLBACK: policies e dados candidatos removidos integralmente'
