\set ON_ERROR_STOP on
-- S0-037C: signed commercial execution END-TO-END regression, PG17 fixture.
-- No new owner, migration, runtime role, API, Meta key or external activity.
-- The legacy commercial wrappers are still SECURITY DEFINER postgres.
begin;
create table if not exists auth.sessions (
 id uuid primary key, user_id uuid not null references auth.users(id));

insert into auth.users(id) values
 ('c3900000-0000-4000-8000-000000000001'),
 ('c3900000-0000-4000-8000-000000000002');
insert into public.atores(id) values
 ('c3900000-0000-4000-8000-000000000001'),
 ('c3900000-0000-4000-8000-000000000002');
insert into auth.sessions(id,user_id) values
 ('c3910000-0000-4000-8000-000000000001','c3900000-0000-4000-8000-000000000001'),
 ('c3910000-0000-4000-8000-000000000002','c3900000-0000-4000-8000-000000000002');
insert into public.concessionarias(id,nome_operacional) values
 ('c3920000-0000-4000-8000-000000000001','037C Loja A ficticia'),
 ('c3920000-0000-4000-8000-000000000002','037C Loja B ficticia');
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel) values
 ('c3900000-0000-4000-8000-000000000001','c3920000-0000-4000-8000-000000000001','gestor'),
 ('c3900000-0000-4000-8000-000000000002','c3920000-0000-4000-8000-000000000002','gestor');
insert into public.canais_loja(id,concessionaria_id,identificador_emissor) values
 ('c3930000-0000-4000-8000-000000000001','c3920000-0000-4000-8000-000000000001','037C_CH_A'),
 ('c3930000-0000-4000-8000-000000000002','c3920000-0000-4000-8000-000000000002','037C_CH_B');
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado) values
 ('c3940000-0000-4000-8000-000000000001','c3920000-0000-4000-8000-000000000001','+5581999013737'),
 ('c3940000-0000-4000-8000-000000000002','c3920000-0000-4000-8000-000000000001','+5581999023737'),
 ('c3940000-0000-4000-8000-000000000003','c3920000-0000-4000-8000-000000000002','+5581999013737');
insert into public.ciclos_comerciais(id,concessionaria_id,lead_id) values
 ('c3950000-0000-4000-8000-000000000001','c3920000-0000-4000-8000-000000000001','c3940000-0000-4000-8000-000000000001'),
 ('c3950000-0000-4000-8000-000000000002','c3920000-0000-4000-8000-000000000001','c3940000-0000-4000-8000-000000000002'),
 ('c3950000-0000-4000-8000-000000000003','c3920000-0000-4000-8000-000000000002','c3940000-0000-4000-8000-000000000003');
insert into public.catalogo_templates_sinteticos(id,concessionaria_id,codigo,versao) values
 ('c3960000-0000-4000-8000-000000000001','c3920000-0000-4000-8000-000000000001','037C_A',1),
 ('c3960000-0000-4000-8000-000000000002','c3920000-0000-4000-8000-000000000002','037C_B',1);
insert into public.planos_recontato_sinteticos(
 id,concessionaria_id,lead_id,ciclo_id,canal_id,chave_idempotencia,fingerprint) values
 ('c3970000-0000-4000-8000-000000000001','c3920000-0000-4000-8000-000000000001',
 'c3940000-0000-4000-8000-000000000001','c3950000-0000-4000-8000-000000000001',
 'c3930000-0000-4000-8000-000000000001','037C_C08_A',repeat('a',64)),
 ('c3970000-0000-4000-8000-000000000002','c3920000-0000-4000-8000-000000000001',
 'c3940000-0000-4000-8000-000000000002','c3950000-0000-4000-8000-000000000002',
 'c3930000-0000-4000-8000-000000000001','037C_C07_A',repeat('b',64)),
 ('c3970000-0000-4000-8000-000000000003','c3920000-0000-4000-8000-000000000002',
 'c3940000-0000-4000-8000-000000000003','c3950000-0000-4000-8000-000000000003',
 'c3930000-0000-4000-8000-000000000002','037C_B',repeat('c',64));
insert into public.envios_template_sinteticos(
 id,concessionaria_id,plano_id,template_id,ordem,agendado_em,
 estado,reservado_em,chave_idempotencia) values
 ('c3980000-0000-4000-8000-000000000001','c3920000-0000-4000-8000-000000000001',
 'c3970000-0000-4000-8000-000000000001','c3960000-0000-4000-8000-000000000001',
 1,statement_timestamp()+interval '1 day','programado',null,'037C_OUT_CANCEL'),
 ('c3980000-0000-4000-8000-000000000002','c3920000-0000-4000-8000-000000000001',
 'c3970000-0000-4000-8000-000000000002','c3960000-0000-4000-8000-000000000001',
 1,statement_timestamp()+interval '1 day','reservado',statement_timestamp(),'037C_OUT_LINK'),
 ('c3980000-0000-4000-8000-000000000003','c3920000-0000-4000-8000-000000000002',
 'c3970000-0000-4000-8000-000000000003','c3960000-0000-4000-8000-000000000002',
 1,statement_timestamp()+interval '1 day','programado',null,'037C_OUT_B');

