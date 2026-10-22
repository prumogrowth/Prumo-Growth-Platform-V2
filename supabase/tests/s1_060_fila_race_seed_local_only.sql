\set ON_ERROR_STOP on
-- S1-002/I40: setup COMMITADO exclusivamente em banco PG17 descartavel.
-- Usa as MESMAS funcoes I39; testes em sessoes separadas exigem COMMIT.
-- O script bash testa host 127.0.0.1/localhost e base prumo_s0_test_*.
begin;
\ir s1_059_proto_fila_novos_setup_local_only.sql
insert into auth.users(id)
 select ('60110000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid
 from generate_series(1,4) i;
insert into public.atores(id)
 select id from auth.users where id::text like '60110000-%';
insert into public.equipe_prumo_s1(ator_id,estado)
 select id,'ativo' from public.atores where id::text like '60110000-%';
-- Gestores 1 e 2 autorizados na MESMA loja, 3 sem grant.
insert into prumo_private.s1_gestor_operadores(gestor_id,operador_id)
 values('60110000-0000-4000-8000-000000000001',
        '60110000-0000-4000-8000-000000000004');
insert into public.concessionarias(id,nome_operacional)
 values('60220000-0000-4000-8000-000000000001',
        'S1 I40 loja ficticia de teste');
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel)
 values
 ('60110000-0000-4000-8000-000000000001','60220000-0000-4000-8000-000000000001','gestor'),
 ('60110000-0000-4000-8000-000000000002','60220000-0000-4000-8000-000000000001','gestor'),
 ('60110000-0000-4000-8000-000000000004','60220000-0000-4000-8000-000000000001','operador');
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado)
 select ('60330000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 '60220000-0000-4000-8000-000000000001',
 '+5581886600'||lpad(i::text,4,'0')
 from generate_series(1,3) i;
insert into public.ciclos_comerciais(id,concessionaria_id,lead_id,status_comercial)
 select ('60440000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 '60220000-0000-4000-8000-000000000001',
 ('60330000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 'em atendimento pelo operador'
 from generate_series(1,3) i;
insert into public.casos_humanos(id,concessionaria_id,lead_id,ciclo_id)
 select ('60550000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 '60220000-0000-4000-8000-000000000001',
 ('60330000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 ('60440000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid
 from generate_series(1,3) i;
-- Um unico Consultor, intake pausado sem conta suspensa.
select prumo_private.s1_definir_disponibilidade_leads_10(
 '60110000-0000-4000-8000-000000000001',
 '60110000-0000-4000-8000-000000000004',true,1);
do $check$
declare i int; j jsonb;
begin
 for i in 1..3 loop
  j:=prumo_private.s1_59_tentar_novo(
  '60220000-0000-4000-8000-000000000001',
  ('60550000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid);
  if j->>'outcome'<>'QUEUED_UNOWNED' then
   raise exception 'I40-SETUP not queued % %',i,j;end if;
 end loop;
 if (select count(*) from public.s1_fila_novos_59
     where estado='PENDENTE')<>3
 or (select count(*) from public.atribuicoes_humanas a
     where a.caso_id::text like '60550000-%')<>0
 or (select estado from public.equipe_prumo_s1
     where ator_id='60110000-0000-4000-8000-000000000004')<>'ativo'
 then raise exception 'I40-SETUP divergencia de fila/intake';end if;
end $check$;
commit;
\echo 'PASS I40-SETUP: 3 casos S0 sem titular e fila compartilhada; funcoes I39 instaladas somente no sandbox'
