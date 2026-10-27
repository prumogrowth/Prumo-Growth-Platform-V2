\set ON_ERROR_STOP on
begin;
insert into public.concessionarias(id,nome_operacional) values
 ('a3300000-0000-4000-8000-000000000001','WA33 A fixture'),
 ('a3300000-0000-4000-8000-000000000002','WA33 B fixture');
insert into public.canais_loja(id,concessionaria_id,identificador_emissor) values
 ('a3310000-0000-4000-8000-000000000001','a3300000-0000-4000-8000-000000000001','WA33_CH_A'),
 ('a3310000-0000-4000-8000-000000000002','a3300000-0000-4000-8000-000000000002','WA33_CH_B');
insert into prumo_private.meta_apps_fixture_s0(app_ref,concessionaria_id) values
 ('FIXTURE_WA33_APP_A','a3300000-0000-4000-8000-000000000001'),
 ('FIXTURE_WA33_APP_B','a3300000-0000-4000-8000-000000000002');
insert into prumo_private.meta_canais_fixture_s0(
 app_ref,concessionaria_id,canal_id,waba_ref,phone_number_ref) values
 ('FIXTURE_WA33_APP_A','a3300000-0000-4000-8000-000000000001',
  'a3310000-0000-4000-8000-000000000001','FIXTURE_WA33_WABA_A','FIXTURE_WA33_PHONE_A'),
 ('FIXTURE_WA33_APP_B','a3300000-0000-4000-8000-000000000002',
  'a3310000-0000-4000-8000-000000000002','FIXTURE_WA33_WABA_B','FIXTURE_WA33_PHONE_B');

create function pg_temp.wa33_receber(p_loja uuid,p_msg text,p_marker text)
returns uuid language plpgsql as $helper$
declare v_app text;v_waba text;v_phone text;v_result jsonb;v_id uuid;
begin
 if p_loja='a3300000-0000-4000-8000-000000000001' then
  v_app:='FIXTURE_WA33_APP_A';v_waba:='FIXTURE_WA33_WABA_A';v_phone:='FIXTURE_WA33_PHONE_A';
 elsif p_loja='a3300000-0000-4000-8000-000000000002' then
  v_app:='FIXTURE_WA33_APP_B';v_waba:='FIXTURE_WA33_WABA_B';v_phone:='FIXTURE_WA33_PHONE_B';
 else raise exception 'WA33 invalid fixture shop';end if;
 v_result:=prumo_private.aceitar_lote_multicanal_fixture_s0(
 jsonb_build_array(jsonb_build_object('app_ref',v_app,'waba_id',v_waba,
 'phone_number_id',v_phone,'event_kind','inbound_message',
 'provider_message_id',p_msg,'provider_kind','text',
 'provider_timestamp','2026-10-18T10:00:00Z',
 'payload_fixture',jsonb_build_object('fixture_ref',p_marker))));
 if v_result->>'outcome'<>'FIXTURE_BATCH_STORED' or (v_result->>'accepted')::int<>1
 then raise exception 'FAIL WA33 helper';end if;
 select id into v_id from prumo_private.inbox_eventos_s0 where
 concessionaria_id=p_loja and provider_message_id_s0=p_msg;
 if v_id is null then raise exception 'FAIL WA33 missing inbox';end if;
 return v_id;
end $helper$;