-- All three callbacks are initially unknown, yielding SEM_CORRELACAO.
select prumo_private.registrar_callback_c07_sintetico(
 'c3930000-0000-4000-8000-000000000001',
 '037C.ENC','037C.EVENT.ENC','INCERTO_SIMULADO',statement_timestamp());
select prumo_private.registrar_callback_c07_sintetico(
 'c3930000-0000-4000-8000-000000000001',
 '037C.LINK','037C.EVENT.LINK','ENTREGUE_SIMULADO',statement_timestamp());
select prumo_private.registrar_callback_c07_sintetico(
 'c3930000-0000-4000-8000-000000000002',
 '037C.B','037C.EVENT.B','INCERTO_SIMULADO',statement_timestamp());
-- Deliberate delayed correlation, not a Meta/provider send. This makes the
-- human-only VINCULAR_SINTETICAMENTE branch executable in the fixture.
update public.envios_template_sinteticos set correlacao_externa_ficticia='037C.LINK'
where id='c3980000-0000-4000-8000-000000000002';

-- An in-memory test-only key; never a real signing or Graph secret.
insert into prumo_private.gateway_chaves_assinatura_s0(
 chave_id,segredo,valido_desde,valido_ate,ativo)
 values('c3990000-0000-4000-8000-000000000001',
 decode(repeat('c7',32),'hex'),statement_timestamp()-interval '1 hour',
 statement_timestamp()+interval '1 hour',false);
select prumo_private.alterar_estado_chave_gateway_s0(
 'c3990000-0000-4000-8000-000000000001',1,true,
 'Ativacao de chave exclusivamente ficticia S0 037C');

create function pg_temp.assinar_037c(
 p_operacao text,p_ator uuid,p_sessao uuid,p_loja uuid,p_alvo uuid,
 p_versao bigint,p_decisao text,p_justificativa text,p_envio uuid,
 p_emitido bigint,p_nonce uuid
) returns text language plpgsql security invoker set search_path='' as $sig$
declare v_schema text;v_bytes bytea;v_material text;
begin
 select n.nspname into v_schema from pg_catalog.pg_extension e
 join pg_catalog.pg_namespace n on n.oid=e.extnamespace where e.extname='pgcrypto';
 v_material:=prumo_private.gateway_material_assinatura_s0(
 p_operacao,p_ator,p_sessao,p_loja,p_alvo,p_versao,p_decisao,
 p_justificativa,p_envio,p_emitido,p_nonce);
 execute pg_catalog.format('select %I.hmac($1,$2,''sha256'')',v_schema)
 into v_bytes using pg_catalog.convert_to(v_material,'UTF8'),
 decode(repeat('c7',32),'hex');
 return pg_catalog.encode(v_bytes,'hex');
end $sig$;

-- Only fixture postgres computes signatures. The gateway receives string
-- proofs; it cannot read key material, auth.sessions or commercial tables.
select pg_catalog.set_config('prumo.test037c.issue',
 (extract(epoch from clock_timestamp())::bigint)::text,true);
select pg_catalog.set_config('prumo.test037c.pending_enc',(
 select p.id::text from public.pendencias_reconciliacao_c07_sinteticas p
 join public.eventos_callback_sinteticos e
  on e.concessionaria_id=p.concessionaria_id and e.id=p.evento_id
 where e.evento_externo_ficticio='037C.EVENT.ENC'),true);
select pg_catalog.set_config('prumo.test037c.pending_link',(
 select p.id::text from public.pendencias_reconciliacao_c07_sinteticas p
 join public.eventos_callback_sinteticos e
  on e.concessionaria_id=p.concessionaria_id and e.id=p.evento_id
 where e.evento_externo_ficticio='037C.EVENT.LINK'),true);
select pg_catalog.set_config('prumo.test037c.pending_b',(
 select p.id::text from public.pendencias_reconciliacao_c07_sinteticas p
 join public.eventos_callback_sinteticos e
  on e.concessionaria_id=p.concessionaria_id and e.id=p.evento_id
 where e.evento_externo_ficticio='037C.EVENT.B'),true);
select pg_catalog.set_config('prumo.test037c.sig_cancel',pg_temp.assinar_037c(
 'cancelar_plano','c3900000-0000-4000-8000-000000000001',
 'c3910000-0000-4000-8000-000000000001','c3920000-0000-4000-8000-000000000001',
 'c3970000-0000-4000-8000-000000000001',1,null,null,null,
 current_setting('prumo.test037c.issue')::bigint,'c39a0000-0000-4000-8000-000000000001'),true);
