-- S0/029 DEC-WA-03: durable SYNTHETIC inbox and processing outbox.
-- Database-only internal prototype; no Meta credential, Graph API or RPC.
-- The service interface is PostgreSQL postgres-only until explicit IAM gates.
create table prumo_private.inbox_eventos_s0(
 id uuid primary key default gen_random_uuid(),
 concessionaria_id uuid not null,
 canal_id uuid not null,
 tipo text not null check(tipo in ('inbound_message','status_callback')),
 chave_evento text not null check(length(chave_evento) between 1 and 160),
 fingerprint_sintetico text not null check(fingerprint_sintetico ~ '^[a-f0-9]{64}$'),
 recebido_em timestamptz not null default clock_timestamp(),
 unique(concessionaria_id,canal_id,tipo,chave_evento),
 unique(concessionaria_id,id),
 foreign key(concessionaria_id,canal_id) references public.canais_loja(concessionaria_id,id)
);
create table prumo_private.tarefas_ingresso_s0(
 inbox_id uuid primary key,
 concessionaria_id uuid not null,
 estado text not null default 'READY'
  check(estado in ('READY','LEASED','APPLIED','RETRY_PENDING','DEAD_LETTER','QUARANTINED')),
 versao bigint not null default 1 check(versao>0),
 lease_worker uuid,
 lease_ate timestamptz,
 tentativas integer not null default 0 check(tentativas>=0),
 criado_em timestamptz not null default clock_timestamp(),
 foreign key(concessionaria_id,inbox_id)
  references prumo_private.inbox_eventos_s0(concessionaria_id,id),
 check ((estado='LEASED' and lease_worker is not null and lease_ate is not null)
   or (estado<>'LEASED' and lease_worker is null and lease_ate is null))
);
create index tarefas_ingresso_ready_s0
 on prumo_private.tarefas_ingresso_s0(concessionaria_id,estado,lease_ate,criado_em);
-- Unified technical intention ledger. Deliberately NO runnable send state:
-- C03/C06/C12 authorization must be revalidated in a future approved gate.
create table prumo_private.outbox_intencoes_s0(
 id uuid primary key default gen_random_uuid(),
 concessionaria_id uuid not null,
 canal_id uuid not null,
 contrato text not null check(contrato in ('C03','C06','C12')),
 chave_idempotencia text not null check(length(chave_idempotencia) between 1 and 160),
 versao_estado_sintetica bigint not null check(versao_estado_sintetica>0),
 estado text not null default 'BLOQUEADA_GATES'
   check(estado in ('BLOQUEADA_GATES','CANCELADA')),
 criado_em timestamptz not null default clock_timestamp(),
 unique(concessionaria_id,canal_id,chave_idempotencia),
 foreign key(concessionaria_id,canal_id) references public.canais_loja(concessionaria_id,id)
);
alter table prumo_private.inbox_eventos_s0 enable row level security;
alter table prumo_private.tarefas_ingresso_s0 enable row level security;
alter table prumo_private.outbox_intencoes_s0 enable row level security;
revoke all on prumo_private.inbox_eventos_s0,
 prumo_private.tarefas_ingresso_s0,prumo_private.outbox_intencoes_s0
 from public,anon,authenticated,service_role,prumo_s0_gateway,prumo_s0_signer;

-- One call = one SQL transaction. Event acceptance and durable job creation
-- cannot diverge. A malformed item fails the WHOLE batch (no false ACK).
-- Hashes are passed by a synthetic trusted fixture; no HMAC proof here.
create function prumo_private.aceitar_lote_ingresso_s0(
 p_canal uuid,p_itens jsonb
) returns jsonb language plpgsql security invoker set search_path='' as $fn$
declare v_loja uuid;v_item jsonb;v_tipo text;v_chave text;v_hash text;
 v_inbox uuid;v_anterior text;v_new integer:=0;v_duplicado integer:=0;
begin
 if current_user<>'postgres' then raise exception 'INTERNAL_ONLY' using errcode='42501';end if;
 if p_canal is null or pg_catalog.jsonb_typeof(p_itens) is distinct from 'array'
 or pg_catalog.jsonb_array_length(p_itens) not between 1 and 20
 then raise exception 'INVALID_INGRESS_BATCH' using errcode='22023';end if;
 select c.concessionaria_id into v_loja from public.canais_loja c
 join public.concessionarias lo on lo.id=c.concessionaria_id and lo.ativo
 where c.id=p_canal and c.modo='simulado';
 if v_loja is null then raise exception 'UNKNOWN_CHANNEL' using errcode='22023';end if;
 for v_item in select value from pg_catalog.jsonb_array_elements(p_itens) loop
  v_tipo:=v_item->>'event_kind';v_chave:=v_item->>'dedupe_key';
  v_hash:=v_item->>'payload_fingerprint';
  if pg_catalog.jsonb_typeof(v_item) is distinct from 'object'
   or v_tipo not in ('inbound_message','status_callback') or v_tipo is null
   or v_chave is null or length(v_chave) not between 1 and 160
   or v_hash is null or v_hash !~ '^[a-f0-9]{64}$'
   or v_item ? 'concessionaria_id'
  then raise exception 'INVALID_INGRESS_ITEM' using errcode='22023';end if;
  insert into prumo_private.inbox_eventos_s0(
   concessionaria_id,canal_id,tipo,chave_evento,fingerprint_sintetico)
  values(v_loja,p_canal,v_tipo,v_chave,v_hash)
  on conflict(concessionaria_id,canal_id,tipo,chave_evento) do nothing
  returning id into v_inbox;
  if v_inbox is not null then
   insert into prumo_private.tarefas_ingresso_s0(inbox_id,concessionaria_id)
    values(v_inbox,v_loja);
   v_new:=v_new+1;
  else
   select fingerprint_sintetico into v_anterior
    from prumo_private.inbox_eventos_s0
    where concessionaria_id=v_loja and canal_id=p_canal
      and tipo=v_tipo and chave_evento=v_chave;
   if v_anterior is distinct from v_hash
   then raise exception 'CONFLICT_IDEMPOTENCY_KEY' using errcode='23505';end if;
   v_duplicado:=v_duplicado+1;
  end if;
  v_inbox:=null;
 end loop;
 return pg_catalog.jsonb_build_object('outcome',
  case when v_new=0 then 'ALREADY_ACCEPTED' else 'ACCEPTED_DURABLE' end,
  'accepted',v_new,'duplicates',v_duplicado,'concessionaria_id',v_loja);
