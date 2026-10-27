\set ON_ERROR_STOP on
-- AUD-DORG-S0: Prumo personnel with multiple independent shop grants.
-- Existing S0 policies only; transaction-only fixtures. NO schema migration.
begin;
insert into auth.users(id) values
 ('d1100000-0000-4000-8000-000000000001'), -- Prumo manager A+B
 ('d1100000-0000-4000-8000-000000000002'), -- Prumo operator A+B
 ('d1100000-0000-4000-8000-000000000003'), -- Prumo operator only A
 ('d1100000-0000-4000-8000-000000000004'); -- authenticated but unlinked
insert into public.atores(id)
 select id from auth.users where id::text like 'd1100000-%';
insert into public.concessionarias(id,nome_operacional) values
 ('d1200000-0000-4000-8000-000000000001','DORG concessionaria A ficticia'),
 ('d1200000-0000-4000-8000-000000000002','DORG concessionaria B ficticia'),
 ('d1200000-0000-4000-8000-000000000003','DORG concessionaria C ficticia');
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel) values
 ('d1100000-0000-4000-8000-000000000001','d1200000-0000-4000-8000-000000000001','gestor'),
 ('d1100000-0000-4000-8000-000000000001','d1200000-0000-4000-8000-000000000002','gestor'),
 ('d1100000-0000-4000-8000-000000000002','d1200000-0000-4000-8000-000000000001','operador'),
 ('d1100000-0000-4000-8000-000000000002','d1200000-0000-4000-8000-000000000002','operador'),
 ('d1100000-0000-4000-8000-000000000003','d1200000-0000-4000-8000-000000000001','operador');
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado) values
 ('d1300000-0000-4000-8000-000000000001','d1200000-0000-4000-8000-000000000001','+5581999007777'),
 ('d1300000-0000-4000-8000-000000000002','d1200000-0000-4000-8000-000000000002','+5581999007777'),
 ('d1300000-0000-4000-8000-000000000003','d1200000-0000-4000-8000-000000000003','+5581999007777'),
 ('d1300000-0000-4000-8000-000000000004','d1200000-0000-4000-8000-000000000001','+5581999007778'),
 ('d1300000-0000-4000-8000-000000000005','d1200000-0000-4000-8000-000000000002','+5581999007778');
insert into public.ciclos_comerciais(id,concessionaria_id,lead_id) values
 ('d1400000-0000-4000-8000-000000000001','d1200000-0000-4000-8000-000000000001','d1300000-0000-4000-8000-000000000001'),
 ('d1400000-0000-4000-8000-000000000002','d1200000-0000-4000-8000-000000000002','d1300000-0000-4000-8000-000000000002'),
 ('d1400000-0000-4000-8000-000000000003','d1200000-0000-4000-8000-000000000003','d1300000-0000-4000-8000-000000000003');
insert into public.casos_humanos(id,concessionaria_id,lead_id,ciclo_id) values
 ('d1500000-0000-4000-8000-000000000001','d1200000-0000-4000-8000-000000000001','d1300000-0000-4000-8000-000000000001','d1400000-0000-4000-8000-000000000001'),
 ('d1500000-0000-4000-8000-000000000002','d1200000-0000-4000-8000-000000000002','d1300000-0000-4000-8000-000000000002','d1400000-0000-4000-8000-000000000002'),
 ('d1500000-0000-4000-8000-000000000003','d1200000-0000-4000-8000-000000000003','d1300000-0000-4000-8000-000000000003','d1400000-0000-4000-8000-000000000003');
insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id) values
 ('d1200000-0000-4000-8000-000000000001','d1500000-0000-4000-8000-000000000001','d1100000-0000-4000-8000-000000000002'),
 ('d1200000-0000-4000-8000-000000000002','d1500000-0000-4000-8000-000000000002','d1100000-0000-4000-8000-000000000002');
insert into public.canais_loja(id,concessionaria_id,identificador_emissor) values
 ('d1600000-0000-4000-8000-000000000001','d1200000-0000-4000-8000-000000000001','DORG-CHANNEL-A'),
 ('d1600000-0000-4000-8000-000000000002','d1200000-0000-4000-8000-000000000002','DORG-CHANNEL-B'),
 ('d1600000-0000-4000-8000-000000000003','d1200000-0000-4000-8000-000000000003','DORG-CHANNEL-C');