select pg_catalog.set_config('prumo.test037c.sig_cancel_again',pg_temp.assinar_037c(
 'cancelar_plano','c3900000-0000-4000-8000-000000000001',
 'c3910000-0000-4000-8000-000000000001','c3920000-0000-4000-8000-000000000001',
 'c3970000-0000-4000-8000-000000000001',1,null,null,null,
 current_setting('prumo.test037c.issue')::bigint,'c39a0000-0000-4000-8000-000000000002'),true);
select pg_catalog.set_config('prumo.test037c.sig_enc',pg_temp.assinar_037c(
 'conciliar_c07','c3900000-0000-4000-8000-000000000001',
 'c3910000-0000-4000-8000-000000000001','c3920000-0000-4000-8000-000000000001',
 current_setting('prumo.test037c.pending_enc')::uuid,1,
 'ENCERRAR_SEM_PROVA','Revisao ficticia de incerteza com justificativa suficiente',
 null,current_setting('prumo.test037c.issue')::bigint,
 'c39a0000-0000-4000-8000-000000000003'),true);
select pg_catalog.set_config('prumo.test037c.sig_link',pg_temp.assinar_037c(
 'conciliar_c07','c3900000-0000-4000-8000-000000000001',
 'c3910000-0000-4000-8000-000000000001','c3920000-0000-4000-8000-000000000001',
 current_setting('prumo.test037c.pending_link')::uuid,1,
 'VINCULAR_SINTETICAMENTE','Associacao ficticia conferida manualmente para teste',
 'c3980000-0000-4000-8000-000000000002',
 current_setting('prumo.test037c.issue')::bigint,
 'c39a0000-0000-4000-8000-000000000004'),true);
select pg_catalog.set_config('prumo.test037c.sig_cross',pg_temp.assinar_037c(
 'conciliar_c07','c3900000-0000-4000-8000-000000000001',
 'c3910000-0000-4000-8000-000000000001','c3920000-0000-4000-8000-000000000002',
 current_setting('prumo.test037c.pending_b')::uuid,1,'ENCERRAR_SEM_PROVA',
 'Revisao proibida de concessionaria B ficticia',null,
 current_setting('prumo.test037c.issue')::bigint,
 'c39a0000-0000-4000-8000-000000000005'),true);
select pg_catalog.set_config('prumo.test037c.sig_revoked',pg_temp.assinar_037c(
 'cancelar_plano','c3900000-0000-4000-8000-000000000001',
 'c3910000-0000-4000-8000-000000000001','c3920000-0000-4000-8000-000000000001',
 'c3970000-0000-4000-8000-000000000001',1,null,null,null,
 current_setting('prumo.test037c.issue')::bigint,
 'c39a0000-0000-4000-8000-000000000006'),true);

set local role prumo_s0_gateway;
do $gate$
declare v jsonb;
begin
 if has_table_privilege(current_user,'public.planos_recontato_sinteticos','UPDATE')
 or has_table_privilege(current_user,'prumo_private.auditoria_gateway_s0','INSERT')
 or has_function_privilege(current_user,
   'prumo_private.gateway_cancelar_plano_s0(uuid,uuid,uuid,uuid,bigint)','EXECUTE')
 then raise exception 'FAIL OWNER37C-01: bypass possible';end if;
 begin
  perform 1 from auth.sessions;
  raise exception 'FAIL OWNER37C-01: session directly readable';
 exception when insufficient_privilege then null;end;
 begin
  perform prumo_private.gateway_cancelar_plano_assinado_s0(
   'c3900000-0000-4000-8000-000000000001',
   'c3910000-0000-4000-8000-000000000001',
   'c3920000-0000-4000-8000-000000000001',
   'c3970000-0000-4000-8000-000000000001',1,
   'c3990000-0000-4000-8000-000000000001',
   current_setting('prumo.test037c.issue')::bigint,
   'c39a0000-0000-4000-8000-000000000007',repeat('0',64));
  raise exception 'FAIL OWNER37C-01: invalid HMAC accepted';
 exception when insufficient_privilege then
  if SQLERRM<>'PROVA_INVALIDA' then
   raise exception 'FAIL OWNER37C-01 unexpected HMAC rejection: %',SQLERRM;end if;
 end;
end $gate$;
\echo 'PASS OWNER37C-01: gateway cannot mutate directly or bypass invalid HMAC'

