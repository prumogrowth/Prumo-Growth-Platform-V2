-- S0/042 WA-15A: technical numeric Meta IDs -> existing S0 channel registry.
-- ONLY disposable local PostgreSQL fixture, never a public RPC or Graph sender.
-- The authoritative mapping is STILL meta_apps_fixture_s0 +
-- meta_canais_fixture_s0; no second sender/channel registry is created.
alter table prumo_private.meta_apps_fixture_s0
 add column app_technical_ref text unique
 check (app_technical_ref is null or app_technical_ref ~ '^[0-9]{5,25}$');

alter table prumo_private.meta_canais_fixture_s0
 add column waba_technical_ref text,
 add column phone_technical_ref text unique,
 add constraint meta_tech_sender_pair_s0 check (
   (waba_technical_ref is null and phone_technical_ref is null)
   or (waba_technical_ref is not null and phone_technical_ref is not null
       and waba_technical_ref ~ '^[0-9]{5,25}
 );

-- Same external WABA cannot belong to different internal Apps, while a
-- WABA legitimately supports multiple sender phones for the same App.
-- Advisory lock serializes competing assignments even for two fresh rows.
create function prumo_private.validar_owner_waba_tecnico_fixture_s0()
returns trigger language plpgsql security invoker set search_path='' as $wa15_owner$
begin
 if new.waba_technical_ref is not null then
   perform pg_catalog.pg_advisory_xact_lock(
     pg_catalog.hashtextextended('wa15-waba:'||new.waba_technical_ref, 42));
   if exists(select 1 from prumo_private.meta_canais_fixture_s0 m
     where m.waba_technical_ref=new.waba_technical_ref
       and m.app_ref<>new.app_ref
       and (tg_op='INSERT' or m.canal_id<>new.canal_id))
   then raise exception 'WABA_TECHNICAL_OWNER_CONFLICT' using errcode='23505';end if;
 end if;
 return new;
end $wa15_owner$;
create trigger meta_waba_owner_technical_guard_s0
 before insert or update of app_ref,waba_technical_ref
 on prumo_private.meta_canais_fixture_s0
 for each row execute function prumo_private.validar_owner_waba_tecnico_fixture_s0();

-- Once an S0 technical binding exists, external aliases used to resolve it
-- must not silently change. A lab owner can alter DDL, not a tamper proof DB.
create function prumo_private.bloquear_remapeamento_tech_fixture_s0()
returns trigger language plpgsql security invoker set search_path='' as $wa15_freeze$
begin
 if tg_table_name='meta_apps_fixture_s0' then
   if exists (select 1 from prumo_private.meta_vinculos_tentativa_fixture_s0 b
     where b.app_ref=old.app_ref) then
      if tg_op='DELETE'
         or old.app_ref is distinct from new.app_ref
         or old.app_technical_ref is distinct from new.app_technical_ref
      then raise exception 'BOUND_META_ALIAS_IMMUTABLE' using errcode='42501';end if;
   end if;
 elsif tg_table_name='meta_canais_fixture_s0' then
   if exists (select 1 from prumo_private.meta_vinculos_tentativa_fixture_s0 b
     where b.app_ref=old.app_ref and b.concessionaria_id=old.concessionaria_id
       and b.canal_id=old.canal_id) then
      if tg_op='DELETE'
         or old.app_ref is distinct from new.app_ref
         or old.waba_technical_ref is distinct from new.waba_technical_ref
         or old.phone_technical_ref is distinct from new.phone_technical_ref
      then raise exception 'BOUND_META_ALIAS_IMMUTABLE' using errcode='42501';end if;
   end if;
 end if;
 if tg_op='DELETE' then return old;end if;
 return new;
end $wa15_freeze$;
create trigger meta_apps_tech_freeze_s0
 before update or delete on prumo_private.meta_apps_fixture_s0
 for each row execute function prumo_private.bloquear_remapeamento_tech_fixture_s0();
create trigger meta_canais_tech_freeze_s0
 before update or delete on prumo_private.meta_canais_fixture_s0
 for each row execute function prumo_private.bloquear_remapeamento_tech_fixture_s0();

-- No caller-provided tenant, WABA alias, shop, or channel mapping is trusted.
-- We check ALL three technical Meta IDs against S0-owned registry, then use
-- the already-tested S0-041 writer. Only postgres local fixture can invoke.
create function prumo_private.registrar_vinculo_meta_tecnico_fixture_s0(
 p_app_tech text,p_waba_tech text,p_phone_tech text,
 p_canal uuid,p_intencao uuid,p_attempt text,p_correlation text,
 p_recipient text,p_wamid text,p_http_status integer
) returns jsonb language plpgsql security invoker set search_path='' as $wa15_write$
declare v_app text;
begin
 if current_user<>'postgres' then
   raise exception 'INTERNAL_ONLY' using errcode='42501';end if;
 if p_app_tech is null or p_app_tech !~ '^[0-9]{5,25}$'
    or p_waba_tech is null or p_waba_tech !~ '^[0-9]{5,25}$'
    or p_phone_tech is null or p_phone_tech !~ '^[0-9]{5,25}$'
 then raise exception 'INVALID_META_TECHNICAL_SCOPE' using errcode='22023';end if;
 select a.app_ref into v_app
 from prumo_private.meta_apps_fixture_s0 a
 join prumo_private.meta_canais_fixture_s0 m on m.app_ref=a.app_ref
   and m.concessionaria_id=a.concessionaria_id
 join public.canais_loja c on c.id=m.canal_id
   and c.concessionaria_id=m.concessionaria_id
 where a.app_technical_ref=p_app_tech and m.waba_technical_ref=p_waba_tech
   and m.phone_technical_ref=p_phone_tech and m.canal_id=p_canal
   and c.modo='simulado'
 for share of a,m;
 if not found then
   raise exception 'UNMAPPED_META_TECHNICAL_SCOPE' using errcode='42501';end if;
 return prumo_private.registrar_vinculo_meta_fixture_s0(
   v_app,p_canal,p_intencao,p_attempt,p_correlation,p_recipient,p_wamid,p_http_status);
end $wa15_write$;

-- Exact read-only recovery, including after cancellation, but never a new
-- POST, ACK, delivered status or commercial authority.
create function prumo_private.consultar_vinculo_meta_tecnico_fixture_s0(
 p_app_tech text,p_waba_tech text,p_phone_tech text,
 p_canal uuid,p_intencao uuid,p_attempt text,p_correlation text,
 p_recipient text,p_wamid text
) returns jsonb language plpgsql security invoker set search_path='' as $wa15_read$
declare v_app text;
begin
 if current_user<>'postgres' then
   raise exception 'INTERNAL_ONLY' using errcode='42501';end if;
 if p_app_tech is null or p_app_tech !~ '^[0-9]{5,25}$'
    or p_waba_tech is null or p_waba_tech !~ '^[0-9]{5,25}$'
    or p_phone_tech is null or p_phone_tech !~ '^[0-9]{5,25}$'
 then raise exception 'INVALID_META_TECHNICAL_SCOPE' using errcode='22023';end if;
 select a.app_ref into v_app
 from prumo_private.meta_apps_fixture_s0 a
 join prumo_private.meta_canais_fixture_s0 m on m.app_ref=a.app_ref
   and m.concessionaria_id=a.concessionaria_id
 join public.canais_loja c on c.id=m.canal_id
   and c.concessionaria_id=m.concessionaria_id
 join prumo_private.outbox_intencoes_s0 o
   on o.concessionaria_id=m.concessionaria_id
   and o.canal_id=m.canal_id and o.id=p_intencao
 where a.app_technical_ref=p_app_tech and m.waba_technical_ref=p_waba_tech
   and m.phone_technical_ref=p_phone_tech and m.canal_id=p_canal
   and c.modo='simulado'
 for share of a,m;
 if not found then
   raise exception 'UNMAPPED_META_TECHNICAL_SCOPE' using errcode='42501';end if;
 return prumo_private.consultar_vinculo_meta_fixture_s0(
    v_app,p_canal,p_intencao,p_attempt,p_correlation,p_recipient,p_wamid);
end $wa15_read$;

-- All helpers are private. This is NOT a credential-bearing service identity.
revoke all on function prumo_private.validar_owner_waba_tecnico_fixture_s0(),
 prumo_private.bloquear_remapeamento_tech_fixture_s0(),
 prumo_private.registrar_vinculo_meta_tecnico_fixture_s0(
    text,text,text,uuid,uuid,text,text,text,text,integer),
 prumo_private.consultar_vinculo_meta_tecnico_fixture_s0(
    text,text,text,uuid,uuid,text,text,text,text)
from public,anon,authenticated,service_role,prumo_s0_gateway,prumo_s0_signer;

       and phone_technical_ref ~ '^[0-9]{5,25}
 );

