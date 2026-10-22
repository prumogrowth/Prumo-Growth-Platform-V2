\set ON_ERROR_STOP on
-- S1-002 I39: ingressos novos entre equipes, fila sem titular, retomada e CAS.
-- Contrato 22/10: S1-D06..D09, D19. SIMULADOR PG17 somente.
-- O S0 deve continuar dono de casos/atribuicoes; NAO e migration operacional.
-- A permissao excepcional sem grant e integrada somente apos contrato S0/I55.
begin;
\ir s1_059_proto_fila_novos_setup_local_only.sql

-- Fixture sintética: tres Gestores, 3 Consultores, mesma loja.
insert into auth.users(id)
select ('59110000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid
from generate_series(1,6) i;
insert into public.atores(id)
select id from auth.users where id::text like '59110000-%';
insert into public.equipe_prumo_s1(ator_id,estado)
select id,'ativo' from public.atores where id::text like '59110000-%';
insert into prumo_private.s1_gestor_operadores(gestor_id,operador_id) values
('59110000-0000-4000-8000-000000000001','59110000-0000-4000-8000-000000000004'),
('59110000-0000-4000-8000-000000000002','59110000-0000-4000-8000-000000000005'),
('59110000-0000-4000-8000-000000000003','59110000-0000-4000-8000-000000000006');
insert into public.concessionarias(id,nome_operacional)
values('59220000-0000-4000-8000-000000000001','S1 I39 Loja ficticia');
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel) values
('59110000-0000-4000-8000-000000000001','59220000-0000-4000-8000-000000000001','gestor'),
('59110000-0000-4000-8000-000000000002','59220000-0000-4000-8000-000000000001','gestor'),
('59110000-0000-4000-8000-000000000004','59220000-0000-4000-8000-000000000001','operador'),
('59110000-0000-4000-8000-000000000005','59220000-0000-4000-8000-000000000001','operador'),
('59110000-0000-4000-8000-000000000006','59220000-0000-4000-8000-000000000001','operador');
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado)
select ('59330000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 '59220000-0000-4000-8000-000000000001','+558199999'||lpad(i::text,4,'0')
from generate_series(1,4) i;
insert into public.ciclos_comerciais(id,concessionaria_id,lead_id,status_comercial)
select ('59440000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 '59220000-0000-4000-8000-000000000001',
 ('59330000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 'em atendimento pelo operador'
from generate_series(1,4) i;
insert into public.casos_humanos(id,concessionaria_id,lead_id,ciclo_id)
select ('59550000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 '59220000-0000-4000-8000-000000000001',
 ('59330000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 ('59440000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid
from generate_series(1,4) i;

-- Caso 1 chega antes da pausa: permanece com o titular original.
do $t$ declare j jsonb;begin
 j:=prumo_private.s1_59_tentar_novo('59220000-0000-4000-8000-000000000001',
   '59550000-0000-4000-8000-000000000001');
 if j->>'outcome'<>'ASSIGNED_NEW'
 or j->>'operator_id'<>'59110000-0000-4000-8000-000000000004' then
  raise exception 'I39-01 primeiro caso nao atribuido %',j;end if;
end $t$;
select prumo_private.s1_definir_disponibilidade_leads_10(
 '59110000-0000-4000-8000-000000000001',
 '59110000-0000-4000-8000-000000000004',true,1);
select prumo_private.s1_definir_disponibilidade_leads_10(
 '59110000-0000-4000-8000-000000000003',
 '59110000-0000-4000-8000-000000000006',true,1);
do $t$ begin
 if (select estado from public.equipe_prumo_s1
   where ator_id='59110000-0000-4000-8000-000000000004')<>'ativo'
 or (select count(*) from public.atribuicoes_humanas
   where operador_id='59110000-0000-4000-8000-000000000004'
     and encerrada_em is null)<>1 then
  raise exception 'I39-02 pausa derrubou conta ou carteira';end if;
end $t$;
\echo 'PASS I39-01/02: pausa nao suspende conta nem remove caso existente'

-- Com C1/C3 pausados, lead NOVO vai a C2 de outra equipe.
do $t$ declare j jsonb;begin
 j:=prumo_private.s1_59_tentar_novo('59220000-0000-4000-8000-000000000001',
   '59550000-0000-4000-8000-000000000002');
 if j->>'outcome'<>'ASSIGNED_NEW'
 or j->>'operator_id'<>'59110000-0000-4000-8000-000000000005' then
  raise exception 'I39-03 distribuicao cruzada falhou %',j;end if;
end $t$;
\echo 'PASS I39-03: novo lead vai a Consultor habilitado de outra equipe'

select prumo_private.s1_definir_disponibilidade_leads_10(
 '59110000-0000-4000-8000-000000000002',
 '59110000-0000-4000-8000-000000000005',true,1);
do $t$ declare j jsonb;begin
 j:=prumo_private.s1_59_tentar_novo('59220000-0000-4000-8000-000000000001',
   '59550000-0000-4000-8000-000000000003');
 if j->>'outcome'<>'QUEUED_UNOWNED' then
  raise exception 'I39-04 fila nao criada %',j;end if;
 j:=prumo_private.s1_59_tentar_novo('59220000-0000-4000-8000-000000000001',
   '59550000-0000-4000-8000-000000000004');
 if j->>'outcome'<>'QUEUED_UNOWNED' then
  raise exception 'I39-04 segundo lead nao entrou fila %',j;end if;
 if (select count(*) from public.s1_fila_novos_59 where estado='PENDENTE')<>2
 or (select count(*) from public.atribuicoes_humanas where caso_id in
  ('59550000-0000-4000-8000-000000000003',
   '59550000-0000-4000-8000-000000000004'))<>0 then
  raise exception 'I39-04 fila criou titular artificial';end if;
end $t$;
\echo 'PASS I39-04: fila de dois leads novos sem titular'

-- A fila eh compartilhada por LOJA autorizada, nao por chefia;
-- gestor 3 e Consultor nunca veem a fila (nem DML).
set local role authenticated;
select pg_catalog.set_config('request.jwt.claim.sub',
 '59110000-0000-4000-8000-000000000001',true);
do $t$ begin
 if (select count(*) from public.s1_fila_novos_59)<>2 then
  raise exception 'I39-05 gestor 1 nao ve fila autorizada';end if;
 begin
  update public.s1_fila_novos_59 set versao=999;
  raise exception 'I39-05 cliente atualizou fila';
 exception when insufficient_privilege then null;end;
end $t$;
select pg_catalog.set_config('request.jwt.claim.sub',
 '59110000-0000-4000-8000-000000000002',true);
do $t$ begin
 if (select count(*) from public.s1_fila_novos_59)<>2 then
  raise exception 'I39-05 gestor 2 nao ve fila compartilhada';end if;
end $t$;
select pg_catalog.set_config('request.jwt.claim.sub',
 '59110000-0000-4000-8000-000000000003',true);
do $t$ begin
 if exists(select 1 from public.s1_fila_novos_59) then
  raise exception 'I39-05 gestor nao autorizado ve fila';end if;
end $t$;
select pg_catalog.set_config('request.jwt.claim.sub',
 '59110000-0000-4000-8000-000000000005',true);
do $t$ begin
 if exists(select 1 from public.s1_fila_novos_59) then
  raise exception 'I39-05 consultor ve fila gerencial';end if;
end $t$;
reset role;
\echo 'PASS I39-05: fila exclusiva a Gestores autorizados para a loja'

do $t$ declare j jsonb;begin
 begin
  perform prumo_private.s1_59_assumir(
   '59110000-0000-4000-8000-000000000003',
   '59220000-0000-4000-8000-000000000001',
   '59550000-0000-4000-8000-000000000003',1);
  raise exception 'I39-06 gestor de loja alheia assumiu';
 exception when insufficient_privilege then null;end;
 j:=prumo_private.s1_59_assumir(
   '59110000-0000-4000-8000-000000000001',
   '59220000-0000-4000-8000-000000000001',
   '59550000-0000-4000-8000-000000000003',1);
 if j->>'outcome'<>'CLAIMED_BY_MANAGER' then
  raise exception 'I39-06 assuncao falhou %',j;end if;
 begin
  perform prumo_private.s1_59_assumir(
   '59110000-0000-4000-8000-000000000002',
   '59220000-0000-4000-8000-000000000001',
   '59550000-0000-4000-8000-000000000003',1);
  raise exception 'I39-06 segunda assuncao indevida';
 exception when serialization_failure then null;end;
 if (select count(*) from public.atribuicoes_humanas
  where caso_id='59550000-0000-4000-8000-000000000003'
  and encerrada_em is null)<>1 then
  raise exception 'I39-06 duplicidade de titular';end if;
end $t$;
\echo 'PASS I39-06: assuncao autorizada, CAS antigo rejeitado'

-- C1 volta: somente caso 4 SEM TITULAR reentra em distribuicao.
select prumo_private.s1_definir_disponibilidade_leads_10(
 '59110000-0000-4000-8000-000000000001',
 '59110000-0000-4000-8000-000000000004',false,2);
do $t$ declare j jsonb;begin
 j:=prumo_private.s1_59_tentar_novo('59220000-0000-4000-8000-000000000001',
   '59550000-0000-4000-8000-000000000004');
 if j->>'outcome'<>'ASSIGNED_NEW'
 or j->>'operator_id'<>'59110000-0000-4000-8000-000000000004' then
  raise exception 'I39-07 retomada da fila nao atribuiu corretamente %',j;end if;
 j:=prumo_private.s1_59_tentar_novo('59220000-0000-4000-8000-000000000001',
   '59550000-0000-4000-8000-000000000003');
 if j->>'outcome'<>'ALREADY_OWNED' then
  raise exception 'I39-07 caso assumido alterado %',j;end if;
 if (select count(*) from public.s1_fila_novos_59 where estado='PENDENTE')<>0
 or (select count(*) from public.atribuicoes_humanas
     where caso_id in ('59550000-0000-4000-8000-000000000003',
                      '59550000-0000-4000-8000-000000000004')
       and encerrada_em is null)<>2
 or (select count(distinct operador_id) from public.atribuicoes_humanas
     where caso_id='59550000-0000-4000-8000-000000000003'
       and encerrada_em is null)<>1 then
  raise exception 'I39-07 fila/casos inconsistentes';end if;
end $t$;
\echo 'PASS I39-07: retomada reatribui somente fila ainda sem titular'

-- O caso 1 do Consultor pausado permaneceu o tempo todo com ele; a conta
-- continuou ativa. Nao fazer conclusao falsa sobre redistribuicao S0 sem prova.
do $t$ begin
 if (select count(*) from public.atribuicoes_humanas
  where caso_id='59550000-0000-4000-8000-000000000001'
   and operador_id='59110000-0000-4000-8000-000000000004'
   and encerrada_em is null)<>1
 or (select count(*) from public.s1_fila_novos_59)<>2 then
  raise exception 'I39-08 caso preexistente perdido ou log de fila apagado';end if;
end $t$;
rollback;
\echo 'PASS I39-08/ROLLBACK: carteira preexistente preservada e fixture removida'
