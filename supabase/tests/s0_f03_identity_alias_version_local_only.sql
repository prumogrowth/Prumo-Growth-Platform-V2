-- E04/S0-F03 LOCAL ONLY. Attaches independent F03 identity versioning
-- to the ACTUAL S0/028 synthetic alias and event tables, not a parallel clone.
-- Does NOT change an alias, merge leads, grant identity, or emit contacts.

create function prumo_private.cfi01_f03_alias_scope_local()
returns trigger language plpgsql security invoker set search_path=''
as $aliasguard$
begin
 if tg_table_schema='prumo_private' and tg_table_name='aliases_identidade_s0' then
  if tg_op='UPDATE' and
    (old.id is distinct from new.id or
     old.concessionaria_id is distinct from new.concessionaria_id or
     old.lead_id is distinct from new.lead_id) then
    raise exception 'F03_ALIAS_LEAD_REBIND_DENIED_LOCAL' using errcode='42501';
  end if;
 elsif tg_table_schema='prumo_private' and tg_table_name='eventos_identidade_s0' then
  if tg_op='UPDATE' and
    (old.id is distinct from new.id or
     old.concessionaria_id is distinct from new.concessionaria_id or
     old.lead_id is distinct from new.lead_id or
     old.alias_id is distinct from new.alias_id) then
    raise exception 'F03_IDENTITY_EVENT_REBIND_DENIED_LOCAL' using errcode='42501';
  end if;
  if not exists (
    select 1 from prumo_private.aliases_identidade_s0 a
    where a.id=new.alias_id and a.concessionaria_id=new.concessionaria_id
      and a.lead_id=new.lead_id
  ) then
    raise exception 'F03_IDENTITY_EVENT_SCOPE_MISMATCH_LOCAL' using errcode='42501';
  end if;
 else
  raise exception 'F03_UNKNOWN_IDENTITY_SOURCE_LOCAL' using errcode='42501';
 end if;
 return new;
end $aliasguard$;

create function prumo_private.cfi01_f03_alias_version_bump_local()
returns trigger language plpgsql security invoker set search_path=''
as $aliasbump$
declare v_shop uuid;v_lead uuid;
begin
 if tg_table_schema<>'prumo_private' or
    tg_table_name not in ('aliases_identidade_s0','eventos_identidade_s0') then
  raise exception 'F03_UNKNOWN_IDENTITY_SOURCE_LOCAL' using errcode='42501';
 end if;
 if tg_op='UPDATE' and pg_catalog.to_jsonb(old)=pg_catalog.to_jsonb(new)
 then return new; end if;
 v_shop:=case when tg_op='DELETE' then old.concessionaria_id else new.concessionaria_id end;
 v_lead:=case when tg_op='DELETE' then old.lead_id else new.lead_id end;
 -- Version changes happen in the same transaction as the source mutation.
 -- Missing F03 version record: leave old S0 flows intact; F03 CAS fails closed.
 update prumo_private.cfi01_f03_lead_versions_local
  set versao_identidade=versao_identidade+1
  where concessionaria_id=v_shop and lead_id=v_lead;
 if tg_op='DELETE' then return old;end if;
 return new;
end $aliasbump$;

create trigger cfi01_f03_alias_scope
 before update on prumo_private.aliases_identidade_s0
 for each row execute function prumo_private.cfi01_f03_alias_scope_local();
create trigger cfi01_f03_event_scope
 before insert or update on prumo_private.eventos_identidade_s0
 for each row execute function prumo_private.cfi01_f03_alias_scope_local();
create trigger cfi01_f03_alias_version
 after insert or update or delete on prumo_private.aliases_identidade_s0
 for each row execute function prumo_private.cfi01_f03_alias_version_bump_local();
create trigger cfi01_f03_event_version
 after insert or update or delete on prumo_private.eventos_identidade_s0
 for each row execute function prumo_private.cfi01_f03_alias_version_bump_local();

revoke execute on function prumo_private.cfi01_f03_alias_scope_local(),
 prumo_private.cfi01_f03_alias_version_bump_local()
 from public,anon,authenticated,service_role,prumo_s0_gateway,prumo_s0_signer;
comment on function prumo_private.cfi01_f03_alias_version_bump_local()
 is 'LOCAL E04 F03: S0/028 identity alias/evidence changes invalidate version for bound lead and store';