insert into public.conversas(id,concessionaria_id,lead_id,canal_id,caso_id) values
 ('d1700000-0000-4000-8000-000000000001','d1200000-0000-4000-8000-000000000001','d1300000-0000-4000-8000-000000000001','d1600000-0000-4000-8000-000000000001','d1500000-0000-4000-8000-000000000001'),
 ('d1700000-0000-4000-8000-000000000002','d1200000-0000-4000-8000-000000000002','d1300000-0000-4000-8000-000000000002','d1600000-0000-4000-8000-000000000002','d1500000-0000-4000-8000-000000000002'),
 ('d1700000-0000-4000-8000-000000000003','d1200000-0000-4000-8000-000000000003','d1300000-0000-4000-8000-000000000003','d1600000-0000-4000-8000-000000000003','d1500000-0000-4000-8000-000000000003');
insert into public.mensagens(concessionaria_id,conversa_id,canal_id,caso_id,direcao,conteudo_sintetico,id_externo) values
 ('d1200000-0000-4000-8000-000000000001','d1700000-0000-4000-8000-000000000001','d1600000-0000-4000-8000-000000000001','d1500000-0000-4000-8000-000000000001','entrada','DORG mensagem ficticia A','DORG-A'),
 ('d1200000-0000-4000-8000-000000000002','d1700000-0000-4000-8000-000000000002','d1600000-0000-4000-8000-000000000002','d1500000-0000-4000-8000-000000000002','entrada','DORG mensagem ficticia B','DORG-B'),
 ('d1200000-0000-4000-8000-000000000003','d1700000-0000-4000-8000-000000000003','d1600000-0000-4000-8000-000000000003','d1500000-0000-4000-8000-000000000003','entrada','DORG mensagem ficticia C','DORG-C');

do $audit$
begin
 if (select count(*) from public.atores where id::text like 'd1100000-%')<>4
 or (select count(*) from public.vinculos_papel_escopo
       where ator_id='d1100000-0000-4000-8000-000000000001')<>2
 or (select count(*) from public.vinculos_papel_escopo
       where ator_id='d1100000-0000-4000-8000-000000000002')<>2
 then raise exception 'FAIL DORG-S0-01 identities cannot have N shop concessions';end if;
 -- Prevent a Prumo operator with only A from receiving a B case.
 begin
  insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id)
  values('d1200000-0000-4000-8000-000000000003','d1500000-0000-4000-8000-000000000003','d1100000-0000-4000-8000-000000000003');
  raise exception 'FAIL DORG-S0-01 operator got non-granted C';
 exception when check_violation then null;end;
end $audit$;
\echo 'PASS DORG-S0-01: one Prumo identity N concessionaria grants, assignment scoped'

set local role authenticated;
select set_config('request.jwt.claim.sub','d1100000-0000-4000-8000-000000000001',true);
do $audit$
begin
 if (select count(*) from public.concessionarias)<>2
 or (select count(*) from public.leads_loja)<>4
 or (select count(*) from public.conversas)<>2
 or (select count(*) from public.mensagens)<>2
 or (select count(*) from public.ciclos_comerciais)<>2
 then raise exception 'FAIL DORG-S0-02 manager A+B cannot see expected data';end if;
 if exists(select 1 from public.concessionarias where id='d1200000-0000-4000-8000-000000000003')
 then raise exception 'FAIL DORG-S0-02 manager A+B saw C';end if;
end $audit$;
\echo 'PASS DORG-S0-02: manager Prumo A+B sees D2 of both, not ungranted C'

select set_config('request.jwt.claim.sub','d1100000-0000-4000-8000-000000000002',true);
do $audit$
begin
 if (select count(*) from public.leads_loja)<>2
 or (select count(*) from public.casos_humanos)<>2
 or (select count(*) from public.conversas)<>2
 or (select count(*) from public.mensagens)<>2
 then raise exception 'FAIL DORG-S0-03 operator A+B must see only two assigned cases';end if;
 if exists(select 1 from public.leads_loja where id in(
 'd1300000-0000-4000-8000-000000000004',
 'd1300000-0000-4000-8000-000000000005',
 'd1300000-0000-4000-8000-000000000003'))
 then raise exception 'FAIL DORG-S0-03 operator sees unassigned/C leads';end if;
