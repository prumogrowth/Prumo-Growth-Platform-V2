\set ON_ERROR_STOP on
-- I58: six checks on canonical S0 tables, entirely synthetic and rolled back.
begin;
insert into auth.users(id)
 select ('79010000-0000-4000-8000-'||pg_catalog.lpad(i::text,12,'0'))::uuid
 from pg_catalog.generate_series(1,3) i;
insert into public.atores(id) select id from auth.users where id::text like '79010000-%';
insert into public.equipe_prumo_s1(ator_id,estado)
 select id,'ativo' from public.atores where id::text like '79010000-%';
insert into public.concessionarias(id,nome_operacional)
 values('79020000-0000-4000-8000-000000000001','I58 store A'),
       ('79020000-0000-4000-8000-000000000002','I58 store B');
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel)
 values('79010000-0000-4000-8000-000000000001','79020000-0000-4000-8000-000000000001','gestor'),
       ('79010000-0000-4000-8000-000000000002','79020000-0000-4000-8000-000000000002','gestor'),
       ('79010000-0000-4000-8000-000000000003','79020000-0000-4000-8000-000000000001','operador');
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado)
 values('79030000-0000-4000-8000-000000000001','79020000-0000-4000-8000-000000000001','+5581995800001'),
       ('79030000-0000-4000-8000-000000000002','79020000-0000-4000-8000-000000000001','+5581995800002');
insert into public.ciclos_comerciais(id,concessionaria_id,lead_id,status_comercial)
 values('79040000-0000-4000-8000-000000000001','79020000-0000-4000-8000-000000000001','79030000-0000-4000-8000-000000000001','em atendimento pelo operador'),
       ('79040000-0000-4000-8000-000000000002','79020000-0000-4000-8000-000000000001','79030000-0000-4000-8000-000000000002','em atendimento pelo operador');
do $t$ declare x jsonb;begin
 perform prumo_private.s0_fila_exigir_gestor_i58(
 '79010000-0000-4000-8000-000000000001',
 '79020000-0000-4000-8000-000000000001');
 x:=prumo_private.s0_fila_assumir(
 '79010000-0000-4000-8000-000000000001',
 '79020000-0000-4000-8000-000000000001',
 '79040000-0000-4000-8000-000000000001',1);
 if x->>'outcome'<>'CLAIMED_BY_MANAGER' then
  raise exception 'I58 authorized claim failed %',x;end if;
end $t$;
\echo 'PASS I58-01: authorized manager sees shared LIST gate and wins exact S0 CAS'
do $t$ declare x jsonb;begin
 x:=prumo_private.s0_fila_assumir(
 '79010000-0000-4000-8000-000000000001',
 '79020000-0000-4000-8000-000000000001',
 '79040000-0000-4000-8000-000000000001',1);
 if x->>'outcome'<>'CONFLICT' then
 raise exception 'I58 authorized replay unexpected %',x;end if;
end $t$;
\echo 'PASS I58-02: authorized stale CAS remains conflict without duplicate'
update public.vinculos_papel_escopo set valido_ate=pg_catalog.clock_timestamp()
 where ator_id='79010000-0000-4000-8000-000000000001' and papel='gestor';
do $t$ declare err text;begin
 begin
  perform prumo_private.s0_fila_assumir(
   '79010000-0000-4000-8000-000000000001',
   '79020000-0000-4000-8000-000000000001',
   '79040000-0000-4000-8000-000000000001',1);
  raise exception 'I58 revoked manager received stale queue signal';
 exception when insufficient_privilege then
  get stacked diagnostics err=message_text;
  if err<>'S0_FILA_GESTOR_SEM_LOJA' then
  raise exception 'I58 unexpected denial %',err;end if;
 end;
end $t$;
\echo 'PASS I58-03: revoked grant denied BEFORE stale CAS and no tenant metadata leaked'
do $t$ declare err text;begin
 begin
 perform prumo_private.s0_fila_exigir_gestor_i58(
 '79010000-0000-4000-8000-000000000002',
 '79020000-0000-4000-8000-000000000001');
 raise exception 'I58 cross-store manager read queue';
 exception when insufficient_privilege then
 get stacked diagnostics err=message_text;
 if err<>'S0_FILA_GESTOR_SEM_LOJA' then
 raise exception 'I58 unexpected cross-store denial %',err;end if;end;
end $t$;
\echo 'PASS I58-04: cross-store manager fails signed LIST predicate'
update public.equipe_prumo_s1 set estado='suspenso'
 where ator_id='79010000-0000-4000-8000-000000000002';
do $t$ declare err text;begin
 begin
 perform prumo_private.s0_fila_exigir_gestor_i58(
 '79010000-0000-4000-8000-000000000002',
 '79020000-0000-4000-8000-000000000002');
 raise exception 'I58 suspended manager allowed';
 exception when insufficient_privilege then
 get stacked diagnostics err=message_text;
 if err<>'S0_FILA_GESTOR_SEM_LOJA' then
 raise exception 'I58 unexpected suspended denial %',err;end if;end;
end $t$;
\echo 'PASS I58-05: manager account suspension denies LIST even with store grant'
do $t$ begin
 if (select count(*) from public.casos_humanos
 where ciclo_id='79040000-0000-4000-8000-000000000002')<>0
 or (select count(*) from prumo_private.s0_fila_humana
 where ciclo_id='79040000-0000-4000-8000-000000000002'
 and estado='pendente' and versao=1)<>1
 or has_function_privilege('authenticated',
  'prumo_private.s0_fila_exigir_gestor_i58(uuid,uuid)','EXECUTE')
 or has_function_privilege('service_role',
  'prumo_private.s0_fila_exigir_gestor_i58(uuid,uuid)','EXECUTE')
 then raise exception 'I58 pending queue mutated or helper exposed';end if;
end $t$;
\echo 'PASS I58-06: denied operations preserve pending queue, ACL remains private'
rollback;
\echo 'I58 PG17 six tests PASS (rollback)'