-- Same external WABA cannot belong to different internal Apps, while a
-- WABA legitimately supports multiple sender phones for the same App.
-- Advisory lock serializes competing assignments even for two fresh rows.
create function prumo_private.validar_owner_waba_tecnico_fixture_s0()
returns trigger language plpgsql security invoker set search_path='' as $wa15_owner$
begin
 if new.waba_technical_ref is not null then
   perform pg_catalog.pg_advisory_xact_lock(
     pg_catalog.hashtextextended('wa15-waba:'||new.waba_technical_ref, 42));
   if exists(select 1 from prumo_private.meta_canais_fixture_s0 m
     where m.waba_technical_ref=new.waba_technical_ref
       and m.app_ref<>new.app_ref
       and (tg_op='INSERT' or m.canal_id<>new.canal_id))
   then raise exception 'WABA_TECHNICAL_OWNER_CONFLICT' using errcode='23505';end if;
 end if;
 return new;
end $wa15_owner$;
create trigger meta_waba_owner_technical_guard_s0
 before insert or update of app_ref,waba_technical_ref
 on prumo_private.meta_canais_fixture_s0
 for each row execute function prumo_private.validar_owner_waba_tecnico_fixture_s0();

-- Once an S0 technical binding exists, external aliases used to resolve it
-- must not silently change. A lab owner can alter DDL, not a tamper proof DB.
create function prumo_private.bloquear_remapeamento_tech_fixture_s0()
returns trigger language plpgsql security invoker set search_path='' as $wa15_freeze$
begin
 if tg_table_name='meta_apps_fixture_s0' then
   if exists (select 1 from prumo_private.meta_vinculos_tentativa_fixture_s0 b
     where b.app_ref=old.app_ref) then
      if tg_op='DELETE'
         or old.app_ref is distinct from new.app_ref
         or old.app_technical_ref is distinct from new.app_technical_ref
      then raise exception 'BOUND_META_ALIAS_IMMUTABLE' using errcode='42501';end if;
   end if;
 elsif tg_table_name='meta_canais_fixture_s0' then
   if exists (select 1 from prumo_private.meta_vinculos_tentativa_fixture_s0 b
     where b.app_ref=old.app_ref and b.concessionaria_id=old.concessionaria_id
       and b.canal_id=old.canal_id) then
      if tg_op='DELETE'
         or old.app_ref is distinct from new.app_ref
         or old.waba_technical_ref is distinct from new.waba_technical_ref
         or old.phone_technical_ref is distinct from new.phone_technical_ref
      then raise exception 'BOUND_META_ALIAS_IMMUTABLE' using errcode='42501';end if;
   end if;
 end if;
 if tg_op='DELETE' then return old;end if;
 return new;
