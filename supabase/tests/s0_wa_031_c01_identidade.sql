\set ON_ERROR_STOP on
begin;
insert into auth.users(id) values
 ('c3110000-0000-4000-8000-000000000001'),
 ('c3110000-0000-4000-8000-000000000002');
insert into public.atores(id)
 select id from auth.users where id in
 ('c3110000-0000-4000-8000-000000000001','c3110000-0000-4000-8000-000000000002');
insert into public.concessionarias(id,nome_operacional) values
 ('c3120000-0000-4000-8000-000000000001','C01 031 A ficticia'),
 ('c3120000-0000-4000-8000-000000000002','C01 031 B ficticia');
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel) values
 ('c3110000-0000-4000-8000-000000000001','c3120000-0000-4000-8000-000000000001','gestor'),
 ('c3110000-0000-4000-8000-000000000002','c3120000-0000-4000-8000-000000000002','gestor');
insert into public.canais_loja(id,concessionaria_id,identificador_emissor) values
 ('c3130000-0000-4000-8000-000000000001','c3120000-0000-4000-8000-000000000001','C01_031_A_SIM'),
 ('c3130000-0000-4000-8000-000000000002','c3120000-0000-4000-8000-000000000002','C01_031_B_SIM');

do $test$
declare v_rows jsonb;v_a jsonb;v_replay jsonb;v_b jsonb;
begin
 v_rows:='[
 {"telefone":"+5581900001111","mobile_confirmado_sintetico":true},
 {"telefone":"+558100001111","mobile_confirmado_sintetico":true},
 {"telefone":"+558177776666","mobile_confirmado_sintetico":true},
 {"telefone":"BAD","mobile_confirmado_sintetico":false},
 {"telefone":"+558155556666","mobile_confirmado_sintetico":"yes"}
 ]'::jsonb;
 v_a:=prumo_private.importar_lote_identidade_s0(
 'c3110000-0000-4000-8000-000000000001',
 'c3120000-0000-4000-8000-000000000001','WA31-LOT-1',v_rows);
 v_replay:=prumo_private.importar_lote_identidade_s0(
 'c3110000-0000-4000-8000-000000000001',
 'c3120000-0000-4000-8000-000000000001','WA31-LOT-1',v_rows);
 v_b:=prumo_private.importar_lote_identidade_s0(
 'c3110000-0000-4000-8000-000000000002',
 'c3120000-0000-4000-8000-000000000002','WA31-LOT-1',
 '[{"telefone":"+558100001111","mobile_confirmado_sintetico":true}]'::jsonb);
 if v_a->>'outcome'<>'APPLIED'
 or (v_a->>'aceitos')::int<>3 or (v_a->>'rejeitados')::int<>2
 or (v_a->>'em_revisao')::int<>0
 or v_replay->>'outcome'<>'ALREADY_APPLIED'
 or v_replay->>'lote_id'<>v_a->>'lote_id'
 or v_b->>'outcome'<>'APPLIED'
 then raise exception 'FAIL WA31-01: lote/replay/lojas';end if;
 if (select count(*) from public.leads_loja
   where concessionaria_id='c3120000-0000-4000-8000-000000000001')<>2
 or (select count(*) from public.ciclos_comerciais
   where concessionaria_id='c3120000-0000-4000-8000-000000000001')<>2
 or (select count(*) from public.reencontros_lote
   where concessionaria_id='c3120000-0000-4000-8000-000000000001')<>1
 or (select count(*) from prumo_private.aliases_identidade_s0
   where concessionaria_id='c3120000-0000-4000-8000-000000000001')<>3
 or (select count(*) from public.leads_loja
   where concessionaria_id='c3120000-0000-4000-8000-000000000002')<>1
 or (select count(*) from public.itens_lote where
   concessionaria_id='c3120000-0000-4000-8000-000000000001'
   and resultado='rejeitado')<>2
 then raise exception 'FAIL WA31-01: cardinalidade comercial';end if;
 begin
  perform prumo_private.importar_lote_identidade_s0(
   'c3110000-0000-4000-8000-000000000001',
   'c3120000-0000-4000-8000-000000000001','WA31-LOT-1',
   '[{"telefone":"+5581900001112","mobile_confirmado_sintetico":true}]'::jsonb);
  raise exception 'FAIL WA31-01: changed payload same key';
 exception when unique_violation then null;end;
 begin
  perform prumo_private.importar_lote_sintetico(
   'c3110000-0000-4000-8000-000000000001',
   'c3120000-0000-4000-8000-000000000001','WA31-LOT-1',v_rows);
  raise exception 'FAIL WA31-01: legacy call treated new hash as same operation';
 exception when unique_violation then null;end;
end $test$;
\echo 'PASS WA31-01: C01 com alias por loja, replay isolado do legado e itens rejeitados'

