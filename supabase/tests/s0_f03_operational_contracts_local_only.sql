-- E04: S0-only operational contract registry, disposable PG17 fixture.
-- Metadata for hypothetical synthetic fields; NO grant to F03, no field write.
create table prumo_private.cfi01_f03_operational_field_contracts_local(
 concessionaria_id uuid not null references public.concessionarias(id) on delete restrict,
 campo_sintetico text not null check(campo_sintetico ~ '^[a-z_]{2,48}$'),
 tipo_sintetico text not null check(tipo_sintetico in ('TEXT_ONLY','CATALOG_CODE')),
 max_chars integer not null check(max_chars between 2 and 128),
 ativo_sintetico boolean not null default true,
 primary key(concessionaria_id,campo_sintetico),
 constraint catalog_code_length_local check(tipo_sintetico<>'CATALOG_CODE' or max_chars<=48)
);
create function prumo_private.cfi01_f03_operational_field_guard_local()
returns trigger language plpgsql security invoker set search_path='' as $guard$
begin
 if old.concessionaria_id is distinct from new.concessionaria_id
    or old.campo_sintetico is distinct from new.campo_sintetico
    or old.tipo_sintetico is distinct from new.tipo_sintetico then
  raise exception 'F03_OPERATIONAL_CONTRACT_REKEY_DENIED' using errcode='42501';
 end if;
 return new;
end $guard$;
create trigger f03_operational_contract_guard
before update on prumo_private.cfi01_f03_operational_field_contracts_local
for each row execute function prumo_private.cfi01_f03_operational_field_guard_local();

create function prumo_private.cfi01_f03_operational_contract_version_local()
returns trigger language plpgsql security invoker set search_path='' as $version$
declare v_shop uuid;
begin
 if tg_op='UPDATE' and pg_catalog.to_jsonb(old)=pg_catalog.to_jsonb(new) then
  return new;
 end if;
 v_shop:=case when tg_op='DELETE' then old.concessionaria_id else new.concessionaria_id end;
 update prumo_private.cfi01_f03_catalog_versions_local
 set versao_catalogo=versao_catalogo+1 where concessionaria_id=v_shop;
 if not found then
  raise exception 'F03_OPERATIONAL_CATALOG_VERSION_MISSING' using errcode='42501';
 end if;
 if tg_op='DELETE' then return old; end if;
 return new;
end $version$;
create trigger f03_operational_contract_version
after insert or update or delete on prumo_private.cfi01_f03_operational_field_contracts_local
for each row execute function prumo_private.cfi01_f03_operational_contract_version_local();

alter table prumo_private.cfi01_f03_operational_field_contracts_local enable row level security;
revoke all on prumo_private.cfi01_f03_operational_field_contracts_local
 from public,anon,authenticated,service_role,prumo_s0_gateway,prumo_s0_signer;
revoke execute on function prumo_private.cfi01_f03_operational_field_guard_local(),
 prumo_private.cfi01_f03_operational_contract_version_local()
 from public,anon,authenticated,service_role,prumo_s0_gateway,prumo_s0_signer;
comment on table prumo_private.cfi01_f03_operational_field_contracts_local
 is 'E04 local S0-only contract metadata: no operational production form, no AI access, no grant';
