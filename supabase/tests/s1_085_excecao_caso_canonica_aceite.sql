\set ON_ERROR_STOP on
-- I61 canonical S0+S1 only: all synthetic rows in rollback.
begin;
insert into auth.users(id)
 select ('86110000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid
 from generate_series(1,4) i;
insert into public.atores(id) select id from auth.users where id::text like '86110000-%';
insert into public.equipe_prumo_s1(ator_id,estado)
 select id,'ativo' from public.atores where id::text like '86110000-%';
insert into prumo_private.s1_gestor_operadores(gestor_id,operador_id)
 values('86110000-0000-4000-8000-000000000001','86110000-0000-4000-8000-000000000002'),
 ('86110000-0000-4000-8000-000000000001','86110000-0000-4000-8000-000000000003');
insert into public.concessionarias(id,nome_operacional)
 values('86120000-0000-4000-8000-000000000001','I61 A'),
 ('86120000-0000-4000-8000-000000000002','I61 B');
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel)
 values('86110000-0000-4000-8000-000000000002',
 '86120000-0000-4000-8000-000000000001','operador');
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado)
 values('86130000-0000-4000-8000-000000000001',
 '86120000-0000-4000-8000-000000000001','+5581886100001'),
 ('86130000-0000-4000-8000-000000000002',
 '86120000-0000-4000-8000-000000000002','+5581886100002');
insert into public.ciclos_comerciais(id,concessionaria_id,lead_id,status_comercial)
 values('86140000-0000-4000-8000-000000000001',
 '86120000-0000-4000-8000-000000000001',
 '86130000-0000-4000-8000-000000000001','em atendimento pelo operador'),
 ('86140000-0000-4000-8000-000000000002',
 '86120000-0000-4000-8000-000000000002',
 '86130000-0000-4000-8000-000000000002','aguardando primeiro disparo');
insert into public.casos_humanos(id,concessionaria_id,lead_id,ciclo_id)
 values('86150000-0000-4000-8000-000000000001',
 '86120000-0000-4000-8000-000000000001',
 '86130000-0000-4000-8000-000000000001',
 '86140000-0000-4000-8000-000000000001'),
 ('86150000-0000-4000-8000-000000000002',
 '86120000-0000-4000-8000-000000000002',
 '86130000-0000-4000-8000-000000000002',
 '86140000-0000-4000-8000-000000000002');
insert into public.atribuicoes_humanas(id,concessionaria_id,caso_id,operador_id)
 values('86160000-0000-4000-8000-000000000001',
 '86120000-0000-4000-8000-000000000001',
 '86150000-0000-4000-8000-000000000001',
 '86110000-0000-4000-8000-000000000002');
do $t$ declare v text;begin
 begin
 insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id)
 values('86120000-0000-4000-8000-000000000002',
 '86150000-0000-4000-8000-000000000002',
 '86110000-0000-4000-8000-000000000003');
 raise exception 'I61 bypassed ordinary S0 guard';
 exception when check_violation then
 get stacked diagnostics v=message_text;
 if v<>'S0_DESTINO_SEM_CONCESSAO_ATIVA' then
  raise exception 'I61 wrong default denial: %',v;end if;end;
end $t$;
\echo 'PASS I61-01: without exact exception default S0 no-grant denial remains'
do $t$ declare j jsonb;begin
 j:=prumo_private.s1_mover_excecao_caso_i61(
 '86110000-0000-4000-8000-000000000004',
 '86120000-0000-4000-8000-000000000001',
 '86150000-0000-4000-8000-000000000001',
 '86160000-0000-4000-8000-000000000001',
 '86110000-0000-4000-8000-000000000003');
 raise exception 'I61 outsider moved case %',j;
 exception when insufficient_privilege then null;end $t$;
\echo 'PASS I61-02: other manager cannot exercise case exception'
select prumo_private.s1_definir_intake(
 '86110000-0000-4000-8000-000000000001',
 '86110000-0000-4000-8000-000000000003',true,1);
do $t$ declare v text;begin
 begin
 perform prumo_private.s1_mover_excecao_caso_i61(
 '86110000-0000-4000-8000-000000000001',
 '86120000-0000-4000-8000-000000000001',
 '86150000-0000-4000-8000-000000000001',
 '86160000-0000-4000-8000-000000000001',
 '86110000-0000-4000-8000-000000000003');
 raise exception 'I61 assigned paused intake';
 exception when check_violation then
 get stacked diagnostics v=message_text;
 if v<>'DESTINO_COM_INTAKE_PAUSADO' then raise exception 'I61 wrong pause %',v;end if;end;