do $t$
declare a uuid;b uuid;c uuid;v jsonb;v_msg uuid;v_worker uuid:='a3320000-0000-4000-8000-000000000001';
begin
 a:=pg_temp.wa33_receber('a3300000-0000-4000-8000-000000000001',
  'wamid.WA33.A1','FIXTURE_WA33_A1');
 v:=prumo_private.anexar_fixture_c02_s0(
  'a3300000-0000-4000-8000-000000000001',
  'a3310000-0000-4000-8000-000000000001',
  a,'+5581900002222','wamid.WA33.A1','Mensagem A1 ficticia',true);
 if v->>'outcome'<>'FIXTURE_ATTACHED' then raise exception 'FAIL WA33-01 attach';end if;
 v:=prumo_private.anexar_fixture_c02_s0(
  'a3300000-0000-4000-8000-000000000001',
  'a3310000-0000-4000-8000-000000000001',
  a,'+5581900002222','wamid.WA33.A1','Mensagem A1 ficticia',true);
 if v->>'outcome'<>'ALREADY_ATTACHED' then raise exception 'FAIL WA33-01 fixture replay';end if;
 begin
 perform prumo_private.anexar_fixture_c02_s0(
  'a3300000-0000-4000-8000-000000000001',
  'a3310000-0000-4000-8000-000000000001',
  a,'+5581900002222','wamid.WA33.A1','ALTERED',true);
 raise exception 'FAIL WA33-01 changed fixture accepted';
 exception when unique_violation then null;end;
 v:=prumo_private.reservar_ingresso_s0(
 'a3300000-0000-4000-8000-000000000001',
 'a3310000-0000-4000-8000-000000000001',v_worker);
 if v->>'inbox_id'<>a::text or (v->>'versao')::int<>2 then
 raise exception 'FAIL WA33-01 claim';end if;
 begin
 perform prumo_private.aplicar_inbox_c02_s0(
 'a3300000-0000-4000-8000-000000000001',
 'a3310000-0000-4000-8000-000000000001',
 a,'a3320000-0000-4000-8000-000000000002',2);
 raise exception 'FAIL WA33-01 wrong worker';
 exception when serialization_failure then null;end;
 v:=prumo_private.aplicar_inbox_c02_s0(
 'a3300000-0000-4000-8000-000000000001',
 'a3310000-0000-4000-8000-000000000001',a,v_worker,2);
 if v->>'outcome'<>'APPLIED_ATOMIC' or v->>'c02_outcome'<>'APPLIED'
 then raise exception 'FAIL WA33-01 atomic';end if;
 v_msg:=(v->>'mensagem_id')::uuid;
 v:=prumo_private.aplicar_inbox_c02_s0(
 'a3300000-0000-4000-8000-000000000001',
 'a3310000-0000-4000-8000-000000000001',a,v_worker,2);
 if v->>'outcome'<>'ALREADY_APPLIED' or (v->>'mensagem_id')::uuid<>v_msg
 or (select count(*) from prumo_private.aplicacoes_c02_inbox_s0 where inbox_id=a)<>1
 or (select count(*) from public.mensagens where id_externo='wamid.WA33.A1')<>1
 then raise exception 'FAIL WA33-01 replay/dedupe';end if;

 b:=pg_temp.wa33_receber('a3300000-0000-4000-8000-000000000001',
  'wamid.WA33.A2','FIXTURE_WA33_A2');
 perform prumo_private.anexar_fixture_c02_s0(
  'a3300000-0000-4000-8000-000000000001',
  'a3310000-0000-4000-8000-000000000001',
  b,'+558100002222','wamid.WA33.A2','Mensagem A2 ficticia',true);
 v:=prumo_private.reservar_ingresso_s0(
 'a3300000-0000-4000-8000-000000000001',
 'a3310000-0000-4000-8000-000000000001',v_worker);
 if v->>'inbox_id'<>b::text then raise exception 'FAIL WA33-01 claim B';end if;
 perform prumo_private.aplicar_inbox_c02_s0(
 'a3300000-0000-4000-8000-000000000001',
 'a3310000-0000-4000-8000-000000000001',b,v_worker,(v->>'versao')::bigint);
 c:=pg_temp.wa33_receber('a3300000-0000-4000-8000-000000000002',
  'wamid.WA33.B1','FIXTURE_WA33_B1');
 perform prumo_private.anexar_fixture_c02_s0(
  'a3300000-0000-4000-8000-000000000002',
  'a3310000-0000-4000-8000-000000000002',
  c,'+5581900002222','wamid.WA33.B1','Mensagem B1 ficticia',true);
 v:=prumo_private.reservar_ingresso_s0(
 'a3300000-0000-4000-8000-000000000002',
 'a3310000-0000-4000-8000-000000000002',v_worker);
 perform prumo_private.aplicar_inbox_c02_s0(
 'a3300000-0000-4000-8000-000000000002',
 'a3310000-0000-4000-8000-000000000002',c,v_worker,(v->>'versao')::bigint);
 if (select count(*) from public.leads_loja
  where concessionaria_id='a3300000-0000-4000-8000-000000000001')<>1
 or (select count(*) from public.ciclos_comerciais
  where concessionaria_id='a3300000-0000-4000-8000-000000000001')<>1
 or (select count(*) from public.mensagens
  where concessionaria_id='a3300000-0000-4000-8000-000000000001')<>2
 or (select count(*) from public.leads_loja
  where concessionaria_id='a3300000-0000-4000-8000-000000000002')<>1
 or (select count(*) from public.mensagens
  where concessionaria_id='a3300000-0000-4000-8000-000000000002')<>1
 or (select count(*) from prumo_private.aplicacoes_c02_inbox_s0)<>3
 or (select count(*) from prumo_private.tarefas_ingresso_s0 where estado='APPLIED')<>3
 then raise exception 'FAIL WA33-01 shop/alias/transaction';end if;
