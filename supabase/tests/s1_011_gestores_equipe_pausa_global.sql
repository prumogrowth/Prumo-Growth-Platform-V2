\set ON_ERROR_STOP on
-- S1T: decisao 19/10, gestor lidera equipe; pausa global, lojas configuradas
-- pelos responsáveis. PG17 local, nenhuma autenticação GoTrue real.
begin;
insert into auth.users(id)
 select ('a1120000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid
 from generate_series(1,7) i;
insert into public.atores(id)
 select id from auth.users where id::text like 'a1120000-%';
insert into public.equipe_prumo_s1(ator_id,estado)
 select id,'ativo' from public.atores where id::text like 'a1120000-%';
insert into prumo_private.s1_responsaveis_plataforma(ator_id)
 values('a1120000-0000-4000-8000-000000000001');
insert into prumo_private.s1_gestor_operadores(gestor_id,operador_id) values
 ('a1120000-0000-4000-8000-000000000002','a1120000-0000-4000-8000-000000000004'),
 ('a1120000-0000-4000-8000-000000000002','a1120000-0000-4000-8000-000000000005'),
 ('a1120000-0000-4000-8000-000000000003','a1120000-0000-4000-8000-000000000006');
insert into public.concessionarias(id,nome_operacional) values
 ('a2120000-0000-4000-8000-000000000001','S1T concessionaria A'),
 ('a2120000-0000-4000-8000-000000000002','S1T concessionaria B'),
 ('a2120000-0000-4000-8000-000000000003','S1T concessionaria C');
-- Os gestores NAO possuem concessoes de loja; a equipe é independente.
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel) values
 ('a1120000-0000-4000-8000-000000000004','a2120000-0000-4000-8000-000000000001','operador'),
 ('a1120000-0000-4000-8000-000000000004','a2120000-0000-4000-8000-000000000002','operador'),
 ('a1120000-0000-4000-8000-000000000005','a2120000-0000-4000-8000-000000000001','operador'),
 ('a1120000-0000-4000-8000-000000000005','a2120000-0000-4000-8000-000000000002','operador'),
 ('a1120000-0000-4000-8000-000000000006','a2120000-0000-4000-8000-000000000003','operador');
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado)
 select ('a3120000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 ('a2120000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 '+5581987600'||lpad(i::text,4,'0') from generate_series(1,3) i;
insert into public.ciclos_comerciais(id,concessionaria_id,lead_id,status_comercial)
 select ('a4120000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 ('a2120000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 ('a3120000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 'em atendimento pelo operador' from generate_series(1,3) i;
insert into public.casos_humanos(id,concessionaria_id,lead_id,ciclo_id)
 select ('a5120000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 ('a2120000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 ('a3120000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 ('a4120000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid
 from generate_series(1,3) i;
insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id)
 select concessionaria_id,id,
 case when concessionaria_id='a2120000-0000-4000-8000-000000000003'
 then 'a1120000-0000-4000-8000-000000000006'::uuid
 else 'a1120000-0000-4000-8000-000000000004'::uuid end
 from public.casos_humanos where id::text like 'a5120000-%';
\echo 'PASS S1T-01: responsavel plataforma, duas chefias, operadores A/B e C'
do $t$ begin
 if not prumo_private.s1_pode_administrar_operador(
  'a1120000-0000-4000-8000-000000000001',null,
  'adicionar_operador','a1120000-0000-4000-8000-000000000007')
 or not prumo_private.s1_pode_administrar_operador(
  'a1120000-0000-4000-8000-000000000001',null,
  'adicionar_gestor','a1120000-0000-4000-8000-000000000007')
 or not prumo_private.s1_pode_administrar_operador(
  'a1120000-0000-4000-8000-000000000001',null,
  'desligar_definitivo_operador','a1120000-0000-4000-8000-000000000004')
 then raise exception 'S1T-02 responsavel plataforma sem alçada';end if;
end $t$;
\echo 'PASS S1T-02: somente responsavel da plataforma adiciona e desliga definitivamente'
do $t$ begin
 if not prumo_private.s1_pode_administrar_operador(
  'a1120000-0000-4000-8000-000000000001',
  'a2120000-0000-4000-8000-000000000003',
  'conceder_concessionaria_operador','a1120000-0000-4000-8000-000000000004')
 or not prumo_private.s1_pode_administrar_operador(
  'a1120000-0000-4000-8000-000000000001',
  'a2120000-0000-4000-8000-000000000001',
  'revogar_concessionaria_operador','a1120000-0000-4000-8000-000000000004')
 then raise exception 'S1T-03 concessoes nao estao no responsavel';end if;
end $t$;
\echo 'PASS S1T-03: grants A/B/C são competencia de responsavel, nao da chefia'
do $t$ begin
 if not prumo_private.s1_pode_administrar_operador(
  'a1120000-0000-4000-8000-000000000002',null,
  'suspender_temporariamente','a1120000-0000-4000-8000-000000000004')
 or not prumo_private.s1_pode_administrar_operador(
  'a1120000-0000-4000-8000-000000000002',null,
  'reativar_temporariamente','a1120000-0000-4000-8000-000000000004')
 or not prumo_private.s1_pode_administrar_operador(
  'a1120000-0000-4000-8000-000000000002',
  'a2120000-0000-4000-8000-000000000002',
  'redistribuir_carteira','a1120000-0000-4000-8000-000000000004')
 then raise exception 'S1T-04 chefia exige grant de loja indevidamente';end if;
end $t$;
\echo 'PASS S1T-04: gestor pode agir sobre sua equipe sem possuir loja'
do $t$ begin
 if prumo_private.s1_pode_administrar_operador(
  'a1120000-0000-4000-8000-000000000002',
  'a2120000-0000-4000-8000-000000000003',
  'conceder_concessionaria_operador','a1120000-0000-4000-8000-000000000004')
 or prumo_private.s1_pode_administrar_operador(
  'a1120000-0000-4000-8000-000000000002',
  'a2120000-0000-4000-8000-000000000001',
  'revogar_concessionaria_operador','a1120000-0000-4000-8000-000000000004')
 or prumo_private.s1_pode_administrar_operador(
  'a1120000-0000-4000-8000-000000000002',null,
  'adicionar_operador','a1120000-0000-4000-8000-000000000007')
 or prumo_private.s1_pode_administrar_operador(
  'a1120000-0000-4000-8000-000000000002',null,
  'desligar_definitivo_operador','a1120000-0000-4000-8000-000000000004')
 then raise exception 'S1T-05 gestor ganhou acesso de responsavel';end if;
end $t$;
\echo 'PASS S1T-05: gestor não muda grants, não cria e não exclui definitivamente'
do $t$ begin
 if prumo_private.s1_pode_administrar_operador(
  'a1120000-0000-4000-8000-000000000002',null,
  'suspender_temporariamente','a1120000-0000-4000-8000-000000000006')
 or prumo_private.s1_pode_administrar_operador(
  'a1120000-0000-4000-8000-000000000003',null,
  'suspender_temporariamente','a1120000-0000-4000-8000-000000000004')
 then raise exception 'S1T-06 alçada cruzou equipes';end if;
end $t$;
\echo 'PASS S1T-06: gestor não interfere em operador de outra chefia'
do $t$ declare j jsonb;begin
 j:=prumo_private.s1_pausar_operador_da_equipe(
  'a1120000-0000-4000-8000-000000000002',
  'a1120000-0000-4000-8000-000000000004','AUSENCIA_TEMPORARIA');
 if j->>'outcome'<>'PAUSED_GLOBAL'
 or (select estado from public.equipe_prumo_s1
  where ator_id='a1120000-0000-4000-8000-000000000004')<>'suspenso'
 then raise exception 'S1T-07 pausa não executada %',j;end if;
end $t$;
\echo 'PASS S1T-07: ausência temporária pausa operador em todas as lojas'
do $t$ begin
 if (select count(*) from public.atribuicoes_humanas
  where operador_id='a1120000-0000-4000-8000-000000000004'
   and encerrada_em is null)<>0
 or (select count(*) from public.atribuicoes_humanas
  where operador_id='a1120000-0000-4000-8000-000000000005'
   and encerrada_em is null
   and caso_id in ('a5120000-0000-4000-8000-000000000001',
                   'a5120000-0000-4000-8000-000000000002'))<>2
 or (select count(*) from public.atribuicoes_humanas
  where operador_id='a1120000-0000-4000-8000-000000000006'
   and encerrada_em is null)<>1
 or (select count(*) from prumo_private.s1_remanejamento_historico
  where operador_anterior='a1120000-0000-4000-8000-000000000004'
   and resultado='REDISTRIBUIDO')<>2
 then raise exception 'S1T-08 carteira A/B não remanejada ou C afetada';end if;
 if (select count(*) from public.vinculos_papel_escopo
  where ator_id='a1120000-0000-4000-8000-000000000004')<>2
 then raise exception 'S1T-08 gestor alterou concessões';end if;
end $t$;
\echo 'PASS S1T-08: A/B redistribuídos, C intacta e grants do operador preservados'
set local role authenticated;
select pg_catalog.set_config('request.jwt.claim.sub',
 'a1120000-0000-4000-8000-000000000004',true);
do $t$ begin
 if exists(select 1 from public.casos_humanos) then
  raise exception 'S1T-09 operador pausado consegue ler casos';end if;
end $t$;
\echo 'PASS S1T-09: operador temporariamente pausado não acessa casos'
reset role;
do $t$ declare j jsonb;begin
 j:=prumo_private.s1_reativar_operador_da_equipe(
  'a1120000-0000-4000-8000-000000000002',
  'a1120000-0000-4000-8000-000000000004');
 if j->>'outcome'<>'ACTIVE_GLOBAL'
 or (select count(*) from public.atribuicoes_humanas
  where operador_id='a1120000-0000-4000-8000-000000000004'
   and encerrada_em is null)<>0
 then raise exception 'S1T-10 reativação resgatou carteira antiga %',j;end if;
end $t$;
\echo 'PASS S1T-10: retorno libera distribuição futura sem recuperar casos antigos'
do $t$ begin
 if (select count(*) from prumo_private.s1_pausas_operadores_historico
  where operador_id='a1120000-0000-4000-8000-000000000004')<>2
 or (select count(*) from public.vinculos_papel_escopo
  where ator_id='a1120000-0000-4000-8000-000000000004')<>2
 then raise exception 'S1T-11 histórico/carteira/grants inconsistentes';end if;
 begin
  update prumo_private.s1_pausas_operadores_historico
   set motivo_codigo='INDISPONIBILIDADE_OPERACIONAL'
   where operador_id='a1120000-0000-4000-8000-000000000004';
  raise exception 'S1T-11 histórico modificável';
 exception when check_violation then null;end;
end $t$;
\echo 'PASS S1T-11: dois eventos append-only, sem alterar grants'
do $t$ begin
 begin
  perform prumo_private.s1_pausar_operador_da_equipe(
   'a1120000-0000-4000-8000-000000000003',
   'a1120000-0000-4000-8000-000000000004','AUSENCIA_TEMPORARIA');
  raise exception 'S1T-12 gestor outra equipe conseguiu pausar';
 exception when insufficient_privilege then null;end;
 begin
  perform prumo_private.s1_pausar_operador_da_equipe(
   'a1120000-0000-4000-8000-000000000002',
   'a1120000-0000-4000-8000-000000000004','ATESTADO COM DIAGNOSTICO');
  raise exception 'S1T-12 motivo médico livre aceito';
 exception when invalid_parameter_value then null;end;
end $t$;
\echo 'PASS S1T-12: equipe alheia bloqueada e motivo médico livre não persistido'
set local role authenticated;
select pg_catalog.set_config('request.jwt.claim.sub',
 'a1120000-0000-4000-8000-000000000002',true);
do $t$ begin
 begin
  perform prumo_private.s1_pausar_operador_da_equipe(
   'a1120000-0000-4000-8000-000000000002',
   'a1120000-0000-4000-8000-000000000004',
   'AUSENCIA_TEMPORARIA');
  raise exception 'S1T-13 função interna virou RPC';
 exception when insufficient_privilege then null;end;
end $t$;
\echo 'PASS S1T-13: função de pausa não exposta ao cliente autenticado'
reset role;
-- Um responsável autoriza a concessionária C para o MESMO operador.
-- A equipe do gestor e sua gestão não precisam ser modificadas.
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel)
 values('a1120000-0000-4000-8000-000000000004',
        'a2120000-0000-4000-8000-000000000003','operador');
do $t$ begin
 if (select count(*) from prumo_private.s1_gestor_operadores
  where gestor_id='a1120000-0000-4000-8000-000000000002'
   and operador_id='a1120000-0000-4000-8000-000000000004'
   and encerrado_em is null)<>1
 or not prumo_private.s1_pode_administrar_operador(
  'a1120000-0000-4000-8000-000000000002',
  'a2120000-0000-4000-8000-000000000003',
  'redistribuir_carteira','a1120000-0000-4000-8000-000000000004')
 or exists(select 1 from public.vinculos_papel_escopo
  where ator_id='a1120000-0000-4000-8000-000000000002'
    and concessionaria_id='a2120000-0000-4000-8000-000000000003')
 then raise exception 'S1T-14 novo grant C alterou gestao da equipe';end if;
end $t$;
\echo 'PASS S1T-14: adicionar loja C não altera chefia nem exige grant C do gestor'
rollback;