end $wa15_freeze$;
create trigger meta_apps_tech_freeze_s0
 before update or delete on prumo_private.meta_apps_fixture_s0
 for each row execute function prumo_private.bloquear_remapeamento_tech_fixture_s0();
create trigger meta_canais_tech_freeze_s0
 before update or delete on prumo_private.meta_canais_fixture_s0
 for each row execute function prumo_private.bloquear_remapeamento_tech_fixture_s0();

-- No caller-provided tenant, WABA alias, shop, or channel mapping is trusted.
-- We check ALL three technical Meta IDs against S0-owned registry, then use
-- the already-tested S0-041 writer. Only postgres local fixture can invoke.
create function prumo_private.registrar_vinculo_meta_tecnico_fixture_s0(
 p_app_tech text,p_waba_tech text,p_phone_tech text,
 p_canal uuid,p_intencao uuid,p_attempt text,p_correlation text,
 p_recipient text,p_wamid text,p_http_status integer
) returns jsonb language plpgsql security invoker set search_path='' as $wa15_write$
declare v_app text;
begin
 if current_user<>'postgres' then
   raise exception 'INTERNAL_ONLY' using errcode='42501';end if;
 if p_app_tech is null or p_app_tech !~ '^[0-9]{5,25}$'
    or p_waba_tech is null or p_waba_tech !~ '^[0-9]{5,25}$'
    or p_phone_tech is null or p_phone_tech !~ '^[0-9]{5,25}$'
 then raise exception 'INVALID_META_TECHNICAL_SCOPE' using errcode='22023';end if;
 select a.app_ref into v_app
 from prumo_private.meta_apps_fixture_s0 a
 join prumo_private.meta_canais_fixture_s0 m on m.app_ref=a.app_ref
   and m.concessionaria_id=a.concessionaria_id
 join public.canais_loja c on c.id=m.canal_id
   and c.concessionaria_id=m.concessionaria_id
 where a.app_technical_ref=p_app_tech and m.waba_technical_ref=p_waba_tech
   and m.phone_technical_ref=p_phone_tech and m.canal_id=p_canal
   and c.modo='simulado'
 for share of a,m;
 if not found then
   raise exception 'UNMAPPED_META_TECHNICAL_SCOPE' using errcode='42501';end if;
 return prumo_private.registrar_vinculo_meta_fixture_s0(
   v_app,p_canal,p_intencao,p_attempt,p_correlation,p_recipient,p_wamid,p_http_status);
