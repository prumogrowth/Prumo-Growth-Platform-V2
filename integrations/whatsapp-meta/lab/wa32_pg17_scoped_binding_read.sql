-- WA32: read physical WA29/31 synthetic claims; no S0 production table.
-- Mapping of lab shops to fake App/channel/wamid is explicit mock data.
\set ON_ERROR_STOP on
BEGIN READ ONLY;
SELECT jsonb_build_object(
  'revoked_a', (
   SELECT jsonb_build_object(
     'app_ref','WA32_LAB_APP_A','concessionaria_id',c.shop_ref,
     'canal_id','WA32_LAB_CHANNEL_A','waba_id','111111',
     'phone_number_id','1234567890',
     'provider_message_id','wamid.WA32_PG_A',
     'recipient_verified','5581900000000',
     'case_ref',c.case_ref,'attempt_ref',c.attempt_ref,
     'binding_revision',a.state_version,'claim_state',c.state
   )
   FROM wa29_lab.claims c JOIN wa29_lab.authority a
   ON a.shop_ref=c.shop_ref AND a.case_ref=c.case_ref
   WHERE c.shop_ref='shop_A' AND c.case_ref='case31_hist'
  ),
  'active_b',(
   SELECT jsonb_build_object(
     'app_ref','WA32_LAB_APP_B','concessionaria_id',c.shop_ref,
     'canal_id','WA32_LAB_CHANNEL_B','waba_id','222222',
     'phone_number_id','9876543210',
     'provider_message_id','wamid.WA32_PG_B',
     'recipient_verified','5581900000011',
     'case_ref',c.case_ref,'attempt_ref',c.attempt_ref,
     'binding_revision',a.state_version,'claim_state',c.state
   )
   FROM wa29_lab.claims c JOIN wa29_lab.authority a
   ON a.shop_ref=c.shop_ref AND a.case_ref=c.case_ref
   WHERE c.shop_ref='shop_B' AND c.case_ref='case31_b'
  ),
  'absent',(
   SELECT jsonb_build_object('case_ref',c.case_ref,'attempt_ref',c.attempt_ref)
   FROM wa29_lab.claims c
   WHERE c.shop_ref='shop_A' AND c.case_ref='case31_no_claim'
  ),
  'counts',jsonb_build_object(
   'a_claims',(SELECT count(*) FROM wa29_lab.claims c
     WHERE c.shop_ref='shop_A' AND c.case_ref='case31_hist'),
   'b_claims',(SELECT count(*) FROM wa29_lab.claims c
     WHERE c.shop_ref='shop_B' AND c.case_ref='case31_b')
  )
)::text;
COMMIT;
