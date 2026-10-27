\set ON_ERROR_STOP on
begin;
insert into public.concessionarias(id,nome_operacional) values
 ('a3200000-0000-4000-8000-000000000001','WA32 A ficticia'),
 ('a3200000-0000-4000-8000-000000000002','WA32 B ficticia');
insert into public.canais_loja(id,concessionaria_id,identificador_emissor) values
 ('a3210000-0000-4000-8000-000000000001','a3200000-0000-4000-8000-000000000001','WA32-SIM-A'),
 ('a3210000-0000-4000-8000-000000000002','a3200000-0000-4000-8000-000000000002','WA32-SIM-B');

do $t$
declare v jsonb;v_id uuid;v_ver bigint;v_res jsonb;
begin
 perform prumo_private.aceitar_lote_ingresso_s0(
 'a3210000-0000-4000-8000-000000000001',
 jsonb_build_array(jsonb_build_object('event_kind','inbound_message',
 'dedupe_key','WA32-APPLY','payload_fingerprint',repeat('a',64))));
 select id into v_id from prumo_private.inbox_eventos_s0 where chave_evento='WA32-APPLY';
 v:=prumo_private.reservar_ingresso_s0(
 'a3200000-0000-4000-8000-000000000001',
 'a3210000-0000-4000-8000-000000000001',
 'a3220000-0000-4000-8000-000000000001');
 v_ver:=(v->>'versao')::bigint;
 if v->>'outcome'<>'LEASED' or v_ver<>2 then raise exception 'FAIL WA32-01 lease';end if;
 begin
  perform prumo_private.registrar_resultado_ingresso_s0(
   'a3200000-0000-4000-8000-000000000001',
   'a3210000-0000-4000-8000-000000000001',v_id,
   'a3220000-0000-4000-8000-000000000002',v_ver,'APLICADO_SINTETICO');
  raise exception 'FAIL WA32-01 wrong worker';
 exception when serialization_failure then null;end;
 begin
  perform prumo_private.registrar_resultado_ingresso_s0(
   'a3200000-0000-4000-8000-000000000001',
   'a3210000-0000-4000-8000-000000000001',v_id,
   'a3220000-0000-4000-8000-000000000001',v_ver+1,'APLICADO_SINTETICO');
  raise exception 'FAIL WA32-01 stale version';
 exception when serialization_failure then null;end;
 v_res:=prumo_private.registrar_resultado_ingresso_s0(
   'a3200000-0000-4000-8000-000000000001',
   'a3210000-0000-4000-8000-000000000001',v_id,
   'a3220000-0000-4000-8000-000000000001',v_ver,'APLICADO_SINTETICO');
 if v_res->>'estado'<>'APPLIED' then raise exception 'FAIL WA32-01 completion';end if;
 v_res:=prumo_private.registrar_resultado_ingresso_s0(
   'a3200000-0000-4000-8000-000000000001',
   'a3210000-0000-4000-8000-000000000001',v_id,
   'a3220000-0000-4000-8000-000000000001',v_ver,'APLICADO_SINTETICO');
 if v_res->>'outcome'<>'ALREADY_RECORDED'
 or (select count(*) from prumo_private.historico_tarefas_ingresso_s0 where inbox_id=v_id)<>2
 or (select estado from prumo_private.tarefas_ingresso_s0 where inbox_id=v_id)<>'APPLIED'
 then raise exception 'FAIL WA32-01 replay/audit';end if;
 begin
  update prumo_private.historico_tarefas_ingresso_s0 set acao='FALHA_DEFINITIVA' where inbox_id=v_id;
  raise exception 'FAIL WA32-01 audit mutable';
 exception when insufficient_privilege then null;end;
end $t$;
\echo 'PASS WA32-01: conclusao versionada, worker errado, replay e auditoria imutavel'

