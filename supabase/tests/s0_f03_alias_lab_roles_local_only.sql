-- E04 F03 disposable PG17 ONLY. S0/028 includes revokes for two roles
-- introduced by another migration that CFI-01's minimal bootstrap omits.
-- They have NOLOGIN, no memberships, grants or privileges. Never hosted.
do $labroles$
begin
 if not exists(select 1 from pg_catalog.pg_roles where rolname='prumo_s0_gateway')
 then create role prumo_s0_gateway nologin noinherit; end if;
 if not exists(select 1 from pg_catalog.pg_roles where rolname='prumo_s0_signer')
 then create role prumo_s0_signer nologin noinherit; end if;
end $labroles$;