end $t$;
\echo 'PASS WA33-01: C02 e settlement atomicos, replay, 8/9 e lojas isoladas'

-- Force failure AFTER C02 effect but BEFORE proof+settlement commit.
create function pg_temp.wa33_fail_insert()
returns trigger language plpgsql as $f$
begin
 raise exception 'FIXTURE_ABORT_AFTER_C02' using errcode='P0001';
end $f$;
do $t$
declare v uuid;r jsonb;w uuid:='a3320000-0000-4000-8000-000000000003';
begin
 v:=pg_temp.wa33_receber('a3300000-0000-4000-8000-000000000001',
  'wamid.WA33.ROLLBACK','FIXTURE_WA33_ABORT');
 perform prumo_private.anexar_fixture_c02_s0(
 'a3300000-0000-4000-8000-000000000001',
 'a3310000-0000-4000-8000-000000000001',v,
 '+558177771111','wamid.WA33.ROLLBACK','Mensagem rollback ficticia',true);
 r:=prumo_private.reservar_ingresso_s0(
 'a3300000-0000-4000-8000-000000000001',
 'a3310000-0000-4000-8000-000000000001',w);
 create trigger wa33_fixture_abort before insert on prumo_private.aplicacoes_c02_inbox_s0
 for each row execute function pg_temp.wa33_fail_insert();
 begin
  perform prumo_private.aplicar_inbox_c02_s0(
   'a3300000-0000-4000-8000-000000000001',
   'a3310000-0000-4000-8000-000000000001',
   v,w,(r->>'versao')::bigint);
  raise exception 'FAIL WA33-02 expected abort';
 exception when raise_exception then
  if SQLERRM is distinct from 'FIXTURE_ABORT_AFTER_C02'
  then raise exception 'FAIL WA33-02 wrong injected exception: %',SQLERRM;end if;
 end;
 if exists(select 1 from public.mensagens where id_externo='wamid.WA33.ROLLBACK')
 or exists(select 1 from prumo_private.aplicacoes_c02_inbox_s0 where inbox_id=v)
 or (select estado from prumo_private.tarefas_ingresso_s0 where inbox_id=v)<>'LEASED'
 or (select count(*) from prumo_private.historico_tarefas_ingresso_s0 where inbox_id=v)<>1
 then raise exception 'FAIL WA33-02 partial commit';end if;
 drop trigger wa33_fixture_abort on prumo_private.aplicacoes_c02_inbox_s0;
 r:=prumo_private.aplicar_inbox_c02_s0(
   'a3300000-0000-4000-8000-000000000001',
   'a3310000-0000-4000-8000-000000000001',
   v,w,(r->>'versao')::bigint);
 if r->>'outcome'<>'APPLIED_ATOMIC'
 or (select count(*) from public.mensagens where id_externo='wamid.WA33.ROLLBACK')<>1
 then raise exception 'FAIL WA33-02 retry after atomic abort';end if;
end $t$;
\echo 'PASS WA33-02: failure after C02 rolls back message, task and audit together'

do $t$
declare v uuid;r jsonb;
begin
 v:=pg_temp.wa33_receber('a3300000-0000-4000-8000-000000000001',
   'wamid.WA33.EXPIRED','FIXTURE_WA33_EXPIRED');
 perform prumo_private.anexar_fixture_c02_s0(
 'a3300000-0000-4000-8000-000000000001',
 'a3310000-0000-4000-8000-000000000001',v,
 '+558166661111','wamid.WA33.EXPIRED','Lease expirada ficticia',true);
 r:=prumo_private.reservar_ingresso_s0(
 'a3300000-0000-4000-8000-000000000001',
 'a3310000-0000-4000-8000-000000000001',
 'a3320000-0000-4000-8000-000000000005');
 update prumo_private.tarefas_ingresso_s0
  set lease_ate=pg_catalog.clock_timestamp()-interval '1 second' where inbox_id=v;
 begin
  perform prumo_private.aplicar_inbox_c02_s0(
  'a3300000-0000-4000-8000-000000000001',
  'a3310000-0000-4000-8000-000000000001',v,
  'a3320000-0000-4000-8000-000000000005',(r->>'versao')::bigint);
  raise exception 'FAIL WA33-03 expired lease applied';
 exception when serialization_failure then null;end;
 if exists(select 1 from public.mensagens where id_externo='wamid.WA33.EXPIRED')
 or exists(select 1 from prumo_private.aplicacoes_c02_inbox_s0 where inbox_id=v)
 then raise exception 'FAIL WA33-03 effect without lease';end if;
