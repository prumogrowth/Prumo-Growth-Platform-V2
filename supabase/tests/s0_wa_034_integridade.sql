\set ON_ERROR_STOP on
begin;
insert into public.concessionarias(id,nome_operacional) values
 ('a3400000-0000-4000-8000-000000000001','WA34 integridade ficticia');
insert into public.canais_loja(id,concessionaria_id,identificador_emissor) values
 ('a3410000-0000-4000-8000-000000000001',
  'a3400000-0000-4000-8000-000000000001','WA34_CH_1'),
 ('a3410000-0000-4000-8000-000000000002',
  'a3400000-0000-4000-8000-000000000001','WA34_CH_2');
insert into prumo_private.meta_apps_fixture_s0(app_ref,concessionaria_id)
 values('FIXTURE_WA34_APP','a3400000-0000-4000-8000-000000000001');
insert into prumo_private.meta_canais_fixture_s0(
 app_ref,concessionaria_id,canal_id,waba_ref,phone_number_ref) values
 ('FIXTURE_WA34_APP','a3400000-0000-4000-8000-000000000001',
  'a3410000-0000-4000-8000-000000000001','FIXTURE_WA34_WABA','FIXTURE_WA34_PHONE');

create function pg_temp.wa34_inbox(p_msg text) returns uuid
language plpgsql as $fixture$
declare v_result jsonb;v_id uuid;
begin
 v_result:=prumo_private.aceitar_lote_multicanal_fixture_s0(
  jsonb_build_array(jsonb_build_object(
   'app_ref','FIXTURE_WA34_APP','waba_id','FIXTURE_WA34_WABA',
   'phone_number_id','FIXTURE_WA34_PHONE','event_kind','inbound_message',
   'provider_message_id',p_msg,'provider_kind','text',
   'provider_timestamp','2026-10-18T13:00:00Z',
   'payload_fixture',jsonb_build_object('fixture_ref','FIXTURE_WA34_EVENT'))));
 if v_result->>'outcome'<>'FIXTURE_BATCH_STORED'
 or (v_result->>'accepted')::integer<>1
 then raise exception 'FAIL WA34 fixture ingress';end if;
 select id into v_id from prumo_private.inbox_eventos_s0
 where concessionaria_id='a3400000-0000-4000-8000-000000000001'
 and canal_id='a3410000-0000-4000-8000-000000000001'
 and provider_message_id_s0=p_msg;
 if v_id is null then raise exception 'FAIL WA34 missing inbox';end if;
 return v_id;
end $fixture$;