do $test$
declare v_inbound jsonb;v_lead uuid;
begin
 select id into v_lead from public.leads_loja
 where concessionaria_id='c3120000-0000-4000-8000-000000000001'
 and telefone_cliente_normalizado='+558177776666';
 v_inbound:=prumo_private.receber_mensagem_identidade_s0(
 'c3130000-0000-4000-8000-000000000001',
 '+5581977776666','WA31-C02-1','C02 apos C01 com 9',true);
 if v_inbound->>'outcome'<>'APPLIED'
 or (select count(*) from public.leads_loja
     where concessionaria_id='c3120000-0000-4000-8000-000000000001')<>2
 or (select count(*) from public.ciclos_comerciais
     where concessionaria_id='c3120000-0000-4000-8000-000000000001')<>2
 or (select count(*) from prumo_private.aliases_identidade_s0 a
  where a.concessionaria_id='c3120000-0000-4000-8000-000000000001'
  and a.lead_id=v_lead and a.numero_sintetico in (
     '+558177776666','+5581977776666'))<>2
 then raise exception 'FAIL WA31-02: C01-C02 reused lead';end if;
end $test$;
\echo 'PASS WA31-02: inbound C02 usa lead importado C01 pela variante 8/9'

do $test$
declare v_r jsonb;v_conflict jsonb;
begin
 perform prumo_private.importar_lote_sintetico(
 'c3110000-0000-4000-8000-000000000001',
 'c3120000-0000-4000-8000-000000000001','WA31-LEGACY-1',
 '[{"telefone":"+558122223333"}]'::jsonb);
 v_r:=prumo_private.importar_lote_identidade_s0(
 'c3110000-0000-4000-8000-000000000001',
 'c3120000-0000-4000-8000-000000000001','WA31-REVIEW-1',
 '[{"telefone":"+5581922223333","mobile_confirmado_sintetico":true}]'::jsonb);
 if (v_r->>'em_revisao')::int<>1
 or (v_r->>'rejeitados')::int<>1
 or (select motivo_rejeicao from public.itens_lote
    where lote_id=(v_r->>'lote_id')::uuid)<>'IDENTIDADE_EM_REVISAO'
 or exists(select 1 from public.leads_loja
   where concessionaria_id='c3120000-0000-4000-8000-000000000001'
   and telefone_cliente_normalizado='+5581922223333')
 then raise exception 'FAIL WA31-03: legacy contact merged without proof';end if;
 insert into public.leads_loja(concessionaria_id,telefone_cliente_normalizado) values
 ('c3120000-0000-4000-8000-000000000001','+5581988884444'),
 ('c3120000-0000-4000-8000-000000000001','+558188884444');
 v_conflict:=prumo_private.importar_lote_identidade_s0(
 'c3110000-0000-4000-8000-000000000001',
 'c3120000-0000-4000-8000-000000000001','WA31-CONFLICT-1',
 '[{"telefone":"+5581988884444","mobile_confirmado_sintetico":true}]'::jsonb);
 if (v_conflict->>'em_revisao')::int<>1
 or (select motivo_rejeicao from public.itens_lote
  where lote_id=(v_conflict->>'lote_id')::uuid)<>'IDENTIDADE_CONFLITANTE'
 then raise exception 'FAIL WA31-03: two leads silently fused';end if;
end $test$;
\echo 'PASS WA31-03: legado sem prova e colisao entre dois leads ficam rejeitados no lote'

do $test$
declare v_r jsonb;
begin
 begin
  perform prumo_private.importar_lote_identidade_s0(
 'c3110000-0000-4000-8000-000000000002',
 'c3120000-0000-4000-8000-000000000001','WA31-WRONG-SCOPE',
 '[{"telefone":"+5581901234567","mobile_confirmado_sintetico":true}]'::jsonb);
  raise exception 'FAIL WA31-04: gestor B importou A';
 exception when insufficient_privilege then null;end;
 v_r:=prumo_private.importar_lote_identidade_s0(
 'c3110000-0000-4000-8000-000000000001',
 'c3120000-0000-4000-8000-000000000001','WA31-INELIGIBLE',
 '[{"telefone":"+55119012345678","mobile_confirmado_sintetico":true}]'::jsonb);
 if (v_r->>'rejeitados')::int<>1
 or (select motivo_rejeicao from public.itens_lote
  where lote_id=(v_r->>'lote_id')::uuid)<>'MOVEL_FIXTURE_NAO_ELEGIVEL'
 then raise exception 'FAIL WA31-04: bad mobile evidence';end if;
 if has_function_privilege('authenticated',
   'prumo_private.importar_lote_identidade_s0(uuid,uuid,text,jsonb)','EXECUTE')
 or has_function_privilege('service_role',
   'prumo_private.importar_lote_identidade_s0(uuid,uuid,text,jsonb)','EXECUTE')
 or has_function_privilege('prumo_s0_gateway',
   'prumo_private.importar_lote_identidade_s0(uuid,uuid,text,jsonb)','EXECUTE')
 then raise exception 'FAIL WA31-04: API access';end if;
end $test$;
\echo 'PASS WA31-04: gestor restrito, telefone inelegivel e nenhuma API exposta'
rollback;