end $audit$;
select set_config('request.jwt.claim.sub','d1100000-0000-4000-8000-000000000003',true);
do $audit$
begin
 if (select count(*) from public.casos_humanos)<>0
 or (select count(*) from public.leads_loja)<>0
 then raise exception 'FAIL DORG-S0-03 single-shop operator without case sees other cases';end if;
end $audit$;
\echo 'PASS DORG-S0-03: multi-shop operator reads only assigned cases; exclusive operator none'

reset role;
-- The manager may self-assign case A; the former operator loses it.
update public.atribuicoes_humanas set encerrada_em=statement_timestamp()
 where concessionaria_id='d1200000-0000-4000-8000-000000000001'
 and caso_id='d1500000-0000-4000-8000-000000000001' and encerrada_em is null;
insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id) values
 ('d1200000-0000-4000-8000-000000000001','d1500000-0000-4000-8000-000000000001','d1100000-0000-4000-8000-000000000001');
set local role authenticated;
select set_config('request.jwt.claim.sub','d1100000-0000-4000-8000-000000000001',true);
insert into public.mensagens(concessionaria_id,conversa_id,canal_id,caso_id,direcao,origem,conteudo_sintetico,enviada_por)
 values('d1200000-0000-4000-8000-000000000001','d1700000-0000-4000-8000-000000000001',
 'd1600000-0000-4000-8000-000000000001','d1500000-0000-4000-8000-000000000001',
 'saida','simulado','DORG gestor Prumo autoatribuido','d1100000-0000-4000-8000-000000000001');
select set_config('request.jwt.claim.sub','d1100000-0000-4000-8000-000000000002',true);
do $audit$
begin
 if (select count(*) from public.leads_loja)<>1
 or (select count(*) from public.conversas)<>1
 or (select count(*) from public.mensagens)<>1
 then raise exception 'FAIL DORG-S0-04 removed operator still reads A';end if;
end $audit$;
\echo 'PASS DORG-S0-04: manager self-assignment and case transfer revoke operator A'

reset role;
-- Revocation B must not erase Prumo identity, grant A, or other actor's grants.
update public.vinculos_papel_escopo set valido_ate=statement_timestamp()
 where concessionaria_id='d1200000-0000-4000-8000-000000000002'
  and ator_id in('d1100000-0000-4000-8000-000000000001',
                 'd1100000-0000-4000-8000-000000000002');
set local role authenticated;
select set_config('request.jwt.claim.sub','d1100000-0000-4000-8000-000000000001',true);
do $audit$
begin
 if (select count(*) from public.concessionarias)<>1
 or (select count(*) from public.leads_loja)<>2
 or (select count(*) from public.casos_humanos)<>1
 or (select count(*) from public.mensagens)<>2
 then raise exception 'FAIL DORG-S0-05 manager lost A or kept B after grant revocation';end if;
end $audit$;
select set_config('request.jwt.claim.sub','d1100000-0000-4000-8000-000000000002',true);
do $audit$
begin
 if (select count(*) from public.casos_humanos)<>0
 or (select count(*) from public.leads_loja)<>0
 or (select count(*) from public.conversas)<>0
 or (select count(*) from public.mensagens)<>0
 then raise exception 'FAIL DORG-S0-05 operator retained B without concession';end if;
end $audit$;
reset role;
do $audit$
begin
 if (select count(*) from public.atores where id::text like 'd1100000-%')<>4
 or (select count(*) from public.atribuicoes_humanas where concessionaria_id='d1200000-0000-4000-8000-000000000002'
   and encerrada_em is null)<>1
 then raise exception 'FAIL DORG-S0-05 revocation deleted actor or assignment history';end if;
end $audit$;
\echo 'PASS DORG-S0-05: B grant revoked independently; A and identities preserved'

set local role authenticated;
select set_config('request.jwt.claim.sub','d1100000-0000-4000-8000-000000000004',true);
do $audit$
begin
 if (select count(*) from public.leads_loja)<>0
 or (select count(*) from public.casos_humanos)<>0
 then raise exception 'FAIL DORG-S0-06 unrelated authenticated identity saw tenant data';end if;
 begin
  insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel)
  values('d1100000-0000-4000-8000-000000000004',
         'd1200000-0000-4000-8000-000000000003','gestor');
  raise exception 'FAIL DORG-S0-06 user self-granted scope';
 exception when insufficient_privilege then null;end;
end $audit$;
\echo 'PASS DORG-S0-06: unlinked JWT denied; cannot self-grant shop access'
reset role;
rollback;