-- A33-01: generic synthetic lifecycle MUST NOT mark bound C02 APPLIED
-- without the linked message proof, even if called by postgres directly.
do $t$
declare v_id uuid;v_claim jsonb;v_apply jsonb;
begin
 v_id:=pg_temp.wa34_inbox('wamid.WA34.APPLY');
 perform prumo_private.anexar_fixture_c02_s0(
  'a3400000-0000-4000-8000-000000000001',
  'a3410000-0000-4000-8000-000000000001',
  v_id,'+5581900003434','wamid.WA34.APPLY','Prova atomica de C02',true);
 v_claim:=prumo_private.reservar_ingresso_s0(
  'a3400000-0000-4000-8000-000000000001',
  'a3410000-0000-4000-8000-000000000001',
  'a3420000-0000-4000-8000-000000000001');
 if v_claim->>'inbox_id'<>v_id::text then raise exception 'FAIL WA34-01 claim';end if;
 begin
  perform prumo_private.registrar_resultado_ingresso_s0(
   'a3400000-0000-4000-8000-000000000001',
   'a3410000-0000-4000-8000-000000000001',v_id,
   'a3420000-0000-4000-8000-000000000001',
   (v_claim->>'versao')::bigint,'APLICADO_SINTETICO');
  raise exception 'FAIL WA34-01 generic bypass';
 exception when check_violation then
  if SQLERRM is distinct from 'C02_PROOF_REQUIRED'
  then raise exception 'FAIL WA34-01 unexpected guard %',SQLERRM;end if;
 end;
 begin
  update prumo_private.tarefas_ingresso_s0
  set estado='APPLIED',lease_worker=null,lease_ate=null,versao=versao+1
  where inbox_id=v_id;
  raise exception 'FAIL WA34-01 direct update bypass';
 exception when check_violation then
  if SQLERRM is distinct from 'C02_PROOF_REQUIRED'
  then raise exception 'FAIL WA34-01 unexpected trigger %',SQLERRM;end if;
 end;
 if (select estado from prumo_private.tarefas_ingresso_s0
   where inbox_id=v_id)<>'LEASED'
 or exists(select 1 from prumo_private.aplicacoes_c02_inbox_s0
   where inbox_id=v_id)
 then raise exception 'FAIL WA34-01 partial settlement';end if;
 v_apply:=prumo_private.aplicar_inbox_c02_s0(
  'a3400000-0000-4000-8000-000000000001',
  'a3410000-0000-4000-8000-000000000001',v_id,
  'a3420000-0000-4000-8000-000000000001',
  (v_claim->>'versao')::bigint);
 if v_apply->>'outcome'<>'APPLIED_ATOMIC'
 or (select count(*) from prumo_private.aplicacoes_c02_inbox_s0
  where inbox_id=v_id)<>1
 or (select count(*) from prumo_private.tarefas_ingresso_s0
  where inbox_id=v_id and estado='APPLIED')<>1
 then raise exception 'FAIL WA34-01 legit completion';end if;
 v_apply:=prumo_private.aplicar_inbox_c02_s0(
  'a3400000-0000-4000-8000-000000000001',
  'a3410000-0000-4000-8000-000000000001',v_id,
  'a3420000-0000-4000-8000-000000000001',
  (v_claim->>'versao')::bigint);
 if v_apply->>'outcome'<>'ALREADY_APPLIED'
 then raise exception 'FAIL WA34-01 replay';end if;
end $t$;
\echo 'PASS WA34-01: sem APPLIED C02 sem prova, nem via função genérica ou UPDATE direto'

-- A33-03: within one concessionaria even a valid alternate channel cannot
-- replace the one recorded for the original event/proof.
do $t$
declare v_id uuid;v_msg uuid;v_alt uuid;
begin
 select inbox_id,mensagem_id into v_id,v_msg
 from prumo_private.aplicacoes_c02_inbox_s0
 where concessionaria_id='a3400000-0000-4000-8000-000000000001';
 begin
  update prumo_private.inbox_c02_fixture_s0
  set canal_id='a3410000-0000-4000-8000-000000000002'
  where inbox_id=v_id;
  raise exception 'FAIL WA34-02 cross-channel fixture';
 exception when foreign_key_violation then null;end;
 begin
  update prumo_private.aplicacoes_c02_inbox_s0
  set canal_id='a3410000-0000-4000-8000-000000000002'
  where inbox_id=v_id;
  raise exception 'FAIL WA34-02 cross-channel application';
 exception when check_violation or foreign_key_violation then null;end;
 -- A valid commercial inbound in a different channel cannot be substituted
 -- despite both messages having the same concessionaria_id.
 v_alt:= (prumo_private.receber_mensagem_sintetica(
 'a3410000-0000-4000-8000-000000000002',
 '+5581900009898','wamid.WA34.OTHERCH','Outra conversa ficticia'))->>'mensagem_id';
 begin
  update prumo_private.aplicacoes_c02_inbox_s0
  set mensagem_id=v_alt where inbox_id=v_id;
  raise exception 'FAIL WA34-02 cross-channel message';
 exception when check_violation then
  if SQLERRM is distinct from 'INVALID_C02_MESSAGE_PROOF'
  then raise exception 'FAIL WA34-02 wrong proof reason %',SQLERRM;end if;
 end;
 -- Isolate the physical composite FK check from the earlier validation
 -- trigger, only inside this rollback-only fixture transaction.
 alter table prumo_private.aplicacoes_c02_inbox_s0
   disable trigger aplicacao_c02_prova_sem_desvio_s0;
 begin
  update prumo_private.aplicacoes_c02_inbox_s0
  set mensagem_id=v_alt where inbox_id=v_id;
  raise exception 'FAIL WA34-02 composite FK not enforced';
 exception when foreign_key_violation then null;end;
 alter table prumo_private.aplicacoes_c02_inbox_s0
   enable trigger aplicacao_c02_prova_sem_desvio_s0;
 -- A different message in the SAME channel also has to match both provider
 -- ID and fixture content (composite FK alone would not catch this).
 v_alt:=(prumo_private.receber_mensagem_sintetica(
 'a3410000-0000-4000-8000-000000000001',
 '+5581900009999','wamid.WA34.SAMECH','Outro texto ficticio'))->>'mensagem_id';
 begin
  update prumo_private.aplicacoes_c02_inbox_s0
  set mensagem_id=v_alt where inbox_id=v_id;
  raise exception 'FAIL WA34-02 incorrect message evidence';
 exception when check_violation then
  if SQLERRM is distinct from 'INVALID_C02_MESSAGE_PROOF'
  then raise exception 'FAIL WA34-02 wrong validation %',SQLERRM;end if;
 end;
 if (select mensagem_id from prumo_private.aplicacoes_c02_inbox_s0
   where inbox_id=v_id)<>v_msg
 then raise exception 'FAIL WA34-02 original proof changed';end if;
