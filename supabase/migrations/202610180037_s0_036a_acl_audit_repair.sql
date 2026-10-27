-- S0-036A audit repair, chronological migration file 037.
-- Fix default PUBLIC EXECUTE on an internal trigger helper from S0/026.
-- No owner changes, no operational secrets, no hosted deployment.
-- The function remains callable by its installed PostgreSQL trigger.
revoke all on function prumo_private.auditar_rotacao_gateway_s0()
 from public,anon,authenticated,service_role,
 prumo_s0_gateway,prumo_s0_signer,prumo_s0_signed_executor;
