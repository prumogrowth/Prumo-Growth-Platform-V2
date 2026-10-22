\set ON_ERROR_STOP on
-- S1-002 I39: ingressos novos entre equipes, fila sem titular, retomada e CAS.
-- Contrato 22/10: S1-D06..D09, D19. SIMULADOR PG17 somente.
-- O S0 deve continuar dono de casos/atribuicoes; NAO e migration operacional.
-- A permissao excepcional sem grant e integrada somente apos contrato S0/I55.
begin;
\ir s1_053_issue10_disponibilidade_local_only.sql

-- Tabela laboratorial. A fila so expõe PENDENTE sem titular; nunca o
-- historico de casos atribuidos de outra equipe.
create table public.s1_fila_novos_59(
 concessionaria_id uuid not null,
 caso_id uuid not null,
 estado text not null default 'PENDENTE'
  check(estado in ('PENDENTE','ATRIBUIDO')),
 versao bigint not null default 1 check(versao>=1),
 atribuicao_id uuid references public.atribuicoes_humanas(id),
 criado_em timestamptz not null default pg_catalog.statement_timestamp(),
 atualizado_em timestamptz not null default pg_catalog.statement_timestamp(),
 primary key(concessionaria_id,caso_id),
 foreign key(concessionaria_id,caso_id)
  references public.casos_humanos(concessionaria_id,id),
 check((estado='PENDENTE' and atribuicao_id is null) or
       (estado='ATRIBUIDO' and atribuicao_id is not null))
);
alter table public.s1_fila_novos_59 enable row level security;
revoke all on public.s1_fila_novos_59 from public,anon,authenticated,service_role;
grant select(concessionaria_id,caso_id,estado,versao,criado_em)
 on public.s1_fila_novos_59 to authenticated;
create policy s1_59_fila_gestor_autorizado
 on public.s1_fila_novos_59 for select to authenticated using (
  estado='PENDENTE'
  and exists(select 1 from public.equipe_prumo_s1 e
   where e.ator_id=(select auth.uid()) and e.estado='ativo')
  and exists(select 1 from public.vinculos_papel_escopo v
   where v.ator_id=(select auth.uid())
    and v.concessionaria_id=s1_fila_novos_59.concessionaria_id
    and v.papel='gestor'
    and v.valido_desde<=pg_catalog.statement_timestamp()
    and (v.valido_ate is null or v.valido_ate>pg_catalog.statement_timestamp()))
 );

-- Acesso INTERNAL_ONLY, nenhum parametro p_gestor vindo do frontend.
-- Ordem de lock S0: caso ANTES da atribuicao/fila.
-- Em produção S0 precisara fornecer evento e versao/canal de handoff.
create function prumo_private.s1_59_tentar_novo(p_loja uuid,p_caso uuid)
returns jsonb language plpgsql security invoker set search_path='' as $fn$
declare v_destino uuid;v_atr uuid;v_estado text;v_existente uuid;
begin
 if current_user<>'postgres' then
  raise exception 'INTERNAL_ONLY' using errcode='42501';end if;
 if p_loja is null or p_caso is null then
  raise exception 'NOVO_INVALIDO' using errcode='22023';end if;
 perform 1 from public.casos_humanos h
  where h.concessionaria_id=p_loja and h.id=p_caso for update of h;
 if not found then raise exception 'CASO_S0_DESCONHECIDO' using errcode='22023';end if;
 select a.id into v_existente from public.atribuicoes_humanas a
  where a.concessionaria_id=p_loja and a.caso_id=p_caso
    and a.encerrada_em is null for update of a;
 select f.estado into v_estado from public.s1_fila_novos_59 f
  where f.concessionaria_id=p_loja and f.caso_id=p_caso for update of f;
 if v_existente is not null then
  if v_estado='PENDENTE' then
   raise exception 'FILA_TITULARIDADE_DIVERGENTE' using errcode='40001';end if;
  return pg_catalog.jsonb_build_object('outcome','ALREADY_OWNED');
 end if;
 if v_estado='ATRIBUIDO' then
  raise exception 'FILA_TITULARIDADE_DIVERGENTE' using errcode='40001';end if;
 -- Nao filtrar pela equipe do Gestor da loja nem pelo time de origem.
 -- Locks de equipe e grant impedem mudanca de elegibilidade ate o commit.
 select e.ator_id into v_destino from public.equipe_prumo_s1 e
 join prumo_private.s1_gestor_operadores g on
  g.operador_id=e.ator_id and g.encerrado_em is null
 join public.equipe_prumo_s1 chefe on
  chefe.ator_id=g.gestor_id and chefe.estado='ativo'
 join public.vinculos_papel_escopo v on
  v.ator_id=e.ator_id and v.concessionaria_id=p_loja
  and v.papel='operador'
  and v.valido_desde<=pg_catalog.statement_timestamp()
  and (v.valido_ate is null or v.valido_ate>pg_catalog.statement_timestamp())
 join public.concessionarias l on l.id=p_loja and l.ativo
 left join prumo_private.s1_disponibilidade_leads_10 d
  on d.operador_id=e.ator_id
 where e.estado='ativo' and coalesce(d.pausado,false)=false
 order by (select count(*) from public.atribuicoes_humanas a
            where a.operador_id=e.ator_id and a.encerrada_em is null),
          e.ator_id
 limit 1 for share of e,g,chefe,v,l;
 if v_destino is null then
  insert into public.s1_fila_novos_59(concessionaria_id,caso_id)
   values(p_loja,p_caso) on conflict(concessionaria_id,caso_id) do nothing;
  return pg_catalog.jsonb_build_object('outcome','QUEUED_UNOWNED');
 end if;
 -- Indice unico parcial S0 impede duas atribuicoes ativas (ultimo gate).
 insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id)
  values(p_loja,p_caso,v_destino) returning id into v_atr;
 if v_estado='PENDENTE' then
  update public.s1_fila_novos_59 set estado='ATRIBUIDO',
   atribuicao_id=v_atr,versao=versao+1,
   atualizado_em=pg_catalog.statement_timestamp()
   where concessionaria_id=p_loja and caso_id=p_caso;
 end if;
 return pg_catalog.jsonb_build_object('outcome','ASSIGNED_NEW',
  'operator_id',v_destino,'assignment_id',v_atr);
