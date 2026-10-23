-- WA35: privileged READ of invented WA33 binding and WA29 claim, no actual S0.
\set ON_ERROR_STOP on
BEGIN READ ONLY;
SELECT jsonb_build_object(
 'app_ref',b.app_ref,'concessionaria_id',b.shop_ref,
 'canal_id',b.channel_ref,'waba_id',b.waba_ref,
 'phone_number_id',b.phone_ref,'provider_message_id',b.wamid_ref,
 'recipient_verified',b.recipient_ref,'case_ref',b.case_ref,
 'attempt_ref',b.attempt_ref,'binding_revision',b.binding_revision,
 'claim_state',c.state
)::text
FROM wa33_lab.bindings b
JOIN wa29_lab.claims c USING(shop_ref,case_ref,attempt_ref)
WHERE b.shop_ref='shop_A' AND b.case_ref='case31_late'
  AND b.attempt_ref='attempt31_late'
  AND b.app_ref='APP_A' AND b.waba_ref='111111'
  AND b.phone_ref='1234567890' AND b.wamid_ref='wamid.WA33_LATE';
COMMIT;