do $gate$
declare v jsonb;
begin
 v:=prumo_private.gateway_cancelar_plano_assinado_s0(
  'c3900000-0000-4000-8000-000000000001',
  'c3910000-0000-4000-8000-000000000001','c3920000-0000-4000-8000-000000000001',
  'c3970000-0000-4000-8000-000000000001',1,
  'c3990000-0000-4000-8000-000000000001',
  current_setting('prumo.test037c.issue')::bigint,
  'c39a0000-0000-4000-8000-000000000001',current_setting('prumo.test037c.sig_cancel'));
 if v->>'outcome'<>'APPLIED' then raise exception 'FAIL OWNER37C-02 cancel';end if;
 begin
  perform prumo_private.gateway_cancelar_plano_assinado_s0(
   'c3900000-0000-4000-8000-000000000001',
   'c3910000-0000-4000-8000-000000000001','c3920000-0000-4000-8000-000000000001',
   'c3970000-0000-4000-8000-000000000001',1,
   'c3990000-0000-4000-8000-000000000001',
   current_setting('prumo.test037c.issue')::bigint,
   'c39a0000-0000-4000-8000-000000000001',current_setting('prumo.test037c.sig_cancel'));
  raise exception 'FAIL OWNER37C-02 replay nonce accepted';
 exception when insufficient_privilege then null;end;
 v:=prumo_private.gateway_cancelar_plano_assinado_s0(
  'c3900000-0000-4000-8000-000000000001',
  'c3910000-0000-4000-8000-000000000001','c3920000-0000-4000-8000-000000000001',
  'c3970000-0000-4000-8000-000000000001',1,
  'c3990000-0000-4000-8000-000000000001',
  current_setting('prumo.test037c.issue')::bigint,
  'c39a0000-0000-4000-8000-000000000002',current_setting('prumo.test037c.sig_cancel_again'));
 if v->>'outcome'<>'ALREADY_APPLIED'
 then raise exception 'FAIL OWNER37C-02 idempotency';end if;
end $gate$;
\echo 'PASS OWNER37C-02: C08 signed, single-use nonce, idempotency'

do $gate$
declare v jsonb;
begin
 v:=prumo_private.gateway_conciliar_c07_assinado_s0(
  'c3900000-0000-4000-8000-000000000001',
  'c3910000-0000-4000-8000-000000000001','c3920000-0000-4000-8000-000000000001',
  current_setting('prumo.test037c.pending_enc')::uuid,1,
  'ENCERRAR_SEM_PROVA','Revisao ficticia de incerteza com justificativa suficiente',null,
  'c3990000-0000-4000-8000-000000000001',
  current_setting('prumo.test037c.issue')::bigint,
  'c39a0000-0000-4000-8000-000000000003',current_setting('prumo.test037c.sig_enc'));
 if v->>'outcome'<>'APPLIED' then raise exception 'FAIL OWNER37C-03 close';end if;
 v:=prumo_private.gateway_conciliar_c07_assinado_s0(
  'c3900000-0000-4000-8000-000000000001',
  'c3910000-0000-4000-8000-000000000001','c3920000-0000-4000-8000-000000000001',
  current_setting('prumo.test037c.pending_link')::uuid,1,
  'VINCULAR_SINTETICAMENTE','Associacao ficticia conferida manualmente para teste',
  'c3980000-0000-4000-8000-000000000002',
  'c3990000-0000-4000-8000-000000000001',
  current_setting('prumo.test037c.issue')::bigint,
  'c39a0000-0000-4000-8000-000000000004',current_setting('prumo.test037c.sig_link'));
 if v->>'outcome'<>'APPLIED' then raise exception 'FAIL OWNER37C-03 link';end if;
 begin
  perform prumo_private.gateway_conciliar_c07_assinado_s0(
   'c3900000-0000-4000-8000-000000000001',
   'c3910000-0000-4000-8000-000000000001','c3920000-0000-4000-8000-000000000002',
   current_setting('prumo.test037c.pending_b')::uuid,1,
   'ENCERRAR_SEM_PROVA','Revisao proibida de concessionaria B ficticia',null,
   'c3990000-0000-4000-8000-000000000001',
   current_setting('prumo.test037c.issue')::bigint,
   'c39a0000-0000-4000-8000-000000000005',current_setting('prumo.test037c.sig_cross'));
  raise exception 'FAIL OWNER37C-03 cross store accepted';
 exception when insufficient_privilege then
  if SQLERRM<>'FORBIDDEN_SCOPE' then
   raise exception 'FAIL OWNER37C-03 unexpected scope rejection: %',SQLERRM;end if;
 end;
end $gate$;
\echo 'PASS OWNER37C-03: C07 both human decisions, cross-store denies'

reset role;
do $check$
begin
 if (select count(*) from prumo_private.auditoria_gateway_s0
  where concessionaria_id='c3920000-0000-4000-8000-000000000001')<>4
 or (select count(*) from prumo_private.gateway_provas_usadas_s0
  where chave_id='c3990000-0000-4000-8000-000000000001')<>4
 or (select count(*) from public.associacoes_callback_c07_sinteticas
  where concessionaria_id='c3920000-0000-4000-8000-000000000001')<>1
 or (select count(*) from public.auditoria_reconciliacao_c07_sintetica
  where concessionaria_id='c3920000-0000-4000-8000-000000000001')<>2
 or (select count(*) from public.eventos_envio_template_sinteticos
  where concessionaria_id='c3920000-0000-4000-8000-000000000001'
   and motivo='cancelamento_gestor')<>1
 or (select count(*) from public.planos_recontato_sinteticos
  where id='c3970000-0000-4000-8000-000000000001' and estado='cancelado')<>1
 or (select count(*) from public.envios_template_sinteticos
  where id='c3980000-0000-4000-8000-000000000001' and estado='cancelado')<>1
 or (select count(*) from public.pendencias_reconciliacao_c07_sinteticas
  where concessionaria_id='c3920000-0000-4000-8000-000000000002' and estado='pendente')<>1
 or (select count(*) from public.ciclos_comerciais
  where concessionaria_id='c3920000-0000-4000-8000-000000000001'
   and status_comercial='aguardando primeiro disparo')<>2
 then raise exception 'FAIL OWNER37C-04 audit, rollback on denial or commercial invariants';end if;