end $fn$;

-- A private, scoped simulated worker may lease one ready job. No external
-- effects or auto-retry of uncertain sends are authorized by this operation.
create function prumo_private.reservar_ingresso_s0(
 p_loja uuid,p_canal uuid,p_worker uuid
) returns jsonb language plpgsql security invoker set search_path='' as $fn$
declare v_tarefa record;
begin
 if current_user<>'postgres' then raise exception 'INTERNAL_ONLY' using errcode='42501';end if;
 if p_loja is null or p_canal is null or p_worker is null or not exists(
 select 1 from public.canais_loja where id=p_canal and concessionaria_id=p_loja
 and modo='simulado') then raise exception 'INVALID_WORKER_SCOPE' using errcode='42501';end if;
 select t.inbox_id,t.versao into v_tarefa
 from prumo_private.tarefas_ingresso_s0 t
 join prumo_private.inbox_eventos_s0 i
   on i.id=t.inbox_id and i.concessionaria_id=t.concessionaria_id
 where i.concessionaria_id=p_loja and i.canal_id=p_canal
 and (t.estado='READY' or (t.estado='LEASED' and t.lease_ate<clock_timestamp()))
 order by t.criado_em,t.inbox_id
 limit 1 for update of t skip locked;
 if not found then return pg_catalog.jsonb_build_object('outcome','EMPTY');end if;
 update prumo_private.tarefas_ingresso_s0
 set estado='LEASED',lease_worker=p_worker,lease_ate=clock_timestamp()+interval '30 seconds',
 versao=versao+1,tentativas=tentativas+1
 where inbox_id=v_tarefa.inbox_id;
 return pg_catalog.jsonb_build_object('outcome','LEASED','inbox_id',v_tarefa.inbox_id,
 'versao',v_tarefa.versao+1);
end $fn$;
-- Recording an intention NEVER authorizes transmission.
create function prumo_private.registrar_intencao_bloqueada_s0(
 p_loja uuid,p_canal uuid,p_contrato text,p_chave text,p_versao bigint
) returns jsonb language plpgsql security invoker set search_path='' as $fn$
declare v_id uuid;v_antigo record;
begin
 if current_user<>'postgres' then raise exception 'INTERNAL_ONLY' using errcode='42501';end if;
 if p_contrato not in ('C03','C06','C12') or p_contrato is null
 or p_chave is null or length(p_chave) not between 1 and 160
 or p_versao is null or p_versao<1 or not exists (
 select 1 from public.canais_loja c join public.concessionarias l
 on l.id=c.concessionaria_id and l.ativo
 where c.id=p_canal and c.concessionaria_id=p_loja and c.modo='simulado')
 then raise exception 'INVALID_OUTBOX_INTENT' using errcode='22023';end if;
 insert into prumo_private.outbox_intencoes_s0(
 concessionaria_id,canal_id,contrato,chave_idempotencia,versao_estado_sintetica)
 values(p_loja,p_canal,p_contrato,p_chave,p_versao)
 on conflict(concessionaria_id,canal_id,chave_idempotencia) do nothing
 returning id into v_id;
 if v_id is not null then
  return pg_catalog.jsonb_build_object('outcome','ACCEPTED_BLOCKED','intent_id',v_id);
 end if;
 select * into v_antigo from prumo_private.outbox_intencoes_s0 where
 concessionaria_id=p_loja and canal_id=p_canal and chave_idempotencia=p_chave;
 if v_antigo.contrato is distinct from p_contrato
  or v_antigo.versao_estado_sintetica is distinct from p_versao
 then raise exception 'CONFLICT_IDEMPOTENCY_KEY' using errcode='23505';end if;
 return pg_catalog.jsonb_build_object('outcome','ALREADY_BLOCKED','intent_id',v_antigo.id);
end $fn$;

revoke all on function prumo_private.aceitar_lote_ingresso_s0(uuid,jsonb),
 prumo_private.reservar_ingresso_s0(uuid,uuid,uuid),
 prumo_private.registrar_intencao_bloqueada_s0(uuid,uuid,text,text,bigint)
 from public,anon,authenticated,service_role,prumo_s0_gateway,prumo_s0_signer;