end $t$;
\echo 'PASS WA34-02: integridade loja+canal+inbox/mensagem e verificação de conteúdo'

-- A33-02: an actual synthetic ambiguous identity must persist pending proof
-- AND an explicitly typed quarantine, with no C02 message or false APPLIED.
do $t$
declare v_id uuid;v_claim jsonb;v_res jsonb;
begin
 insert into public.leads_loja(concessionaria_id,telefone_cliente_normalizado)
 values('a3400000-0000-4000-8000-000000000001','+558122223333');
 v_id:=pg_temp.wa34_inbox('wamid.WA34.REVIEW');
 perform prumo_private.anexar_fixture_c02_s0(
  'a3400000-0000-4000-8000-000000000001',
  'a3410000-0000-4000-8000-000000000001',v_id,
  '+5581922223333','wamid.WA34.REVIEW','Conflito legado de identidade',true);
 v_claim:=prumo_private.reservar_ingresso_s0(
 'a3400000-0000-4000-8000-000000000001',
 'a3410000-0000-4000-8000-000000000001',
 'a3420000-0000-4000-8000-000000000002');
 v_res:=prumo_private.aplicar_inbox_c02_s0(
  'a3400000-0000-4000-8000-000000000001',
  'a3410000-0000-4000-8000-000000000001',v_id,
  'a3420000-0000-4000-8000-000000000002',
  (v_claim->>'versao')::bigint);
 if v_res->>'outcome'<>'QUARANTINED_IDENTITY'
 or v_res->>'motivo'<>'NEEDS_REVIEW'
 or (select count(*) from prumo_private.pendencias_identidade_s0
  where concessionaria_id='a3400000-0000-4000-8000-000000000001'
   and id_externo='wamid.WA34.REVIEW' and motivo='NEEDS_REVIEW')<>1
 or (select count(*) from prumo_private.tarefas_ingresso_s0
  where inbox_id=v_id and estado='QUARANTINED' and motivo_terminal_s0='NEEDS_REVIEW')<>1
 or (select count(*) from prumo_private.historico_tarefas_ingresso_s0
  where inbox_id=v_id and acao='NEEDS_REVIEW')<>1
 or exists(select 1 from public.mensagens where id_externo='wamid.WA34.REVIEW')
 or exists(select 1 from prumo_private.aplicacoes_c02_inbox_s0 where inbox_id=v_id)
 then raise exception 'FAIL WA34-03: conflict evidence not atomic';end if;
 -- A subsequent attempt cannot apply a quarantined job.
 begin
  perform prumo_private.aplicar_inbox_c02_s0(
   'a3400000-0000-4000-8000-000000000001',
   'a3410000-0000-4000-8000-000000000001',v_id,
   'a3420000-0000-4000-8000-000000000002',
   (v_claim->>'versao')::bigint);
  raise exception 'FAIL WA34-03 quarantined reapplied';
 exception when serialization_failure then null;end;
 if (select count(*) from prumo_private.pendencias_identidade_s0
  where id_externo='wamid.WA34.REVIEW')<>1
 then raise exception 'FAIL WA34-03 lost pending under replay';end if;
