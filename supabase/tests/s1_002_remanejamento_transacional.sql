\set ON_ERROR_STOP on
-- S1R-01..08 — fixtures sintéticas, nenhum dado persiste após ROLLBACK.
begin;
insert into auth.users(id)
 select ('61020000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid
 from generate_series(1,5) as i;
insert into public.atores(id)
 select id from auth.users where id::text like '61020000-%';
insert into public.concessionarias(id,nome_operacional)
 select ('62020000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
        'S1R concessionaria ficticia '||i::text
 from generate_series(1,3) i;
insert into public.equipe_prumo_s1(ator_id,estado)
 select ('61020000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 case when i=5 then 'pendente' else 'ativo' end
 from generate_series(1,5) i;
-- O1 em A+B+C, O2 A+B, O3 A, M4 gestor A, O5 pendente A.
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel)
 select ('61020000-0000-4000-8000-'||lpad(t.actor::text,12,'0'))::uuid,
        ('62020000-0000-4000-8000-'||lpad(t.shop::text,12,'0'))::uuid,
        case when t.actor=4 then 'gestor' else 'operador' end
 from (values (1,1),(1,2),(1,3),(2,1),(2,2),(3,1),(4,1),(5,1)) as t(actor,shop);
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado)
 select ('63020000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
        ('62020000-0000-4000-8000-'||lpad((case when i in (1,2,3,6) then 1 when i=4 then 2 else 3 end)::text,12,'0'))::uuid,
        '+558100002'||lpad((case when i in(1,4,5) then 1 else i end)::text,4,'0')
 from generate_series(1,6) i;
insert into public.ciclos_comerciais(id,concessionaria_id,lead_id,status_comercial)
 select ('64020000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
        l.concessionaria_id,l.id,
        case when i=6 then 'vendido' when i=3 then 'cadastro enviado ao operador'
        else 'em atendimento pelo operador' end
 from generate_series(1,6) i
 join public.leads_loja l on l.id=('63020000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid;
insert into public.casos_humanos(id,concessionaria_id,lead_id,ciclo_id)
 select ('65020000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
        c.concessionaria_id,c.lead_id,c.id
 from generate_series(1,6) i
 join public.ciclos_comerciais c on c.id=('64020000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid;
insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id)
 select concessionaria_id,id,'61020000-0000-4000-8000-000000000001'::uuid
 from public.casos_humanos where id::text like '65020000-%';
\echo 'PASS S1R-01 fixtures A+B+C, quatro profissionais ativos e caso vendido'
do $q$
begin
 begin
  insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id)
  values('62020000-0000-4000-8000-000000000001',
  '65020000-0000-4000-8000-000000000001',
  '61020000-0000-4000-8000-000000000005');
  raise exception 'S1R-02 pending person accepted';
 exception when check_violation or unique_violation then null; end;
end $q$;
\echo 'PASS S1R-02 guard rejeita profissional pendente'
-- Revoga apenas B do operador O1, preservando A/C.
update public.vinculos_papel_escopo set valido_ate=statement_timestamp()
 where ator_id='61020000-0000-4000-8000-000000000001'
 and concessionaria_id='62020000-0000-4000-8000-000000000002';
do $q$
begin
 if (select count(*) from public.atribuicoes_humanas
 where operador_id='61020000-0000-4000-8000-000000000001' and encerrada_em is null)<>5
 or (select count(*) from public.atribuicoes_humanas
 where operador_id='61020000-0000-4000-8000-000000000002'
 and concessionaria_id='62020000-0000-4000-8000-000000000002' and encerrada_em is null)<>1
 or (select count(*) from prumo_private.s1_remanejamento_historico
 where motivo='ESCOPO_REVOGADO' and caso_id::text like '65020000-%')<>1 then
 raise exception 'S1R-03 B revoke failed: old %, new %, audit %',
 (select count(*) from public.atribuicoes_humanas
  where operador_id='61020000-0000-4000-8000-000000000001' and encerrada_em is null),
 (select count(*) from public.atribuicoes_humanas
  where operador_id='61020000-0000-4000-8000-000000000002'
   and concessionaria_id='62020000-0000-4000-8000-000000000002'
   and encerrada_em is null),
 (select count(*) from prumo_private.s1_remanejamento_historico
  where motivo='ESCOPO_REVOGADO' and caso_id::text like '65020000-%');end if;
end $q$;
\echo 'PASS S1R-03 revogacao B redistribui somente B'
-- Suspensao O1 distribui 3 A entre O2/O3; C sem substituto; terminal nao revive.
update public.equipe_prumo_s1 set estado='suspenso'
 where ator_id='61020000-0000-4000-8000-000000000001';
do $q$
declare o2 integer;o3 integer;
begin
 select count(*) into o2 from public.atribuicoes_humanas
 where concessionaria_id='62020000-0000-4000-8000-000000000001'
 and operador_id='61020000-0000-4000-8000-000000000002' and encerrada_em is null;
 select count(*) into o3 from public.atribuicoes_humanas
 where concessionaria_id='62020000-0000-4000-8000-000000000001'
 and operador_id='61020000-0000-4000-8000-000000000003' and encerrada_em is null;
 if o2+o3<>3 or abs(o2-o3)<>1
 or exists(select 1 from public.atribuicoes_humanas where
 operador_id='61020000-0000-4000-8000-000000000001' and encerrada_em is null)
 or (select count(*) from prumo_private.s1_remanejamento_pendencias
  where caso_id::text like '65020000-%')<>1
 or (select count(*) from prumo_private.s1_remanejamento_historico
  where caso_id::text like '65020000-%')<>6
 or (select count(*) from prumo_private.s1_remanejamento_historico
 where resultado='ENCERRADO_HISTORICO' and caso_id::text like '65020000-%')<>1
 then raise exception 'S1R-04 load %, %, queue/audit invalid',o2,o3;end if;
 if (select status_comercial from public.ciclos_comerciais
 where id='64020000-0000-4000-8000-000000000006')<>'vendido'
 then raise exception 'S1R-04 terminal business status changed';end if;
end $q$;
\echo 'PASS S1R-04 autoequilibrio A, fila C e ciclo terminal preservado'
-- Caso C ficou SEM atribuicao ativa; rejeicao aqui nao pode ser
-- causada pela restricao de unicidade, deve ser a guarda de equipe.
do $q$
begin
 begin
  insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id)
  values('62020000-0000-4000-8000-000000000003',
         '65020000-0000-4000-8000-000000000005',
         '61020000-0000-4000-8000-000000000001');
  raise exception 'S1R-09 suspenso recebeu caso de fila';
 exception when check_violation then null; end;
end $q$;
\echo 'PASS S1R-09 fila sem atribuicao rejeita novo operador suspenso'
set local role authenticated;
select set_config('request.jwt.claim.sub','61020000-0000-4000-8000-000000000001',true);
do $q$
begin
 if exists(select 1 from public.casos_humanos)
 or exists(select 1 from public.leads_loja) then
 raise exception 'S1R-05 suspended identity retained access';end if;
end $q$;
\echo 'PASS S1R-05 suspenso sem D2'
select set_config('request.jwt.claim.sub','61020000-0000-4000-8000-000000000004',true);
do $q$
begin
 if (select count(*) from public.casos_humanos)<>4
 or exists(select 1 from public.atribuicoes_humanas
 where operador_id='61020000-0000-4000-8000-000000000004')
 then raise exception 'S1R-06 manager auto-assigned incorrectly';end if;
end $q$;
\echo 'PASS S1R-06 gestor nao recebe casos por automacao'
reset role;
update public.equipe_prumo_s1 set estado='ativo'
 where ator_id='61020000-0000-4000-8000-000000000001';
do $q$
begin
 if exists(select 1 from public.atribuicoes_humanas where
 operador_id='61020000-0000-4000-8000-000000000001' and encerrada_em is null)
 or (select count(*) from public.atribuicoes_humanas
 where operador_id='61020000-0000-4000-8000-000000000001' and encerrada_em is not null)<>6
 then raise exception 'S1R-07 reactivation restored stale assignments';end if;
 begin
  insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id)
  values('62020000-0000-4000-8000-000000000002',
  '65020000-0000-4000-8000-000000000004',
  '61020000-0000-4000-8000-000000000001');
  raise exception 'S1R-07 revoked B could assign';
 exception when check_violation or unique_violation then null; end;
end $q$;
\echo 'PASS S1R-07 reativacao nao restaura carteira; B revogada'
set local role authenticated;
select set_config('request.jwt.claim.sub','61020000-0000-4000-8000-000000000002',true);
do $q$
begin
 begin
  perform prumo_private.s1_remanejar_ator(
   '61020000-0000-4000-8000-000000000002',null,'EQUIPE_INATIVA');
  raise exception 'S1R-08 public RPC exposure';
 exception when insufficient_privilege then null;end;
end $q$;
\echo 'PASS S1R-08 usuario autenticado nao executa remanejamento privado'
reset role;
rollback;