end $fn$;

-- Assuncao por Gestor: autorizacao somente da loja daquela fila,
-- CAS versionado, S0 case lock + um titular por caso. Nunca concede loja.
create function prumo_private.s1_59_assumir(
 p_gestor uuid,p_loja uuid,p_caso uuid,p_versao_esperada bigint)
returns jsonb language plpgsql security invoker set search_path='' as $fn$
declare v_estado text;v_versao bigint;v_atr uuid;
begin
 if current_user<>'postgres' then
  raise exception 'INTERNAL_ONLY' using errcode='42501';end if;
 if p_gestor is null or p_loja is null or p_caso is null
  or p_versao_esperada is null or p_versao_esperada<1 then
  raise exception 'ASSUNCAO_INVALIDA' using errcode='22023';end if;
 perform 1 from public.casos_humanos h
  where h.concessionaria_id=p_loja and h.id=p_caso for update of h;
 if not found then raise exception 'CASO_DESCONHECIDO' using errcode='22023';end if;
 select f.estado,f.versao into v_estado,v_versao
  from public.s1_fila_novos_59 f
  where f.concessionaria_id=p_loja and f.caso_id=p_caso for update of f;
 if v_estado is distinct from 'PENDENTE' or v_versao<>p_versao_esperada then
  raise exception 'FILA_CAS_OBSOLETO' using errcode='40001';end if;
 -- Revalidar alçada sob locks de conta, loja e vinculo.
 perform 1 from public.equipe_prumo_s1 e
  join public.vinculos_papel_escopo v
   on v.ator_id=e.ator_id and v.concessionaria_id=p_loja
    and v.papel='gestor'
    and v.valido_desde<=pg_catalog.statement_timestamp()
    and (v.valido_ate is null or v.valido_ate>pg_catalog.statement_timestamp())
  join public.concessionarias l on l.id=p_loja and l.ativo
  where e.ator_id=p_gestor and e.estado='ativo'
  for share of e,v,l;
 if not found then
  raise exception 'GESTOR_SEM_AUTORIZACAO_LOJA' using errcode='42501';end if;
 if exists(select 1 from public.atribuicoes_humanas a
  where a.concessionaria_id=p_loja and a.caso_id=p_caso
    and a.encerrada_em is null) then
  raise exception 'CASO_JA_POSSUI_TITULAR' using errcode='40001';end if;
 insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id)
  values(p_loja,p_caso,p_gestor) returning id into v_atr;
 update public.s1_fila_novos_59 set estado='ATRIBUIDO',
  versao=versao+1,atribuicao_id=v_atr,
  atualizado_em=pg_catalog.statement_timestamp()
  where concessionaria_id=p_loja and caso_id=p_caso and estado='PENDENTE';
 return pg_catalog.jsonb_build_object('outcome','CLAIMED_BY_MANAGER',
  'operator_id',p_gestor,'assignment_id',v_atr);
end $fn$;
revoke all on function prumo_private.s1_59_tentar_novo(uuid,uuid),
 prumo_private.s1_59_assumir(uuid,uuid,uuid,bigint)
 from public,anon,authenticated,service_role;

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