end $t$;
\echo 'PASS WA33-03: lease vencido nao altera dominio nem tarefa'

do $t$
declare v uuid;r jsonb;
begin
 -- Old C02 text-only importer created a legacy 8-digit contact.
 insert into public.leads_loja(concessionaria_id,telefone_cliente_normalizado)
 values('a3300000-0000-4000-8000-000000000001','+558122223333');
 v:=pg_temp.wa33_receber('a3300000-0000-4000-8000-000000000001',
  'wamid.WA33.REVIEW','FIXTURE_WA33_REVIEW');
 perform prumo_private.anexar_fixture_c02_s0(
 'a3300000-0000-4000-8000-000000000001',
 'a3310000-0000-4000-8000-000000000001',v,
 '+5581922223333','wamid.WA33.REVIEW','Identidade pendente',true);
 r:=prumo_private.reservar_ingresso_s0(
 'a3300000-0000-4000-8000-000000000001',
 'a3310000-0000-4000-8000-000000000001',
 'a3320000-0000-4000-8000-000000000006');
 r:=prumo_private.aplicar_inbox_c02_s0(
   'a3300000-0000-4000-8000-000000000001',
   'a3310000-0000-4000-8000-000000000001',
   v,'a3320000-0000-4000-8000-000000000006',(r->>'versao')::bigint);
 if r->>'outcome'<>'QUARANTINED_IDENTITY' or r->>'motivo'<>'NEEDS_REVIEW'
 then raise exception 'FAIL WA33-04 identity was not quarantined';end if;
 if exists(select 1 from public.mensagens where id_externo='wamid.WA33.REVIEW')
 or exists(select 1 from prumo_private.aplicacoes_c02_inbox_s0 where inbox_id=v)
 or (select count(*) from prumo_private.pendencias_identidade_s0
     where concessionaria_id='a3300000-0000-4000-8000-000000000001'
       and canal_id='a3310000-0000-4000-8000-000000000001'
       and id_externo='wamid.WA33.REVIEW' and motivo='NEEDS_REVIEW')<>1
 or (select count(*) from prumo_private.tarefas_ingresso_s0
     where inbox_id=v and estado='QUARANTINED'
       and motivo_terminal_s0='NEEDS_REVIEW')<>1
 or (select count(*) from prumo_private.historico_tarefas_ingresso_s0
     where inbox_id=v and acao='NEEDS_REVIEW')<>1
 then raise exception 'FAIL WA33-04 identity reason not durable';end if;
end $t$;
\echo 'PASS WA33-04: identidade ambigua preservada em pendencia e quarentena atomica'

do $t$
declare v uuid;
begin
 v:=pg_temp.wa33_receber('a3300000-0000-4000-8000-000000000001',
  'wamid.WA33.NOATTACH','FIXTURE_WA33_NOTATTACHED');
 begin
  perform prumo_private.anexar_fixture_c02_s0(
   'a3300000-0000-4000-8000-000000000002',
   'a3310000-0000-4000-8000-000000000002',
   v,'+5581999999999','wamid.WA33.NOATTACH','Wrong shop',true);
  raise exception 'FAIL WA33-05 cross shop';
 exception when insufficient_privilege then null;end;
 begin
  perform prumo_private.anexar_fixture_c02_s0(
   'a3300000-0000-4000-8000-000000000001',
   'a3310000-0000-4000-8000-000000000001',
   v,'+5581999999999','wamid.WRONG.ID','Wrong provider ID',true);
  raise exception 'FAIL WA33-05 sender mismatch';
 exception when insufficient_privilege then null;end;
 if has_table_privilege('anon','prumo_private.inbox_c02_fixture_s0','SELECT')
 or has_table_privilege('authenticated','prumo_private.aplicacoes_c02_inbox_s0','INSERT')
 or has_function_privilege('service_role',
  'prumo_private.aplicar_inbox_c02_s0(uuid,uuid,uuid,uuid,bigint)','EXECUTE')
 or has_function_privilege('prumo_s0_gateway',
  'prumo_private.anexar_fixture_c02_s0(uuid,uuid,uuid,text,text,text,boolean)','EXECUTE')
 then raise exception 'FAIL WA33-05 public rights';end if;
end $t$;
\echo 'PASS WA33-05: app/canal/loja, message-id e ACL privada'
rollback;