end $t$;
\echo 'PASS I61-03: A2 pause blocks even exceptional assignment'
select prumo_private.s1_definir_intake(
 '86110000-0000-4000-8000-000000000001',
 '86110000-0000-4000-8000-000000000003',false,2);
do $t$ declare j jsonb;begin
 j:=prumo_private.s1_mover_excecao_caso_i61(
 '86110000-0000-4000-8000-000000000001',
 '86120000-0000-4000-8000-000000000001',
 '86150000-0000-4000-8000-000000000001',
 '86160000-0000-4000-8000-000000000001',
 '86110000-0000-4000-8000-000000000003');
 if j->>'outcome'<>'MOVED_CASE_EXCEPTION'
 or (select count(*) from public.atribuicoes_humanas
   where id=(j->>'assignment_id')::uuid and encerrada_em is null
   and operador_id='86110000-0000-4000-8000-000000000003')<>1
 or (select count(*) from prumo_private.s1_excecoes_caso_i61
   where id=(j->>'exception_id')::uuid and revogada_em is null)<>1
 then raise exception 'I61 valid transfer failed %',j;end if;
end $t$;
\echo 'PASS I61-04: S0 canonical assignment now accepts exact case exception only'
do $t$ declare j jsonb;begin
 begin
 perform prumo_private.s1_mover_excecao_caso_i61(
 '86110000-0000-4000-8000-000000000001',
 '86120000-0000-4000-8000-000000000001',
 '86150000-0000-4000-8000-000000000001',
 '86160000-0000-4000-8000-000000000001',
 '86110000-0000-4000-8000-000000000002');
 raise exception 'I61 allowed stale CAS';
 exception when invalid_parameter_value then null;end;
end $t$;
\echo 'PASS I61-05: stale assignment cannot claim a second owner'
do $t$ declare v jsonb;x uuid;begin
 select id into x from prumo_private.s1_excecoes_caso_i61 where revogada_em is null;
 begin
 v:=prumo_private.s1_revogar_excecao_i61(
 '86110000-0000-4000-8000-000000000004',x);
 raise exception 'I61 outsider revoked exception %',v;
 exception when insufficient_privilege then null;end;
 v:=prumo_private.s1_revogar_excecao_i61(
 '86110000-0000-4000-8000-000000000001',x);
 if v->>'outcome'<>'REVOKED_CASE_ACCESS'
 or (select count(*) from prumo_private.s1_excecoes_caso_eventos_i61
 where excecao_id=x and evento='REVOGADA')<>1
 then raise exception 'I61 revocation audit mismatch %',v;end if;
 if prumo_private.s1_prova_excecao_i61(
 '86120000-0000-4000-8000-000000000001',
 '86150000-0000-4000-8000-000000000001',
 (select atribuicao_id from prumo_private.s1_excecoes_caso_i61 where id=x),
 '86110000-0000-4000-8000-000000000003')
 then raise exception 'I61 revoked entitlement still valid';end if;
end $t$;
\echo 'PASS I61-06: only owning manager revokes and authorization stops without moving S0 case'
do $t$ declare v text;begin
 if (select count(*) from prumo_private.s1_excecoes_caso_eventos_i61
  where evento='CRIADA')<>1 then raise exception 'I61 missing create audit';end if;
 if has_table_privilege('authenticated','prumo_private.s1_excecoes_caso_i61','SELECT')
 or has_table_privilege('service_role','prumo_private.s1_excecoes_caso_i61','SELECT')
 or has_function_privilege('authenticated',
  'prumo_private.s1_mover_excecao_caso_i61(uuid,uuid,uuid,uuid,uuid)','EXECUTE')
 or has_function_privilege('authenticated',
  'prumo_private.s1_revogar_excecao_i61(uuid,uuid)','EXECUTE')
 then raise exception 'I61 private ACL leak';end if;
 begin update prumo_private.s1_excecoes_caso_eventos_i61
  set evento='CRIADA' where evento='REVOGADA';
 raise exception 'I61 changed append-only event';
 exception when check_violation then null;end;
end $t$;
\echo 'PASS I61-07: private grants denied, event audit append-only'
rollback;
\echo 'I61 canonical case-exception PG17 7/7; rollback'
