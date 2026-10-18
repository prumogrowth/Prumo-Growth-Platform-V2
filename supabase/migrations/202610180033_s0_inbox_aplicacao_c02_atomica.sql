-- S0/033: C02-only atomic application of synthetic inbox fixtures.
-- No actual Meta inbound, no C07 callback adapter and no HTTP ACK.
-- Existing commercial C02 implementation and S0/032 lifecycle are reused.
create table prumo_private.inbox_c02_fixture_s0 (
 inbox_id uuid primary key,
 concessionaria_id uuid not null,
 canal_id uuid not null,
 telefone_sintetico text not null
  check(telefone_sintetico ~ '^\+[1-9][0-9]{9,14}$'),
 id_externo_sintetico text not null
  check(id_externo_sintetico ~ '^[A-Za-z0-9_.:-]{1,100}$'),
 texto_sintetico text not null
  check(length(btrim(texto_sintetico)) between 1 and 1024),
 mobile_confirmado_fixture boolean not null,
 criado_em timestamptz not null default pg_catalog.clock_timestamp(),
 foreign key(concessionaria_id,inbox_id)
  references prumo_private.inbox_eventos_s0(concessionaria_id,id),
 foreign key(concessionaria_id,canal_id)
  references public.canais_loja(concessionaria_id,id)
);
create table prumo_private.aplicacoes_c02_inbox_s0 (
 inbox_id uuid primary key,
 concessionaria_id uuid not null,
 canal_id uuid not null,
 mensagem_id uuid not null,
 worker_fixture uuid not null,
 versao_reserva bigint not null check(versao_reserva>=2),
 resultado_c02 text not null check(resultado_c02 in ('APPLIED','ALREADY_APPLIED')),
 aplicado_em timestamptz not null default pg_catalog.clock_timestamp(),
 unique(concessionaria_id,mensagem_id),
 foreign key(concessionaria_id,inbox_id)
   references prumo_private.inbox_eventos_s0(concessionaria_id,id),
 foreign key(concessionaria_id,mensagem_id)
   references public.mensagens(concessionaria_id,id),
 foreign key(concessionaria_id,canal_id)
   references public.canais_loja(concessionaria_id,id)
);
alter table prumo_private.inbox_c02_fixture_s0 enable row level security;
alter table prumo_private.aplicacoes_c02_inbox_s0 enable row level security;
revoke all on prumo_private.inbox_c02_fixture_s0,
 prumo_private.aplicacoes_c02_inbox_s0
 from public,anon,authenticated,service_role,prumo_s0_gateway,prumo_s0_signer;

-- Fixture-only annotation before task reservation. The original Meta
-- envelope is not transported: only the limited marker from S0/030 qualifies.
create function prumo_private.anexar_fixture_c02_s0(
 p_loja uuid,p_canal uuid,p_inbox uuid,p_telefone text,
 p_id_externo text,p_texto text,p_mobile boolean
) returns jsonb language plpgsql security invoker set search_path='' as $fn$
declare v_t record;v_old record;
begin
 if current_user<>'postgres' then
  raise exception 'INTERNAL_ONLY' using errcode='42501';end if;
 if p_loja is null or p_canal is null or p_inbox is null
 or p_telefone is null or p_telefone !~ '^\+[1-9][0-9]{9,14}$'
 or p_id_externo is null or p_id_externo !~ '^[A-Za-z0-9_.:-]{1,100}$'
 or p_texto is null or length(btrim(p_texto)) not between 1 and 1024
 or p_mobile is null
 then raise exception 'INVALID_C02_FIXTURE' using errcode='22023';end if;
 select t.estado,t.versao into v_t
 from prumo_private.tarefas_ingresso_s0 t
 join prumo_private.inbox_eventos_s0 i
  on i.id=t.inbox_id and i.concessionaria_id=t.concessionaria_id
 join public.canais_loja c on c.id=i.canal_id and c.concessionaria_id=i.concessionaria_id
 join public.concessionarias l on l.id=i.concessionaria_id
 where t.concessionaria_id=p_loja and i.canal_id=p_canal and t.inbox_id=p_inbox
  and i.tipo='inbound_message' and i.payload_fixture_s0 is not null
  and i.app_fixture_ref is not null and i.provider_message_id_s0=p_id_externo
  and i.chave_evento='in:'||p_id_externo
  and c.modo='simulado' and l.ativo
 for update of t;
 if not found then
  raise exception 'MISSING_AUTHENTICATED_FIXTURE_SCOPE' using errcode='42501';end if;
 select * into v_old from prumo_private.inbox_c02_fixture_s0
 where concessionaria_id=p_loja and inbox_id=p_inbox;
 if found then
  if v_old.canal_id is distinct from p_canal
   or v_old.telefone_sintetico is distinct from p_telefone
   or v_old.id_externo_sintetico is distinct from p_id_externo
   or v_old.texto_sintetico is distinct from p_texto
   or v_old.mobile_confirmado_fixture is distinct from p_mobile
  then raise exception 'CONFLICT_IDEMPOTENCY_KEY' using errcode='23505';end if;
  return pg_catalog.jsonb_build_object('outcome','ALREADY_ATTACHED');
 end if;
 if v_t.estado<>'READY' or v_t.versao<>1
 then raise exception 'FIXTURE_AFTER_CLAIM_FORBIDDEN' using errcode='40001';end if;
 insert into prumo_private.inbox_c02_fixture_s0(
  concessionaria_id,canal_id,inbox_id,telefone_sintetico,
  id_externo_sintetico,texto_sintetico,mobile_confirmado_fixture)
 values(p_loja,p_canal,p_inbox,p_telefone,p_id_externo,p_texto,p_mobile);
 return pg_catalog.jsonb_build_object('outcome','FIXTURE_ATTACHED');