do $t$
declare v jsonb;v_id uuid;v_n int;v_res jsonb;
begin
 perform prumo_private.aceitar_lote_ingresso_s0(
 'a3210000-0000-4000-8000-000000000001',
 jsonb_build_array(jsonb_build_object('event_kind','inbound_message',
 'dedupe_key','WA32-RETRY','payload_fingerprint',repeat('b',64))));
 select id into v_id from prumo_private.inbox_eventos_s0 where chave_evento='WA32-RETRY';
 for v_n in 1..3 loop
  v:=prumo_private.reservar_ingresso_s0(
   'a3200000-0000-4000-8000-000000000001',
   'a3210000-0000-4000-8000-000000000001',
   'a3220000-0000-4000-8000-000000000001');
  if v->>'outcome'<>'LEASED' or (v->>'tentativas')::int<>v_n
  then raise exception 'FAIL WA32-02 attempt %',v_n;end if;
  v_res:=prumo_private.registrar_resultado_ingresso_s0(
   'a3200000-0000-4000-8000-000000000001',
   'a3210000-0000-4000-8000-000000000001',
   v_id,'a3220000-0000-4000-8000-000000000001',
   (v->>'versao')::bigint,'FALHA_RETRY_SEGURA');
  if v_n<3 then
   if v_res->>'estado'<>'RETRY_PENDING'
   then raise exception 'FAIL WA32-02 not pending';end if;
   v:=prumo_private.reservar_ingresso_s0(
    'a3200000-0000-4000-8000-000000000001',
    'a3210000-0000-4000-8000-000000000001',
    'a3220000-0000-4000-8000-000000000002');
   if v->>'outcome'<>'EMPTY' then raise exception 'FAIL WA32-02 premature retry';end if;
   -- Controlled fixture time travel, no external side effect.
   update prumo_private.tarefas_ingresso_s0
    set proxima_tentativa_em=clock_timestamp()-interval '1 second'
    where inbox_id=v_id;
  else
   if v_res->>'estado'<>'DEAD_LETTER'
   then raise exception 'FAIL WA32-02 attempts cap';end if;
  end if;
 end loop;
 if (select count(*) from prumo_private.historico_tarefas_ingresso_s0 where inbox_id=v_id)<>6
 or (select count(*) from prumo_private.tarefas_ingresso_s0
      where inbox_id=v_id and estado='DEAD_LETTER' and tentativas=3)<>1
 then raise exception 'FAIL WA32-02 trail';end if;
 v:=prumo_private.reservar_ingresso_s0(
  'a3200000-0000-4000-8000-000000000001',
  'a3210000-0000-4000-8000-000000000001',
  'a3220000-0000-4000-8000-000000000002');
 if v->>'outcome'<>'EMPTY' then raise exception 'FAIL WA32-02 fifth claim';end if;
end $t$;
\echo 'PASS WA32-02: retry conhecido com backoff, limite 3 e dead-letter sem auto-envio'

do $t$
declare v jsonb;v_id uuid;
begin
 perform prumo_private.aceitar_lote_ingresso_s0(
 'a3210000-0000-4000-8000-000000000001',
 jsonb_build_array(jsonb_build_object('event_kind','status_callback',
 'dedupe_key','WA32-UNCERTAIN','payload_fingerprint',repeat('c',64))));
 select id into v_id from prumo_private.inbox_eventos_s0 where chave_evento='WA32-UNCERTAIN';
 v:=prumo_private.reservar_ingresso_s0(
  'a3200000-0000-4000-8000-000000000001',
  'a3210000-0000-4000-8000-000000000001',
  'a3220000-0000-4000-8000-000000000001');
 v:=prumo_private.registrar_resultado_ingresso_s0(
  'a3200000-0000-4000-8000-000000000001',
  'a3210000-0000-4000-8000-000000000001',v_id,
  'a3220000-0000-4000-8000-000000000001',
  (v->>'versao')::bigint,'RESULTADO_INCERTO');
 if v->>'estado'<>'QUARANTINED'
 then raise exception 'FAIL WA32-03 uncertain not quarantined';end if;
 v:=prumo_private.reservar_ingresso_s0(
  'a3200000-0000-4000-8000-000000000001',
  'a3210000-0000-4000-8000-000000000001',
  'a3220000-0000-4000-8000-000000000002');
 if v->>'outcome'<>'EMPTY' then raise exception 'FAIL WA32-03 untrusted auto replay';end if;
end $t$;
\echo 'PASS WA32-03: resultado incerto mantido em quarentena, sem retomada'

do $t$
declare v jsonb;v_id uuid;v_ver bigint;
begin
 perform prumo_private.aceitar_lote_ingresso_s0(
 'a3210000-0000-4000-8000-000000000001',
 jsonb_build_array(jsonb_build_object('event_kind','inbound_message',
 'dedupe_key','WA32-EXPIRED','payload_fingerprint',repeat('d',64))));
 select id into v_id from prumo_private.inbox_eventos_s0 where chave_evento='WA32-EXPIRED';
 v:=prumo_private.reservar_ingresso_s0(
 'a3200000-0000-4000-8000-000000000001',
 'a3210000-0000-4000-8000-000000000001',
 'a3220000-0000-4000-8000-000000000001');
 v_ver:=(v->>'versao')::bigint;
 update prumo_private.tarefas_ingresso_s0 set lease_ate=clock_timestamp()-interval '1 second'
 where inbox_id=v_id;
 v:=prumo_private.reservar_ingresso_s0(
 'a3200000-0000-4000-8000-000000000001',
 'a3210000-0000-4000-8000-000000000001',
 'a3220000-0000-4000-8000-000000000002');
 if v->>'outcome'<>'EMPTY' then raise exception 'FAIL WA32-04 expired reclaimed';end if;
 begin
  perform prumo_private.registrar_resultado_ingresso_s0(
  'a3200000-0000-4000-8000-000000000001',
  'a3210000-0000-4000-8000-000000000001',v_id,
  'a3220000-0000-4000-8000-000000000001',v_ver,'APLICADO_SINTETICO');
  raise exception 'FAIL WA32-04 expired worker accepted';
 exception when serialization_failure then null;end;
 begin
  perform prumo_private.reconciliar_lease_expirado_s0(
  'a3200000-0000-4000-8000-000000000001',
  'a3210000-0000-4000-8000-000000000001',v_id,v_ver+1,
  'a3230000-0000-4000-8000-000000000001','QUARENTENA');
  raise exception 'FAIL WA32-04 stale reviewer';
 exception when serialization_failure then null;end;
 v:=prumo_private.reconciliar_lease_expirado_s0(
  'a3200000-0000-4000-8000-000000000001',
  'a3210000-0000-4000-8000-000000000001',v_id,v_ver,
  'a3230000-0000-4000-8000-000000000001','QUARENTENA');
 if v->>'estado'<>'QUARANTINED' then raise exception 'FAIL WA32-04 reconcile';end if;