end $check$;
\echo 'PASS OWNER37C-04: signed chain commits audit/nonce/domain once; no B effect or state change'

-- AUD-037: adversarial coverage missing from the first 037C acceptance.
-- Compute test proofs as postgres, NEVER through the restricted SQL role.
select pg_catalog.set_config('prumo.test037c.sig_wrong_session',pg_temp.assinar_037c(
 'cancelar_plano','c3900000-0000-4000-8000-000000000001',
 'c3910000-0000-4000-8000-000000000002','c3920000-0000-4000-8000-000000000001',
 'c3970000-0000-4000-8000-000000000001',1,null,null,null,
 current_setting('prumo.test037c.issue')::bigint,
 'c39a0000-0000-4000-8000-000000000011'),true);
select pg_catalog.set_config('prumo.test037c.sig_wrong_actor_scope',pg_temp.assinar_037c(
 'cancelar_plano','c3900000-0000-4000-8000-000000000002',
 'c3910000-0000-4000-8000-000000000002','c3920000-0000-4000-8000-000000000001',
 'c3970000-0000-4000-8000-000000000001',1,null,null,null,
 current_setting('prumo.test037c.issue')::bigint,
 'c39a0000-0000-4000-8000-000000000012'),true);
select pg_catalog.set_config('prumo.test037c.sig_c07_same',pg_temp.assinar_037c(
 'conciliar_c07','c3900000-0000-4000-8000-000000000001',
 'c3910000-0000-4000-8000-000000000001','c3920000-0000-4000-8000-000000000001',
 current_setting('prumo.test037c.pending_link')::uuid,1,
 'VINCULAR_SINTETICAMENTE','Associacao ficticia conferida manualmente para teste',
 'c3980000-0000-4000-8000-000000000002',
 current_setting('prumo.test037c.issue')::bigint,
 'c39a0000-0000-4000-8000-000000000013'),true);
select pg_catalog.set_config('prumo.test037c.sig_c07_conflict',pg_temp.assinar_037c(
 'conciliar_c07','c3900000-0000-4000-8000-000000000001',
 'c3910000-0000-4000-8000-000000000001','c3920000-0000-4000-8000-000000000001',
 current_setting('prumo.test037c.pending_link')::uuid,1,
 'ENCERRAR_SEM_PROVA','Decisao divergente assinada de teste sem prova real',
 null,current_setting('prumo.test037c.issue')::bigint,
 'c39a0000-0000-4000-8000-000000000014'),true);

set local role prumo_s0_gateway;
do $audit$
begin
 begin
  perform prumo_private.gateway_cancelar_plano_assinado_s0(
   'c3900000-0000-4000-8000-000000000001',
   'c3910000-0000-4000-8000-000000000002',
   'c3920000-0000-4000-8000-000000000001',
   'c3970000-0000-4000-8000-000000000001',1,
   'c3990000-0000-4000-8000-000000000001',
   current_setting('prumo.test037c.issue')::bigint,
   'c39a0000-0000-4000-8000-000000000011',
   current_setting('prumo.test037c.sig_wrong_session'));
  raise exception 'FAIL AUD37-01: accepted session of another actor';
 exception when insufficient_privilege then
  if SQLERRM<>'SESSAO_INATIVA' then
   raise exception 'FAIL AUD37-01 wrong rejection: %',SQLERRM;end if;
 end;
 begin
  perform prumo_private.gateway_cancelar_plano_assinado_s0(
   'c3900000-0000-4000-8000-000000000002',
   'c3910000-0000-4000-8000-000000000002',
   'c3920000-0000-4000-8000-000000000001',
   'c3970000-0000-4000-8000-000000000001',1,
   'c3990000-0000-4000-8000-000000000001',
   current_setting('prumo.test037c.issue')::bigint,
   'c39a0000-0000-4000-8000-000000000012',
   current_setting('prumo.test037c.sig_wrong_actor_scope'));
  raise exception 'FAIL AUD37-01: B manager updated A';
 exception when insufficient_privilege then
  if SQLERRM<>'FORBIDDEN_SCOPE' then
   raise exception 'FAIL AUD37-01 wrong scope denial: %',SQLERRM;end if;
 end;
end $audit$;
\echo 'PASS AUD37-01: valid HMAC not sufficient for mismatched actor/session or cross-store gestor'

