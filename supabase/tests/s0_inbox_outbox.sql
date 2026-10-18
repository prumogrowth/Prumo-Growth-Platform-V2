\set ON_ERROR_STOP on
begin;
insert into public.concessionarias(id,nome_operacional) values
 ('c2000000-0000-4000-8000-000000000001','Inbox A ficticia'),
 ('c2000000-0000-4000-8000-000000000002','Inbox B ficticia');
insert into public.canais_loja(id,concessionaria_id,identificador_emissor) values
 ('c3000000-0000-4000-8000-000000000001','c2000000-0000-4000-8000-000000000001','INBOX_EMISSOR_A'),
 ('c3000000-0000-4000-8000-000000000002','c2000000-0000-4000-8000-000000000002','INBOX_EMISSOR_B');
do $inbox$
declare itens jsonb; a jsonb;dup jsonb;b jsonb;
begin
 itens:=pg_catalog.jsonb_build_array(
 jsonb_build_object('event_kind','inbound_message','dedupe_key','wamid.ONE','payload_fingerprint',repeat('a',64)),
 jsonb_build_object('event_kind','inbound_message','dedupe_key','wamid.TWO','payload_fingerprint',repeat('b',64)),
 jsonb_build_object('event_kind','status_callback','dedupe_key','wamid.OUT.sent.100','payload_fingerprint',repeat('c',64)),
 jsonb_build_object('event_kind','status_callback','dedupe_key','wamid.OUT.delivered.200','payload_fingerprint',repeat('d',64)));
 a:=prumo_private.aceitar_lote_ingresso_s0('c3000000-0000-4000-8000-000000000001',itens);
 dup:=prumo_private.aceitar_lote_ingresso_s0('c3000000-0000-4000-8000-000000000001',itens);
 b:=prumo_private.aceitar_lote_ingresso_s0('c3000000-0000-4000-8000-000000000002',itens);
 if a->>'outcome'<>'ACCEPTED_DURABLE' or (a->>'accepted')::integer<>4
 or dup->>'outcome'<>'ALREADY_ACCEPTED' or (dup->>'duplicates')::integer<>4
 or b->>'outcome'<>'ACCEPTED_DURABLE'
 or (select count(*) from prumo_private.inbox_eventos_s0)<>8
 or (select count(*) from prumo_private.tarefas_ingresso_s0)<>8
 then raise exception 'FAIL WA-IN-01: batch atomico/duplicidade/multiloja';end if;
end $inbox$;
\echo 'PASS WA-IN-01: quatro eventos POST, quatro tarefas atomicas e dois escopos'

do $inbox$
begin
 begin
  perform prumo_private.aceitar_lote_ingresso_s0(
  'c3000000-0000-4000-8000-000000000001',
  jsonb_build_array(
   jsonb_build_object('event_kind','inbound_message','dedupe_key','MUST-ROLLBACK','payload_fingerprint',repeat('a',64)),
   jsonb_build_object('event_kind','oops','dedupe_key','BAD','payload_fingerprint',repeat('b',64))));
  raise exception 'FAIL WA-IN-02: item invalido aceito';
 exception when invalid_parameter_value then null;end;
 if exists(select 1 from prumo_private.inbox_eventos_s0 where chave_evento='MUST-ROLLBACK')
 then raise exception 'FAIL WA-IN-02: ACK parcial/perda';end if;
 begin
  perform prumo_private.aceitar_lote_ingresso_s0(
   'c3000000-0000-4000-8000-000000000001',
   jsonb_build_array(jsonb_build_object('event_kind','inbound_message',
   'dedupe_key','wamid.ONE','payload_fingerprint',repeat('f',64))));
  raise exception 'FAIL WA-IN-02: replay conflitante';
 exception when unique_violation then null;end;
 if (select count(*) from prumo_private.inbox_eventos_s0)<>8
 then raise exception 'FAIL WA-IN-02: alteração apos erro';end if;
end $inbox$;
\echo 'PASS WA-IN-02: item invalido e fingerprint divergente nao deixam commit parcial'

do $worker$
declare a jsonb;b jsonb;c jsonb;
begin
 a:=prumo_private.reservar_ingresso_s0(
 'c2000000-0000-4000-8000-000000000001',
 'c3000000-0000-4000-8000-000000000001',
 'c4000000-0000-4000-8000-000000000001');
 b:=prumo_private.reservar_ingresso_s0(
 'c2000000-0000-4000-8000-000000000001',
 'c3000000-0000-4000-8000-000000000001',
 'c4000000-0000-4000-8000-000000000002');
 if a->>'outcome'<>'LEASED' or b->>'outcome'<>'LEASED'
  or a->>'inbox_id'=b->>'inbox_id'
  or (select count(*) from prumo_private.tarefas_ingresso_s0
     where estado='LEASED' and concessionaria_id='c2000000-0000-4000-8000-000000000001')<>2
 then raise exception 'FAIL WA-IN-03: lease duplicado';end if;
 begin
  perform prumo_private.reservar_ingresso_s0(
   'c2000000-0000-4000-8000-000000000002',
   'c3000000-0000-4000-8000-000000000001',
   'c4000000-0000-4000-8000-000000000003');
  raise exception 'FAIL WA-IN-03: escopo trocado';
 exception when insufficient_privilege then null;end;
end $worker$;
\echo 'PASS WA-IN-03: lease de worker evita duplo claim e valida canal da loja'

do $outbox$
declare a jsonb;b jsonb;
begin
 a:=prumo_private.registrar_intencao_bloqueada_s0(
 'c2000000-0000-4000-8000-000000000001',
 'c3000000-0000-4000-8000-000000000001','C03','IA-FIXTURE-001',1);
 b:=prumo_private.registrar_intencao_bloqueada_s0(
 'c2000000-0000-4000-8000-000000000001',
 'c3000000-0000-4000-8000-000000000001','C03','IA-FIXTURE-001',1);
 if a->>'outcome'<>'ACCEPTED_BLOCKED' or b->>'outcome'<>'ALREADY_BLOCKED'
 or a->>'intent_id'<>b->>'intent_id'
 or (select estado from prumo_private.outbox_intencoes_s0 limit 1)<>'BLOQUEADA_GATES'
 then raise exception 'FAIL WA-OUT-01';end if;
 begin
 perform prumo_private.registrar_intencao_bloqueada_s0(
 'c2000000-0000-4000-8000-000000000001',
 'c3000000-0000-4000-8000-000000000001','C12','IA-FIXTURE-001',2);
 raise exception 'FAIL WA-OUT-01: chave reusada em outro contrato';
 exception when unique_violation then null;end;
end $outbox$;
\echo 'PASS WA-OUT-01: outbox unificada sem estado executavel, idempotencia C03/C12/C06'

do $acl$
begin
 if has_table_privilege('anon','prumo_private.inbox_eventos_s0','SELECT')
 or has_table_privilege('authenticated','prumo_private.tarefas_ingresso_s0','INSERT')
 or has_table_privilege('service_role','prumo_private.outbox_intencoes_s0','SELECT')
 or has_function_privilege('prumo_s0_gateway','prumo_private.aceitar_lote_ingresso_s0(uuid,jsonb)','EXECUTE')
 or has_function_privilege('authenticated','prumo_private.registrar_intencao_bloqueada_s0(uuid,uuid,text,text,bigint)','EXECUTE')
 then raise exception 'FAIL WA-SEC-01 ACL';end if;
end $acl$;
\echo 'PASS WA-SEC-01: nenhuma API publica ou gateway comercial recebe acesso'
rollback;