end $t$;
\echo 'PASS WA32-04: lease vencida exige reconciliação versionada e isolamento'

do $t$
declare v jsonb;v_id uuid;
begin
 perform prumo_private.aceitar_lote_ingresso_s0(
 'a3210000-0000-4000-8000-000000000001',
 jsonb_build_array(jsonb_build_object('event_kind','inbound_message',
 'dedupe_key','WA32-SAFE','payload_fingerprint',repeat('e',64))));
 select id into v_id from prumo_private.inbox_eventos_s0 where chave_evento='WA32-SAFE';
 v:=prumo_private.reservar_ingresso_s0(
 'a3200000-0000-4000-8000-000000000001',
 'a3210000-0000-4000-8000-000000000001',
 'a3220000-0000-4000-8000-000000000001');
 update prumo_private.tarefas_ingresso_s0 set lease_ate=clock_timestamp()-interval '1 second'
 where inbox_id=v_id;
 v:=prumo_private.reconciliar_lease_expirado_s0(
 'a3200000-0000-4000-8000-000000000001',
 'a3210000-0000-4000-8000-000000000001',v_id,
 (v->>'versao')::bigint,'a3230000-0000-4000-8000-000000000001','SEM_EFEITO_FIXTURE');
 if v->>'estado'<>'RETRY_PENDING' then raise exception 'FAIL WA32-05 safe reconciliation';end if;
 update prumo_private.tarefas_ingresso_s0 set proxima_tentativa_em=clock_timestamp()-interval '1 second'
 where inbox_id=v_id;
 v:=prumo_private.reservar_ingresso_s0(
 'a3200000-0000-4000-8000-000000000001',
 'a3210000-0000-4000-8000-000000000001',
 'a3220000-0000-4000-8000-000000000002');
 if v->>'outcome'<>'LEASED' or (v->>'versao')::int<>4
 or (v->>'tentativas')::int<>2
 then raise exception 'FAIL WA32-05 reviewed claim';end if;
end $t$;
\echo 'PASS WA32-05: retentativa so apos declaração manual ficticia sem efeito'

do $t$
declare v jsonb;v_id uuid;
begin
 perform prumo_private.aceitar_lote_ingresso_s0(
 'a3210000-0000-4000-8000-000000000002',
 jsonb_build_array(jsonb_build_object('event_kind','inbound_message',
 'dedupe_key','WA32-B','payload_fingerprint',repeat('f',64))));
 select id into v_id from prumo_private.inbox_eventos_s0 where chave_evento='WA32-B';
 v:=prumo_private.reservar_ingresso_s0(
  'a3200000-0000-4000-8000-000000000002',
  'a3210000-0000-4000-8000-000000000002',
  'a3220000-0000-4000-8000-000000000002');
 begin
  perform prumo_private.registrar_resultado_ingresso_s0(
   'a3200000-0000-4000-8000-000000000001',
   'a3210000-0000-4000-8000-000000000001',v_id,
   'a3220000-0000-4000-8000-000000000002',
   (v->>'versao')::bigint,'FALHA_DEFINITIVA');
  raise exception 'FAIL WA32-06 wrong scope';
 exception when insufficient_privilege then null;end;
 v:=prumo_private.registrar_resultado_ingresso_s0(
  'a3200000-0000-4000-8000-000000000002',
  'a3210000-0000-4000-8000-000000000002',v_id,
  'a3220000-0000-4000-8000-000000000002',
  (v->>'versao')::bigint,'FALHA_DEFINITIVA');
 if v->>'estado'<>'DEAD_LETTER'
 or has_function_privilege('authenticated',
   'prumo_private.registrar_resultado_ingresso_s0(uuid,uuid,uuid,uuid,bigint,text)','EXECUTE')
 or has_function_privilege('service_role',
   'prumo_private.reconciliar_lease_expirado_s0(uuid,uuid,uuid,bigint,uuid,text)','EXECUTE')
 or has_table_privilege('anon',
   'prumo_private.historico_tarefas_ingresso_s0','SELECT')
 or has_function_privilege('prumo_s0_gateway',
   'prumo_private.reservar_ingresso_s0(uuid,uuid,uuid)','EXECUTE')
 then raise exception 'FAIL WA32-06 scope/ACL';end if;
end $t$;
\echo 'PASS WA32-06: DLQ definitivo, FK por loja e sem grants a roles publicos'
rollback;