end $fn$;

-- The C02 domain mutation and the inbox settlement share ONE SQL transaction.
-- Any SQL error (including identity ambiguity or expired lease) rolls back both.
create function prumo_private.aplicar_inbox_c02_s0(
 p_loja uuid,p_canal uuid,p_inbox uuid,p_worker uuid,p_versao bigint
) returns jsonb language plpgsql security invoker set search_path='' as $fn$
declare v_job record;v_old record;v_c02 jsonb;v_settle jsonb;v_msg uuid;
begin
 if current_user<>'postgres' then
  raise exception 'INTERNAL_ONLY' using errcode='42501';end if;
 if p_loja is null or p_canal is null or p_inbox is null
 or p_worker is null or p_versao is null or p_versao<2
 then raise exception 'INVALID_C02_APPLY_ARGS' using errcode='22023';end if;
 select t.estado,t.versao,t.lease_worker,t.lease_ate,
  f.telefone_sintetico,f.id_externo_sintetico,f.texto_sintetico,
  f.mobile_confirmado_fixture
 into v_job
 from prumo_private.tarefas_ingresso_s0 t
 join prumo_private.inbox_eventos_s0 i
  on i.id=t.inbox_id and i.concessionaria_id=t.concessionaria_id
 join prumo_private.inbox_c02_fixture_s0 f
  on f.inbox_id=i.id and f.concessionaria_id=i.concessionaria_id
  and f.canal_id=i.canal_id
 join public.canais_loja c on c.id=i.canal_id and c.concessionaria_id=i.concessionaria_id
 join public.concessionarias l on l.id=i.concessionaria_id
 where t.concessionaria_id=p_loja and t.inbox_id=p_inbox
  and i.canal_id=p_canal and i.tipo='inbound_message'
  and i.payload_fixture_s0 is not null and i.app_fixture_ref is not null
  and i.provider_message_id_s0=f.id_externo_sintetico
  and i.chave_evento='in:'||f.id_externo_sintetico
  and c.modo='simulado' and l.ativo
 for update of t;
 if not found then
  raise exception 'INVALID_C02_APPLY_SCOPE' using errcode='42501';end if;
 select * into v_old from prumo_private.aplicacoes_c02_inbox_s0
 where concessionaria_id=p_loja and inbox_id=p_inbox;
 if found then
  if v_job.estado='APPLIED' and v_old.canal_id=p_canal
   and v_old.worker_fixture=p_worker and v_old.versao_reserva=p_versao
  then return pg_catalog.jsonb_build_object('outcome','ALREADY_APPLIED',
   'mensagem_id',v_old.mensagem_id);end if;
  raise exception 'STALE_OR_DIFFERENT_APPLY' using errcode='40001';
 end if;
 if v_job.estado<>'LEASED' or v_job.versao<>p_versao
  or v_job.lease_worker is distinct from p_worker
  or v_job.lease_ate<=pg_catalog.clock_timestamp()
 then raise exception 'STALE_OR_EXPIRED_LEASE' using errcode='40001';end if;

 v_c02:=prumo_private.receber_mensagem_identidade_s0(
  p_canal,v_job.telefone_sintetico,v_job.id_externo_sintetico,
  v_job.texto_sintetico,v_job.mobile_confirmado_fixture);
 -- An unresolved identity may be reviewed through the S0/032 quarantine flow.
 -- Never mark C02 as applied when it created only an identity pending item.
 if v_c02->>'outcome' not in ('APPLIED','ALREADY_APPLIED')
   or v_c02->>'mensagem_id' is null
 then raise exception 'C02_REVIEW_REQUIRED_NO_SETTLEMENT' using errcode='22023';end if;
 v_msg:=(v_c02->>'mensagem_id')::uuid;
 v_settle:=prumo_private.registrar_resultado_ingresso_s0(
  p_loja,p_canal,p_inbox,p_worker,p_versao,'APLICADO_SINTETICO');
 if v_settle->>'outcome'<>'RECORDED' or v_settle->>'estado'<>'APPLIED'
 then raise exception 'C02_SETTLEMENT_REJECTED' using errcode='40001';end if;
 insert into prumo_private.aplicacoes_c02_inbox_s0(
  concessionaria_id,canal_id,inbox_id,mensagem_id,worker_fixture,
  versao_reserva,resultado_c02)
 values(p_loja,p_canal,p_inbox,v_msg,p_worker,p_versao,v_c02->>'outcome');
 return pg_catalog.jsonb_build_object(
  'outcome','APPLIED_ATOMIC','mensagem_id',v_msg,
  'c02_outcome',v_c02->>'outcome','tarefa_versao',v_settle->>'versao',
  'roteamento',v_c02->>'roteamento');
end $fn$;

revoke all on function prumo_private.anexar_fixture_c02_s0(
 uuid,uuid,uuid,text,text,text,boolean),
 prumo_private.aplicar_inbox_c02_s0(uuid,uuid,uuid,uuid,bigint)
 from public,anon,authenticated,service_role,prumo_s0_gateway,prumo_s0_signer;
