-- S0/040: scoped security repair requested by Meta integration, fixtures only.
-- DEC-WA-05 / WA-06B: one internal channel must resolve to ONE WABA/phone
-- binding at a time. This is NOT a real credential/channel registry.
-- PostgreSQL rejects existing contradictory fixture mappings: no silent cleanup.
alter table prumo_private.meta_canais_fixture_s0
 add constraint meta_canais_fixture_canal_emissor_unico_s0
 unique(concessionaria_id,canal_id);

-- Existing UNIQUE(phone_number_ref) already enforces the reverse direction;
-- the FK app_ref+concessionaria_id continues to constrain App ownership.
-- No elevated GRANT, RPC, Meta ACK or production migration authorized.
