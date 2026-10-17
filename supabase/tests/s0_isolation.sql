\set ON_ERROR_STOP on
begin;
insert into auth.users(id) values
 ('10000000-0000-4000-8000-000000000001'),
 ('10000000-0000-4000-8000-000000000002'),
 ('10000000-0000-4000-8000-000000000003'),
 ('10000000-0000-4000-8000-000000000004');
insert into public.atores(id) select id from auth.users;
insert into public.concessionarias(id,nome_operacional) values
 ('20000000-0000-4000-8000-000000000001','Loja A sintética'),
 ('20000000-0000-4000-8000-000000000002','Loja B sintética');
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel) values
 ('10000000-0000-4000-8000-000000000001','20000000-0000-4000-8000-000000000001','gestor'),
 ('10000000-0000-4000-8000-000000000002','20000000-0000-4000-8000-000000000002','gestor'),
 ('10000000-0000-4000-8000-000000000003','20000000-0000-4000-8000-000000000001','operador');
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado) values
 ('30000000-0000-4000-8000-000000000001','20000000-0000-4000-8000-000000000001','+5500000000000'),
 ('30000000-0000-4000-8000-000000000002','20000000-0000-4000-8000-000000000002','+5500000000001');
insert into public.ciclos_comerciais(concessionaria_id,lead_id) values
 ('20000000-0000-4000-8000-000000000001','30000000-0000-4000-8000-000000000001'),
 ('20000000-0000-4000-8000-000000000002','30000000-0000-4000-8000-000000000002');
do $$ begin
 if (select count(*) from public.leads_loja)<>2 then raise exception 'dois telefones distintos: FAIL'; end if;
 begin
 insert into public.leads_loja(concessionaria_id,telefone_cliente_normalizado)
 values('20000000-0000-4000-8000-000000000002','+5500000000000');
 raise exception 'telefone repetido entre lojas: FAIL';
 exception when unique_violation then null; end;
 begin
 insert into public.ciclos_comerciais(concessionaria_id,lead_id) values
  ('20000000-0000-4000-8000-000000000001','30000000-0000-4000-8000-000000000002');
 raise exception 'cross-tenant FK: FAIL';
 exception when foreign_key_violation then null; end;
 begin
 insert into public.ciclos_comerciais(concessionaria_id,lead_id,status_comercial) values
  ('20000000-0000-4000-8000-000000000001','30000000-0000-4000-8000-000000000001','ganho');
 raise exception 'ninth status: FAIL';
 exception when check_violation then null; end;
end $$;
\echo 'PASS: exclusividade global de telefone, isolamento FK e oito status'
set local role authenticated;
select set_config('request.jwt.claim.sub','10000000-0000-4000-8000-000000000001',true);
do $$ begin
 if (select count(*) from public.leads_loja)<>1 or (select count(*) from public.ciclos_comerciais)<>1
 or (select count(*) from public.leads_loja where concessionaria_id='20000000-0000-4000-8000-000000000002')<>0
 then raise exception 'gestor A isolation: FAIL'; end if;
end $$;
\echo 'PASS: gestor A vê só A'
select set_config('request.jwt.claim.sub','10000000-0000-4000-8000-000000000002',true);
do $$ begin
 if (select count(*) from public.leads_loja)<>1 or (select count(*) from public.ciclos_comerciais)<>1
 or (select count(*) from public.leads_loja where concessionaria_id='20000000-0000-4000-8000-000000000001')<>0
 then raise exception 'gestor B isolation: FAIL'; end if;
end $$;
\echo 'PASS: gestor B vê só B'
select set_config('request.jwt.claim.sub','10000000-0000-4000-8000-000000000003',true);
do $$ begin
 if (select count(*) from public.leads_loja)<>0 then raise exception 'OP without case: FAIL'; end if;
end $$;
\echo 'PASS: OP sem caso não recebe SELECT'
select set_config('request.jwt.claim.sub','10000000-0000-4000-8000-000000000004',true);
do $$ begin
 if (select count(*) from public.leads_loja)<>0 then raise exception 'unlinked actor: FAIL'; end if;
 begin
 update public.ciclos_comerciais set status_comercial='vendido';
 raise exception 'authenticated wrote status: FAIL';
 exception when insufficient_privilege then null; end;
end $$;
\echo 'PASS: sem vínculo e sem escrita'
reset role;
set local role anon;
do $$ begin
 begin
 perform count(*) from public.leads_loja;
 raise exception 'anon access: FAIL';
 exception when insufficient_privilege then null; end;
end $$;
\echo 'PASS: anon sem SELECT'
reset role;
rollback;