do $audit$
declare v jsonb;
begin
 v:=prumo_private.gateway_conciliar_c07_assinado_s0(
  'c3900000-0000-4000-8000-000000000001',
  'c3910000-0000-4000-8000-000000000001',
  'c3920000-0000-4000-8000-000000000001',
  current_setting('prumo.test037c.pending_link')::uuid,1,
  'VINCULAR_SINTETICAMENTE','Associacao ficticia conferida manualmente para teste',
  'c3980000-0000-4000-8000-000000000002',
  'c3990000-0000-4000-8000-000000000001',
  current_setting('prumo.test037c.issue')::bigint,
  'c39a0000-0000-4000-8000-000000000013',
  current_setting('prumo.test037c.sig_c07_same'));
 if v->>'outcome'<>'ALREADY_APPLIED'
 then raise exception 'FAIL AUD37-02 C07 same-request idempotency';end if;
 begin
  perform prumo_private.gateway_conciliar_c07_assinado_s0(
   'c3900000-0000-4000-8000-000000000001',
   'c3910000-0000-4000-8000-000000000001',
   'c3920000-0000-4000-8000-000000000001',
   current_setting('prumo.test037c.pending_link')::uuid,1,
   'ENCERRAR_SEM_PROVA','Decisao divergente assinada de teste sem prova real',
   null,'c3990000-0000-4000-8000-000000000001',
   current_setting('prumo.test037c.issue')::bigint,
   'c39a0000-0000-4000-8000-000000000014',
   current_setting('prumo.test037c.sig_c07_conflict'));
  raise exception 'FAIL AUD37-02 differing C07 replay accepted';
 exception when serialization_failure then
  if SQLERRM<>'CONFLICT_VERSION' then
   raise exception 'FAIL AUD37-02 wrong version rejection: %',SQLERRM;end if;
 end;
end $audit$;
\echo 'PASS AUD37-02: identical C07 decision idempotent; changed decision conflicts on version'
reset role;
do $audit$
begin
 if (select count(*) from prumo_private.gateway_provas_usadas_s0
      where chave_id='c3990000-0000-4000-8000-000000000001')<>5
 or (select count(*) from prumo_private.auditoria_gateway_s0
      where concessionaria_id='c3920000-0000-4000-8000-000000000001')<>5
 or (select count(*) from public.auditoria_reconciliacao_c07_sintetica
      where concessionaria_id='c3920000-0000-4000-8000-000000000001')<>2
 or (select count(*) from public.associacoes_callback_c07_sinteticas
      where concessionaria_id='c3920000-0000-4000-8000-000000000001')<>1
 then raise exception 'FAIL AUD37-03 nonce, private audit, C07 domain audit inconsistent';end if;
end $audit$;
\echo 'PASS AUD37-03: failed signed attempts rollback nonce; C07 replay does not duplicate domain events'

-- S0-037E / AUTHATOM: inject a failure AFTER successful domain DML,
-- exactly when the private gateway audit would be inserted. The signed
-- command must fail as a unit (including HMAC nonce); retry with the SAME
-- valid proof after removing the fault must succeed. ALL in outer ROLLBACK.
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado)
values('c39b0000-0000-4000-8000-000000000001',
       'c3920000-0000-4000-8000-000000000001','+5581999033737');
insert into public.ciclos_comerciais(id,concessionaria_id,lead_id)
values('c39b0000-0000-4000-8000-000000000002',
       'c3920000-0000-4000-8000-000000000001',
       'c39b0000-0000-4000-8000-000000000001');
insert into public.planos_recontato_sinteticos(
 id,concessionaria_id,lead_id,ciclo_id,canal_id,chave_idempotencia,fingerprint)
values('c39b0000-0000-4000-8000-000000000003',
       'c3920000-0000-4000-8000-000000000001',
       'c39b0000-0000-4000-8000-000000000001',
       'c39b0000-0000-4000-8000-000000000002',
       'c3930000-0000-4000-8000-000000000001',
       'AUTHATOM_C08',repeat('d',64));
insert into public.envios_template_sinteticos(
 id,concessionaria_id,plano_id,template_id,ordem,agendado_em,
 estado,chave_idempotencia)
values('c39b0000-0000-4000-8000-000000000004',
       'c3920000-0000-4000-8000-000000000001',
       'c39b0000-0000-4000-8000-000000000003',
       'c3960000-0000-4000-8000-000000000001',
       1,statement_timestamp()+interval '1 day',
       'programado','AUTHATOM_C08_SEND');
select prumo_private.registrar_callback_c07_sintetico(
 'c3930000-0000-4000-8000-000000000001',
 'AUTHATOM.UNKNOWN','AUTHATOM.EVENT','INCERTO_SIMULADO',statement_timestamp());
select pg_catalog.set_config('prumo.test037e.pending',(
 select p.id::text from public.pendencias_reconciliacao_c07_sinteticas p
 join public.eventos_callback_sinteticos e
  on e.concessionaria_id=p.concessionaria_id and e.id=p.evento_id
 where e.evento_externo_ficticio='AUTHATOM.EVENT'),true);