end $wa15_write$;

-- Exact read-only recovery, including after cancellation, but never a new
-- POST, ACK, delivered status or commercial authority.
create function prumo_private.consultar_vinculo_meta_tecnico_fixture_s0(
 p_app_tech text,p_waba_tech text,p_phone_tech text,
 p_canal uuid,p_intencao uuid,p_attempt text,p_correlation text,
 p_recipient text,p_wamid text
) returns jsonb language plpgsql security invoker set search_path='' as $wa15_read$
declare v_app text;
begin
 if current_user<>'postgres' then
   raise exception 'INTERNAL_ONLY' using errcode='42501';end if;
 if p_app_tech is null or p_app_tech !~ '^[0-9]{5,25}$'
    or p_waba_tech is null or p_waba_tech !~ '^[0-9]{5,25}$'
    or p_phone_tech is null or p_phone_tech !~ '^[0-9]{5,25}$'
 then raise exception 'INVALID_META_TECHNICAL_SCOPE' using errcode='22023';end if;
 select a.app_ref into v_app
 from prumo_private.meta_apps_fixture_s0 a
 join prumo_private.meta_canais_fixture_s0 m on m.app_ref=a.app_ref
   and m.concessionaria_id=a.concessionaria_id
 join public.canais_loja c on c.id=m.canal_id
   and c.concessionaria_id=m.concessionaria_id
 join prumo_private.outbox_intencoes_s0 o
   on o.concessionaria_id=m.concessionaria_id
   and o.canal_id=m.canal_id and o.id=p_intencao
 where a.app_technical_ref=p_app_tech and m.waba_technical_ref=p_waba_tech
   and m.phone_technical_ref=p_phone_tech and m.canal_id=p_canal
   and c.modo='simulado'
 for share of a,m;
 if not found then
   raise exception 'UNMAPPED_META_TECHNICAL_SCOPE' using errcode='42501';end if;
 return prumo_private.consultar_vinculo_meta_fixture_s0(
    v_app,p_canal,p_intencao,p_attempt,p_correlation,p_recipient,p_wamid);
end $wa15_read$;

-- All helpers are private. This is NOT a credential-bearing service identity.
revoke all on function prumo_private.validar_owner_waba_tecnico_fixture_s0(),
 prumo_private.bloquear_remapeamento_tech_fixture_s0(),
 prumo_private.registrar_vinculo_meta_tecnico_fixture_s0(
    text,text,text,uuid,uuid,text,text,text,text,integer),
 prumo_private.consultar_vinculo_meta_tecnico_fixture_s0(
    text,text,text,uuid,uuid,text,text,text,text)
