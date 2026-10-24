\set ON_ERROR_STOP on
-- I59 FK proof: all fictional data, one PG17 transaction rolled back.
begin;
insert into public.concessionarias(id,nome_operacional)
 values('79120000-0000-4000-8000-000000000001','I59 loja A'),
 ('79120000-0000-4000-8000-000000000002','I59 loja B');
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado)
 values('79130000-0000-4000-8000-000000000001','79120000-0000-4000-8000-000000000001','+5581885910001'),
 ('79130000-0000-4000-8000-000000000002','79120000-0000-4000-8000-000000000001','+5581885910002'),
 ('79130000-0000-4000-8000-000000000003','79120000-0000-4000-8000-000000000002','+5581885910001');
insert into public.ciclos_comerciais(id,concessionaria_id,lead_id,status_comercial)
 values('79140000-0000-4000-8000-000000000001','79120000-0000-4000-8000-000000000001','79130000-0000-4000-8000-000000000001','aguardando primeiro disparo'),
 ('79140000-0000-4000-8000-000000000002','79120000-0000-4000-8000-000000000001','79130000-0000-4000-8000-000000000002','aguardando primeiro disparo'),
 ('79140000-0000-4000-8000-000000000003','79120000-0000-4000-8000-000000000002','79130000-0000-4000-8000-000000000003','aguardando primeiro disparo');
insert into public.casos_humanos(id,concessionaria_id,lead_id,ciclo_id)
 values('79150000-0000-4000-8000-000000000001','79120000-0000-4000-8000-000000000001','79130000-0000-4000-8000-000000000001','79140000-0000-4000-8000-000000000001'),
 ('79150000-0000-4000-8000-000000000002','79120000-0000-4000-8000-000000000001','79130000-0000-4000-8000-000000000002','79140000-0000-4000-8000-000000000002'),
 ('79150000-0000-4000-8000-000000000003','79120000-0000-4000-8000-000000000002','79130000-0000-4000-8000-000000000003','79140000-0000-4000-8000-000000000003');
insert into public.canais_loja(id,concessionaria_id,identificador_emissor)
 values('79160000-0000-4000-8000-000000000001','79120000-0000-4000-8000-000000000001','i59-a'),
 ('79160000-0000-4000-8000-000000000002','79120000-0000-4000-8000-000000000002','i59-b');
insert into public.conversas(id,concessionaria_id,lead_id,canal_id,caso_id)
 values('79170000-0000-4000-8000-000000000001',
 '79120000-0000-4000-8000-000000000001','79130000-0000-4000-8000-000000000001',
 '79160000-0000-4000-8000-000000000001','79150000-0000-4000-8000-000000000001');
\echo 'PASS I59-01: legitimate conversation binds exact shop/case/contact'
do $t$ begin
 begin
  insert into public.conversas(concessionaria_id,lead_id,canal_id,caso_id)
  values('79120000-0000-4000-8000-000000000001',
   '79130000-0000-4000-8000-000000000002',
   '79160000-0000-4000-8000-000000000001',
   '79150000-0000-4000-8000-000000000001');
  raise exception 'I59 cross-contact case link inserted';
 exception when foreign_key_violation then null;end;
end $t$;
\echo 'PASS I59-02: same-store different-contact case association is rejected'
do $t$ begin
 begin
  update public.conversas set lead_id='79130000-0000-4000-8000-000000000002'
   where id='79170000-0000-4000-8000-000000000001';
  raise exception 'I59 switched contact of authorized conversation';
 exception when foreign_key_violation then null;end;
end $t$;
\echo 'PASS I59-03: changing contact of existing case conversation fails closed'
do $t$ begin
 begin
  update public.conversas set caso_id='79150000-0000-4000-8000-000000000002'
   where id='79170000-0000-4000-8000-000000000001';
  raise exception 'I59 retargeted conversation to different case contact';
 exception when foreign_key_violation then null;end;
end $t$;
\echo 'PASS I59-04: redirecting existing conversation to another contact case fails'
insert into public.conversas(id,concessionaria_id,lead_id,canal_id,caso_id)
 values('79170000-0000-4000-8000-000000000002',
 '79120000-0000-4000-8000-000000000001',
 '79130000-0000-4000-8000-000000000002',
 '79160000-0000-4000-8000-000000000001',null);
do $t$ begin
 if (select count(*) from public.conversas
 where id='79170000-0000-4000-8000-000000000002' and caso_id is null)<>1
 then raise exception 'I59 unassigned conversation blocked';end if;
end $t$;
\echo 'PASS I59-05: case-less S0 conversation remains valid before human handoff'
do $t$ begin
 begin
  insert into public.conversas(concessionaria_id,lead_id,canal_id,caso_id)
   values('79120000-0000-4000-8000-000000000002',
    '79130000-0000-4000-8000-000000000003',
    '79160000-0000-4000-8000-000000000002',
    '79150000-0000-4000-8000-000000000001');
  raise exception 'I59 foreign-store case inserted';
 exception when foreign_key_violation then null;end;
end $t$;
\echo 'PASS I59-06: same telephone in another store never attaches foreign case'
do $t$ declare n int;begin
 select count(*) into n from pg_catalog.pg_constraint
 where conname='s0_conversa_caso_lead_i59'
 and conrelid='public.conversas'::regclass and confrelid='public.casos_humanos'::regclass
 and contype='f' and convalidated;
 if n<>1 then raise exception 'I59 key not validated in canonical S0';end if;
 if (select count(*) from public.conversas
 where id='79170000-0000-4000-8000-000000000001'
 and caso_id='79150000-0000-4000-8000-000000000001'
 and lead_id='79130000-0000-4000-8000-000000000001')<>1
 then raise exception 'I59 forbidden mutation took effect';end if;
end $t$;
\echo 'PASS I59-07: validated canonical FK; denied writes leave original conversation intact'
rollback;
\echo 'I59 PG17 canonical conversation/case/contact integrity 7/7 (rollback)'