select pg_catalog.set_config('prumo.test037e.sig_c08',pg_temp.assinar_037c(
 'cancelar_plano','c3900000-0000-4000-8000-000000000001',
 'c3910000-0000-4000-8000-000000000001',
 'c3920000-0000-4000-8000-000000000001',
 'c39b0000-0000-4000-8000-000000000003',1,null,null,null,
 current_setting('prumo.test037c.issue')::bigint,
 'c39b0000-0000-4000-8000-000000000005'),true);
select pg_catalog.set_config('prumo.test037e.sig_c07',pg_temp.assinar_037c(
 'conciliar_c07','c3900000-0000-4000-8000-000000000001',
 'c3910000-0000-4000-8000-000000000001',
 'c3920000-0000-4000-8000-000000000001',
 current_setting('prumo.test037e.pending')::uuid,1,
 'ENCERRAR_SEM_PROVA',
 'Auditoria indisponivel durante conciliação ficticia de teste',
 null,current_setting('prumo.test037c.issue')::bigint,
 'c39b0000-0000-4000-8000-000000000006'),true);

create function pg_temp.bloquear_auditoria_037e()
returns trigger language plpgsql security invoker set search_path='' as $fault$
begin
 raise exception 'AUDITORIA_INDISPONIVEL_FIXTURE' using errcode='P0001';
end $fault$;
create trigger audit_fault_037e before insert
on prumo_private.auditoria_gateway_s0 for each row
execute function pg_temp.bloquear_auditoria_037e();

set local role prumo_s0_gateway;
do $fault$
begin
 begin
  perform prumo_private.gateway_cancelar_plano_assinado_s0(
   'c3900000-0000-4000-8000-000000000001',
   'c3910000-0000-4000-8000-000000000001',
   'c3920000-0000-4000-8000-000000000001',
   'c39b0000-0000-4000-8000-000000000003',1,
   'c3990000-0000-4000-8000-000000000001',
   current_setting('prumo.test037c.issue')::bigint,
   'c39b0000-0000-4000-8000-000000000005',
   current_setting('prumo.test037e.sig_c08'));
  raise exception 'FAIL AUTHATOM-01: signed C08 accepted without audit';
 exception when raise_exception then
  if SQLERRM<>'AUDITORIA_INDISPONIVEL_FIXTURE' then
   raise exception 'FAIL AUTHATOM-01: unexpected exception %',SQLERRM;end if;
 end;
 begin
  perform prumo_private.gateway_conciliar_c07_assinado_s0(
   'c3900000-0000-4000-8000-000000000001',
   'c3910000-0000-4000-8000-000000000001',
   'c3920000-0000-4000-8000-000000000001',
   current_setting('prumo.test037e.pending')::uuid,1,
   'ENCERRAR_SEM_PROVA',
   'Auditoria indisponivel durante conciliação ficticia de teste',null,
   'c3990000-0000-4000-8000-000000000001',
   current_setting('prumo.test037c.issue')::bigint,
   'c39b0000-0000-4000-8000-000000000006',
   current_setting('prumo.test037e.sig_c07'));
  raise exception 'FAIL AUTHATOM-01: signed C07 accepted without audit';
 exception when raise_exception then
  if SQLERRM<>'AUDITORIA_INDISPONIVEL_FIXTURE' then
   raise exception 'FAIL AUTHATOM-01: unexpected exception %',SQLERRM;end if;
 end;
end $fault$;
reset role;

do $assert$
begin
 if not exists(select 1 from public.planos_recontato_sinteticos
   where id='c39b0000-0000-4000-8000-000000000003'
   and estado='ativo' and versao=1)
 or not exists(select 1 from public.envios_template_sinteticos
   where id='c39b0000-0000-4000-8000-000000000004' and estado='programado')
 or not exists(select 1 from public.pendencias_reconciliacao_c07_sinteticas
   where id=current_setting('prumo.test037e.pending')::uuid
   and estado='pendente' and versao=1)
 or (select count(*) from public.eventos_envio_template_sinteticos
   where envio_id='c39b0000-0000-4000-8000-000000000004')<>0
 or (select count(*) from public.auditoria_reconciliacao_c07_sintetica
   where pendencia_id=current_setting('prumo.test037e.pending')::uuid)<>0
 or (select count(*) from prumo_private.gateway_provas_usadas_s0
   where nonce in ('c39b0000-0000-4000-8000-000000000005',
                   'c39b0000-0000-4000-8000-000000000006'))<>0
 or (select count(*) from prumo_private.auditoria_gateway_s0
   where alvo_id in ('c39b0000-0000-4000-8000-000000000003',
    current_setting('prumo.test037e.pending')::uuid))<>0
 then raise exception 'FAIL AUTHATOM-02: failure did not rollback domain/audit/nonce';end if;
end $assert$;
\echo 'PASS AUTHATOM-01/02: audit injection refused C08/C07; domain and HMAC nonce rolled back'

