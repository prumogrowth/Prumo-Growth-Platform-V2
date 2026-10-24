-- Disposable E04 PostgreSQL 17 fixture ONLY. NOT a hosted migration.
-- Shared transaction advisory lock for S0 identity readers/writers by shop.
-- Future writers remain possible: this NEVER grants a F03 permission.
create function prumo_private.s0_f03_lock_shop_local(p_shop uuid)
returns void language plpgsql security invoker set search_path=''
as $$
begin
 if current_user<>'postgres' or p_shop is null then
   raise exception 'S0_F03_SCOPE_DENIED_LOCAL' using errcode='42501';
 end if;
 perform pg_catalog.pg_advisory_xact_lock(
   pg_catalog.hashtextextended('s0-f03-shop:'||p_shop::text,0));
end $$;

create function prumo_private.s0_f03_candidate_writer_guard_local()
returns trigger language plpgsql security invoker set search_path=''
as $$
declare a uuid; b uuid;
begin
 if not ((tg_table_schema='prumo_private' and
          tg_table_name in ('pendencias_identidade_s0','aliases_identidade_s0'))
     or (tg_table_schema='public' and tg_table_name='leads_loja')) then
   raise exception 'S0_F03_SOURCE_DENIED_LOCAL' using errcode='42501';
 end if;
 a:=case when tg_op='INSERT' then null else old.concessionaria_id end;
 b:=case when tg_op='DELETE' then null else new.concessionaria_id end;
 if a is not null and b is not null and a<>b then
   if a::text<b::text then
     perform prumo_private.s0_f03_lock_shop_local(a);
     perform prumo_private.s0_f03_lock_shop_local(b);
   else
     perform prumo_private.s0_f03_lock_shop_local(b);
     perform prumo_private.s0_f03_lock_shop_local(a);
   end if;
 else
   perform prumo_private.s0_f03_lock_shop_local(pg_catalog.coalesce(a,b));
 end if;
 if tg_op='DELETE' then return old; end if;
 return new;
end $$;

create trigger s0_f03_pending_writer_scope
before insert or update or delete on prumo_private.pendencias_identidade_s0
for each row execute function prumo_private.s0_f03_candidate_writer_guard_local();
create trigger s0_f03_alias_writer_scope
before insert or update or delete on prumo_private.aliases_identidade_s0
for each row execute function prumo_private.s0_f03_candidate_writer_guard_local();
create trigger s0_f03_lead_writer_scope
before insert or update or delete on public.leads_loja
for each row execute function prumo_private.s0_f03_candidate_writer_guard_local();

revoke execute on function prumo_private.s0_f03_lock_shop_local(uuid),
 prumo_private.s0_f03_candidate_writer_guard_local()
from public,anon,authenticated,service_role,prumo_s0_gateway,prumo_s0_signer;
comment on function prumo_private.s0_f03_lock_shop_local(uuid)
is 'E04 only: transaction-scoped S0 candidate serialization, HOLD not grant';