end $t$;
\echo 'PASS WA34-03: pendencia e quarentena atômicas com causa NEEDS_REVIEW'

do $t$
declare v_id uuid;v_claim jsonb;v_result jsonb;
begin
 insert into public.leads_loja(concessionaria_id,telefone_cliente_normalizado)
 values('a3400000-0000-4000-8000-000000000001','+5581988884444'),
 ('a3400000-0000-4000-8000-000000000001','+558188884444');
 v_id:=pg_temp.wa34_inbox('wamid.WA34.CONFLICT');
 perform prumo_private.anexar_fixture_c02_s0(
  'a3400000-0000-4000-8000-000000000001',
  'a3410000-0000-4000-8000-000000000001',
  v_id,'+5581988884444','wamid.WA34.CONFLICT','Dois leads conflitantes',true);
 v_claim:=prumo_private.reservar_ingresso_s0(
  'a3400000-0000-4000-8000-000000000001',
  'a3410000-0000-4000-8000-000000000001',
  'a3420000-0000-4000-8000-000000000003');
 v_result:=prumo_private.aplicar_inbox_c02_s0(
  'a3400000-0000-4000-8000-000000000001',
  'a3410000-0000-4000-8000-000000000001',v_id,
  'a3420000-0000-4000-8000-000000000003',
  (v_claim->>'versao')::bigint);
 if v_result->>'motivo'<>'IDENTITY_CONFLICT'
 or (select motivo_terminal_s0 from prumo_private.tarefas_ingresso_s0
  where inbox_id=v_id)<>'IDENTITY_CONFLICT'
 or (select count(*) from prumo_private.pendencias_identidade_s0
  where id_externo='wamid.WA34.CONFLICT' and motivo='IDENTITY_CONFLICT')<>1
 then raise exception 'FAIL WA34-04 conflict reason';end if;
end $t$;
\echo 'PASS WA34-04: dois leads em colisão preservam IDENTITY_CONFLICT distinto'

do $t$
declare v_id uuid;v_claim jsonb;
begin
 v_id:=pg_temp.wa34_inbox('wamid.WA34.NOPENDING');
 perform prumo_private.anexar_fixture_c02_s0(
  'a3400000-0000-4000-8000-000000000001',
  'a3410000-0000-4000-8000-000000000001',
  v_id,'+5581900009090','wamid.WA34.NOPENDING','Sem pendencia de identidade',true);
 v_claim:=prumo_private.reservar_ingresso_s0(
  'a3400000-0000-4000-8000-000000000001',
  'a3410000-0000-4000-8000-000000000001',
  'a3420000-0000-4000-8000-000000000004');
 begin
  perform prumo_private.registrar_resultado_ingresso_s0(
   'a3400000-0000-4000-8000-000000000001',
   'a3410000-0000-4000-8000-000000000001',v_id,
   'a3420000-0000-4000-8000-000000000004',
   (v_claim->>'versao')::bigint,'NEEDS_REVIEW');
  raise exception 'FAIL WA34-05 fabricated review';
 exception when check_violation then
  if SQLERRM is distinct from 'IDENTITY_PENDING_PROOF_REQUIRED'
  then raise exception 'FAIL WA34-05 reason mismatch %',SQLERRM;end if;
 end;
 if (select estado from prumo_private.tarefas_ingresso_s0
  where inbox_id=v_id)<>'LEASED'
 then raise exception 'FAIL WA34-05 altered task';end if;
 if has_function_privilege('authenticated',
  'prumo_private.aplicar_inbox_c02_s0(uuid,uuid,uuid,uuid,bigint)','EXECUTE')
 or has_function_privilege('service_role',
  'prumo_private.registrar_resultado_ingresso_s0(uuid,uuid,uuid,uuid,bigint,text)','EXECUTE')
 or has_table_privilege('anon','prumo_private.aplicacoes_c02_inbox_s0','SELECT')
 then raise exception 'FAIL WA34-05 ACL';end if;
end $t$;
\echo 'PASS WA34-05: quarentena nao pode forjar pendência; sem grants públicos'
rollback;