drop trigger audit_fault_037e on prumo_private.auditoria_gateway_s0;
set local role prumo_s0_gateway;
do $retry$
declare v jsonb;
begin
 v:=prumo_private.gateway_cancelar_plano_assinado_s0(
   'c3900000-0000-4000-8000-000000000001',
   'c3910000-0000-4000-8000-000000000001',
   'c3920000-0000-4000-8000-000000000001',
   'c39b0000-0000-4000-8000-000000000003',1,
   'c3990000-0000-4000-8000-000000000001',
   current_setting('prumo.test037c.issue')::bigint,
   'c39b0000-0000-4000-8000-000000000005',
   current_setting('prumo.test037e.sig_c08'));
 if v->>'outcome'<>'APPLIED' then
  raise exception 'FAIL AUTHATOM-03: C08 retry not applied';end if;
 v:=prumo_private.gateway_conciliar_c07_assinado_s0(
   'c3900000-0000-4000-8000-000000000001',
   'c3910000-0000-4000-8000-000000000001',
   'c3920000-0000-4000-8000-000000000001',
   current_setting('prumo.test037e.pending')::uuid,1,
   'ENCERRAR_SEM_PROVA',
   'Auditoria indisponivel durante conciliação ficticia de teste',null,
   'c3990000-0000-4000-8000-000000000001',
   current_setting('prumo.test037c.issue')::bigint,
   'c39b0000-0000-4000-8000-000000000006',
   current_setting('prumo.test037e.sig_c07'));
 if v->>'outcome'<>'APPLIED' then
  raise exception 'FAIL AUTHATOM-03: C07 retry not applied';end if;
end $retry$;
reset role;
do $done$
begin
 if (select count(*) from prumo_private.gateway_provas_usadas_s0
   where nonce in ('c39b0000-0000-4000-8000-000000000005',
                   'c39b0000-0000-4000-8000-000000000006'))<>2
 or (select count(*) from prumo_private.auditoria_gateway_s0
   where alvo_id in ('c39b0000-0000-4000-8000-000000000003',
      current_setting('prumo.test037e.pending')::uuid))<>2
 or (select count(*) from public.eventos_envio_template_sinteticos
   where envio_id='c39b0000-0000-4000-8000-000000000004'
   and motivo='cancelamento_gestor')<>1
 or (select count(*) from public.auditoria_reconciliacao_c07_sintetica
   where pendencia_id=current_setting('prumo.test037e.pending')::uuid)<>1
 or (select count(*) from public.pendencias_reconciliacao_c07_sinteticas
   where id=current_setting('prumo.test037e.pending')::uuid and estado='encerrada')<>1
 or (select count(*) from public.planos_recontato_sinteticos
   where id='c39b0000-0000-4000-8000-000000000003' and estado='cancelado')<>1
 then raise exception 'FAIL AUTHATOM-03: after repair, atomic results or counts differ';end if;
end $done$;
\echo 'PASS AUTHATOM-03: original proof reusable after audit outage; C08 and C07 each commit once'

-- Revoke session after successful effects. A valid fresh proof must NOT
-- increment nonce/audit counters, nor revive an already-cancelled plan.
delete from auth.sessions
 where id='c3910000-0000-4000-8000-000000000001';
set local role prumo_s0_gateway;
do $rev$
begin
 begin
  perform prumo_private.gateway_cancelar_plano_assinado_s0(
   'c3900000-0000-4000-8000-000000000001',
   'c3910000-0000-4000-8000-000000000001','c3920000-0000-4000-8000-000000000001',
   'c3970000-0000-4000-8000-000000000001',1,
   'c3990000-0000-4000-8000-000000000001',
   current_setting('prumo.test037c.issue')::bigint,
   'c39a0000-0000-4000-8000-000000000006',current_setting('prumo.test037c.sig_revoked'));
  raise exception 'FAIL OWNER37C-05 revoked session allowed';
 exception when insufficient_privilege then
  if SQLERRM<>'SESSAO_INATIVA'
  then raise exception 'FAIL OWNER37C-05 incorrect rejection: %',SQLERRM;end if;
 end;
end $rev$;
reset role;
do $final$
begin
 if (select count(*) from prumo_private.auditoria_gateway_s0
  where concessionaria_id='c3920000-0000-4000-8000-000000000001')<>7
 or (select count(*) from prumo_private.gateway_provas_usadas_s0
  where chave_id='c3990000-0000-4000-8000-000000000001')<>7
 then raise exception 'FAIL OWNER37C-05 invalid/revoked proof persisted effects';end if;
 if not exists(select 1 from public.planos_recontato_sinteticos
  where id='c3970000-0000-4000-8000-000000000003'
  and concessionaria_id='c3920000-0000-4000-8000-000000000002'
  and estado='ativo')
 then raise exception 'FAIL OWNER37C-05 B plan changed';end if;
end $final$;
\echo 'PASS OWNER37C-05: GoTrue-session revocation blocks signed operations atomically'
rollback;