from public,anon,authenticated,service_role,prumo_s0_gateway,prumo_s0_signer;
)
 );

-- Same external WABA cannot belong to different internal Apps, while a
-- WABA legitimately supports multiple sender phones for the same App.
-- Advisory lock serializes competing assignments even for two fresh rows.
create function prumo_private.validar_owner_waba_tecnico_fixture_s0()
returns trigger language plpgsql security invoker set search_path='' as $wa15_owner$
begin
 if new.waba_technical_ref is not null then
   perform pg_catalog.pg_advisory_xact_lock(
     pg_catalog.hashtextextended('wa15-waba:'||new.waba_technical_ref, 42));
   if exists(select 1 from prumo_private.meta_canais_fixture_s0 m
     where m.waba_technical_ref=new.waba_technical_ref
       and m.app_ref<>new.app_ref
       and (tg_op='INSERT' or m.canal_id<>new.canal_id))
   then raise exception 'WABA_TECHNICAL_OWNER_CONFLICT' using errcode='23505';end if;
 end if;
 return new;
end $wa15_owner$;
create trigger meta_waba_owner_technical_guard_s0
 before insert or update of app_ref,waba_technical_ref
 on prumo_private.meta_canais_fixture_s0
 for each row execute function prumo_private.validar_owner_waba_tecnico_fixture_s0();

-- Once an S0 technical binding exists, external aliases used to resolve it
-- must not silently change. A lab owner can alter DDL, not a tamper proof DB.
create function prumo_private.bloquear_remapeamento_tech_fixture_s0()
returns trigger language plpgsql security invoker set search_path='' as $wa15_freeze$
begin
 if tg_table_name='meta_apps_fixture_s0' then
   if exists (select 1 from prumo_private.meta_vinculos_tentativa_fixture_s0 b
     where b.app_ref=old.app_ref) then
      if tg_op='DELETE'
         or old.app_ref is distinct from new.app_ref
         or old.app_technical_ref is distinct from new.app_technical_ref
      then raise exception 'BOUND_META_ALIAS_IMMUTABLE' using errcode='42501';end if;
   end if;
 elsif tg_table_name='meta_canais_fixture_s0' then
   if exists (select 1 from prumo_private.meta_vinculos_tentativa_fixture_s0 b
     where b.app_ref=old.app_ref and b.concessionaria_id=old.concessionaria_id
       and b.canal_id=old.canal_id) then
      if tg_op='DELETE'
         or old.app_ref is distinct from new.app_ref
         or old.waba_technical_ref is distinct from new.waba_technical_ref
         or old.phone_technical_ref is distinct from new.phone_technical_ref
      then raise exception 'BOUND_META_ALIAS_IMMUTABLE' using errcode='42501';end if;
   end if;
 end if;
 if tg_op='DELETE' then return old;end if;
 return new;
end $wa15_freeze$;
create trigger meta_apps_tech_freeze_s0
 before update or delete on prumo_private.meta_apps_fixture_s0
 for each row execute function prumo_private.bloquear_remapeamento_tech_fixture_s0();
create trigger meta_canais_tech_freeze_s0
 before update or delete on prumo_private.meta_canais_fixture_s0
 for each row execute function prumo_private.bloquear_remapeamento_tech_fixture_s0();

