\set ON_ERROR_STOP on
-- S1B: backlog >25, justa varredura, status terminal e anti-invasao de loja.
-- 100 casos sinteticos, ROLLBACK completo. Executar DEPOIS da migration 043.
begin;
insert into auth.users(id)
 select ('c1020000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid
 from generate_series(1,5) i;
insert into public.atores(id)
 select id from auth.users where id::text like 'c1020000-%';
insert into public.concessionarias(id,nome_operacional) values
 ('c2020000-0000-4000-8000-000000000001','S1B Loja A ficticia'),
 ('c2020000-0000-4000-8000-000000000002','S1B Loja B ficticia');
insert into public.equipe_prumo_s1(ator_id,estado)
 select id,case
  when id::text like '%000000000002' or id::text like '%000000000005' then 'pendente'
  when id::text like '%000000000003' then 'ativo'
  else 'suspenso' end
 from public.atores where id::text like 'c1020000-%';
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel) values
 ('c1020000-0000-4000-8000-000000000002','c2020000-0000-4000-8000-000000000001','operador'),
 ('c1020000-0000-4000-8000-000000000003','c2020000-0000-4000-8000-000000000002','operador'),
 ('c1020000-0000-4000-8000-000000000005','c2020000-0000-4000-8000-000000000002','operador');
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado)
 select ('c3020000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 case when i<=60 then 'c2020000-0000-4000-8000-000000000001'::uuid
 else 'c2020000-0000-4000-8000-000000000002'::uuid end,
 '+558198400'||lpad(i::text,4,'0') from generate_series(1,100) i;
insert into public.ciclos_comerciais(id,concessionaria_id,lead_id,status_comercial)
 select ('c4020000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 l.concessionaria_id,l.id,'em atendimento pelo operador'
 from generate_series(1,100) i join public.leads_loja l
 on l.id=('c3020000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid;
insert into public.casos_humanos(id,concessionaria_id,lead_id,ciclo_id)
 select ('c5020000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 c.concessionaria_id,c.lead_id,c.id
 from generate_series(1,100) i join public.ciclos_comerciais c
 on c.id=('c4020000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid;
-- Pendencias representam estado JA protegido por um processo I2 anterior.
insert into prumo_private.s1_remanejamento_pendencias(
 concessionaria_id,caso_id,operador_anterior,motivo)
 select h.concessionaria_id,h.id,
 ('c1020000-0000-4000-8000-'||lpad(
   case when i<=60 then '1' when i<=90 then '3' else '4' end,12,'0'))::uuid,
 'EQUIPE_INATIVA'
 from generate_series(1,100) i join public.casos_humanos h
 on h.id=('c5020000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid;
update public.ciclos_comerciais set status_comercial='vendido'
 where id='c4020000-0000-4000-8000-000000000060';
do $t$ begin
 if (select count(*) from prumo_private.s1_remanejamento_pendencias
  where caso_id::text like 'c5020000-%')<>100
 then raise exception 'S1B-01 fixture nao criada';end if;
end $t$;
\echo 'PASS S1B-01: 100 pendencias privadas em 2 lojas, sendo uma venda terminal'
-- Ativar O2 em A deve recuperar apenas 25 e nao trazer nenhum B.
update public.equipe_prumo_s1 set estado='ativo'
 where ator_id='c1020000-0000-4000-8000-000000000002';
do $t$ begin
 if (select count(*) from prumo_private.s1_remanejamento_pendencias
  where concessionaria_id='c2020000-0000-4000-8000-000000000001')<>35
 or (select count(*) from prumo_private.s1_remanejamento_pendencias
  where concessionaria_id='c2020000-0000-4000-8000-000000000002')<>40
 or (select count(*) from public.atribuicoes_humanas
  where operador_id='c1020000-0000-4000-8000-000000000002'
    and encerrada_em is null)<>25
 then raise exception 'S1B-02 ativacao nao respeitou teto ou loja';end if;
end $t$;
\echo 'PASS S1B-02: gatilho de ativacao drena apenas 25 de A, B intacta'
do $t$ declare j jsonb;begin
 j:=prumo_private.s1_drenar_backlog_protegido(
  'c2020000-0000-4000-8000-000000000001',1);
 if (j->>'reassigned')::integer<>25 or (j->>'pending_after')::integer<>10
 or (j->>'batches_run')::integer<>1
 then raise exception 'S1B-03 lote incompleto %',j;end if;
end $t$;
\echo 'PASS S1B-03: uma chamada limitada a 25 deixa 10 protegidos'
do $t$ declare j jsonb;begin
 j:=prumo_private.s1_drenar_backlog_protegido(
  'c2020000-0000-4000-8000-000000000001',2);
 if (j->>'reassigned')::integer<>9 or (j->>'terminal_closed')::integer<>1
 or (j->>'pending_after')::integer<>0 or (j->>'outcome')<>'DRAINED'
 then raise exception 'S1B-04 final de A incorreto %',j;end if;
 if exists(select 1 from public.atribuicoes_humanas
  where caso_id='c5020000-0000-4000-8000-000000000060'
  and encerrada_em is null)
 or (select status_comercial from public.ciclos_comerciais
  where id='c4020000-0000-4000-8000-000000000060')<>'vendido'
 then raise exception 'S1B-04 venda reaberta';end if;
end $t$;
\echo 'PASS S1B-04: lote final recupera 9, fecha vendido sem reabrir'
do $t$ declare j jsonb;begin
 j:=prumo_private.s1_drenar_backlog_protegido(
  'c2020000-0000-4000-8000-000000000001',3);
 if (j->>'inspected')::integer<>0
 or (select count(*) from prumo_private.s1_recuperacao_fila_historico
  where concessionaria_id='c2020000-0000-4000-8000-000000000001')<>60
 then raise exception 'S1B-05 rerun duplicado %',j;end if;
end $t$;
\echo 'PASS S1B-05: drenagem idempotente apos completar A'
-- B: primeiro 30 casos excluem o unico operador O3 (operador anterior).
-- Os ultimos 10 sao recuperaveis pelo mesmo O3. Rotacao impede starvation.
do $t$ declare j jsonb;begin
 j:=prumo_private.s1_drenar_backlog_protegido(
  'c2020000-0000-4000-8000-000000000002',2);
 if (j->>'reassigned')::integer<>10
 or (j->>'pending_after')::integer<>30
 or (j->>'blocked_inspections')::integer<30
 or (j->>'blocked_inspections')::integer>50
 then raise exception 'S1B-06 starvation ou fuga de loja %',j;end if;
 if (select count(*) from public.atribuicoes_humanas
  where operador_id='c1020000-0000-4000-8000-000000000003'
   and concessionaria_id='c2020000-0000-4000-8000-000000000002'
   and encerrada_em is null)<>10
 then raise exception 'S1B-06 destino incorreto';end if;
end $t$;
\echo 'PASS S1B-06: rotacao ignora 30 casos bloqueados e recupera os 10 posteriores'
-- O5 ficou pendente; ativacao realocara apenas 25 de B.
update public.equipe_prumo_s1 set estado='ativo'
 where ator_id='c1020000-0000-4000-8000-000000000005';
do $t$ declare j jsonb;begin
 if (select count(*) from prumo_private.s1_remanejamento_pendencias
  where concessionaria_id='c2020000-0000-4000-8000-000000000002')<>5
 then raise exception 'S1B-07 ativacao excedeu 25';end if;
 j:=prumo_private.s1_drenar_backlog_protegido(
  'c2020000-0000-4000-8000-000000000002',1);
 if (j->>'reassigned')::integer<>5 or (j->>'pending_after')::integer<>0
 then raise exception 'S1B-07 lote restante nao concluiu %',j;end if;
 if (select count(*) from public.atribuicoes_humanas
  where caso_id::text like 'c5020000-%' and encerrada_em is null)<>99
 then raise exception 'S1B-07 total de casos recuperados errado';end if;
end $t$;
\echo 'PASS S1B-07: ativacao limita 25 em B e rotina interna drena os cinco restantes'
set local role authenticated;
select set_config('request.jwt.claim.sub','c1020000-0000-4000-8000-000000000002',true);
do $t$ begin
 if (select count(*) from public.casos_humanos)<>59
 or exists(select 1 from public.casos_humanos
  where concessionaria_id='c2020000-0000-4000-8000-000000000002')
 then raise exception 'S1B-08 vazamento de loja';end if;
end $t$;
\echo 'PASS S1B-08: A tem somente seus 59 casos na leitura autenticada'
do $t$ begin
 begin
  perform prumo_private.s1_drenar_backlog_protegido(
   'c2020000-0000-4000-8000-000000000001',1);
  raise exception 'S1B-09 autenticado acionou backend privado';
 exception when insufficient_privilege then null;end;
end $t$;
\echo 'PASS S1B-09: authenticated nao executa drenagem'
reset role;
do $t$ begin
 begin
  perform prumo_private.s1_drenar_backlog_protegido(null,1);
  raise exception 'S1B-10 loja ausente aceita';
 exception when invalid_parameter_value then null;end;
 begin
  perform prumo_private.s1_drenar_backlog_protegido(
   'c2020000-0000-4000-8000-000000000001',11);
  raise exception 'S1B-10 lote acima do limite aceito';
 exception when invalid_parameter_value then null;end;
end $t$;
\echo 'PASS S1B-10: input nao confiavel e limite 10 rejeitados'
rollback;