-- No caller-provided tenant, WABA alias, shop, or channel mapping is trusted.
-- We check ALL three technical Meta IDs against S0-owned registry, then use
-- the already-tested S0-041 writer. Only postgres local fixture can invoke.
create function prumo_private.registrar_vinculo_meta_tecnico_fixture_s0(
 p_app_tech text,p_waba_tech text,p_phone_tech text,
 p_canal uuid,p_intencao uuid,p_attempt text,p_correlation text,
 p_recipient text,p_wamid text,p_http_status integer
) returns jsonb language plpgsql security invoker set search_path='' as $wa15_write$
declare v_app text;
begin
 if current_user<>'postgres' then
   raise exception 'INTERNAL_ONLY' using errcode='42501';end if;
 if p_app_tech is null or p_app_tech !~ '^[0-9]{5,25}$'
    or p_waba_tech is null or p_waba_tech !~ '^[0-9]{5,25}$'
    or p_phone_tech is null or p_phone_tech !~ '^[0-9]{5,25}$'
 then raise exception 'INVALID_META_TECHNICAL_SCOPE' using errcode='22023';end if;
 select a.app_ref into v_app
 from prumo_private.meta_apps_fixture_s0 a
 join prumo_private.meta_canais_fixture_s0 m on m.app_ref=a.app_ref
   and m.concessionaria_id=a.concessionaria_id
 join public.canais_loja c on c.id=m.canal_id
   and c.concessionaria_id=m.concessionaria_id
 where a.app_technical_ref=p_app_tech and m.waba_technical_ref=p_waba_tech
   and m.phone_technical_ref=p_phone_tech and m.canal_id=p_canal
   and c.modo='simulado'
 for share of a,m;
 if not found then
   raise exception 'UNMAPPED_META_TECHNICAL_SCOPE' using errcode='42501';end if;
 return prumo_private.registrar_vinculo_meta_fixture_s0(
   v_app,p_canal,p_intencao,p_attempt,p_correlation,p_recipient,p_wamid,p_http_status);
end $wa15_write$;

-- Exact read-only recovery, including after cancellation, but never a new
-- POST, ACK, delivered status or commercial authority.
create function prumo_private.consultar_vinculo_meta_tecnico_fixture_s0(
 p_app_tech text,p_waba_tech text,p_phone_tech text,
 p_canal uuid,p_intencao uuid,p_attempt text,p_correlation text,
 p_recipient text,p_wamid text
) returns jsonb language plpgsql security invoker set search_path='' as $wa15_read$
declare v_app text;
begin
 if current_user<>'postgres' then
   raise exception 'INTERNAL_ONLY' using errcode='42501';end if;
 if p_app_tech is null or p_app_tech !~ '^[0-9]{5,25}$'
    or p_waba_tech is null or p_waba_tech !~ '^[0-9]{5,25}$'
    or p_phone_tech is null or p_phone_tech !~ '^[0-9]{5,25}$'
 then raise exception 'INVALID_META_TECHNICAL_SCOPE' using errcode='22023';end if;
 select a.app_ref into v_app
 from prumo_private.meta_apps_fixture_s0 a
 join prumo_private.meta_canais_fixture_s0 m on m.app_ref=a.app_ref
   and m.concessionaria_id=a.concessionaria_id
 join public.canais_loja c on c.id=m.canal_id
   and c.concessionaria_id=m.concessionaria_id
 join prumo_private.outbox_intencoes_s0 o
   on o.concessionaria_id=m.concessionaria_id
   and o.canal_id=m.canal_id and o.id=p_intencao
 where a.app_technical_ref=p_app_tech and m.waba_technical_ref=p_waba_tech
   and m.phone_technical_ref=p_phone_tech and m.canal_id=p_canal
   and c.modo='simulado'
 for share of a,m;
 if not found then
   raise exception 'UNMAPPED_META_TECHNICAL_SCOPE' using errcode='42501';end if;
 return prumo_private.consultar_vinculo_meta_fixture_s0(
    v_app,p_canal,p_intencao,p_attempt,p_correlation,p_recipient,p_wamid);
end $wa15_read$;

-- All helpers are private. This is NOT a credential-bearing service identity.
revoke all on function prumo_private.validar_owner_waba_tecnico_fixture_s0(),
 prumo_private.bloquear_remapeamento_tech_fixture_s0(),
 prumo_private.registrar_vinculo_meta_tecnico_fixture_s0(
    text,text,text,uuid,uuid,text,text,text,text,integer),
 prumo_private.consultar_vinculo_meta_tecnico_fixture_s0(
    text,text,text,uuid,uuid,text,text,text,text)
from public,anon,authenticated,service_role,prumo_s0_gateway,prumo_s0_signer;
