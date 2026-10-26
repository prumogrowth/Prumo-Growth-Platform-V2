"""Additional Issue #5 negatives; original I74 eight markers unchanged."""
assert os.environ.get('CI')=='true' and os.environ.get('PRUMO_S1_I37_EPHEMERAL')=='YES'
# Actual signed and former application connections cannot SET ROLE executor.
for _dsn in (signed_dsn,gateway_dsn):
 with psycopg.connect(_dsn) as _con:
  try:
   _con.execute('set role prumo_s1_export_executor')
   raise AssertionError('I74_EXECUTOR_ROLE_BYPASS')
  except psycopg.errors.InsufficientPrivilege:pass
for _role in ('anon','authenticated','service_role'):
 with psycopg.connect(db) as _con:
  _con.execute('set local role '+_role)  # fixed test allowlist only
  try:
   _con.execute(_SQL_SIGNED_EXPORT,proof)
   raise AssertionError('I74_UNAUTHORIZED_ROLE_EXECUTE')
  except psycopg.errors.InsufficientPrivilege:pass
print('PASS I74-PROV-03: actual application SET ROLE and unauthorized role EXECUTE denied')

# Same GoTrue JWT whose shop grant was revoked earlier: RLS still empty.
_revoked=verifier.verify('Bearer '+token_g2)
_revoked_proof=signed_gateway.proof(_revoked,fields,'Bearer '+token_g2)
_before=int(sql('select count(*) from prumo_export_ledger.s1_70_export_reservas'))
with psycopg.connect(signed_dsn) as _con:
 _reply=_con.execute(_SQL_SIGNED_EXPORT,_revoked_proof).fetchone()[0]
assert _reply=={'estado':'VAZIO','linhas':[]},_reply
assert int(sql('select count(*) from prumo_export_ledger.s1_70_export_reservas'))==_before
print('PASS I74-SEC-01: revoked shop grant on same GoTrue token exports nothing and charges no quota')

# Sign while session exists, then logout: DB must recheck it after valid HMAC.
_actor,_token,_,_=person('i74-new-logout-only')
_principal=verifier.verify('Bearer '+_token)
_session_proof=signed_gateway.proof(_principal,fields,'Bearer '+_token)
_st,_=http('POST','/auth/v1/logout',bearer=_token,base=api)
assert _st in (200,204),_st
assert sql("select prumo_export_auth.sessao_ativa("+f"'{_principal.actor_id}'::uuid,'{_principal.session_id}'::uuid)")=='f'
with psycopg.connect(signed_dsn) as _con:
 try:
  _con.execute(_SQL_SIGNED_EXPORT,_session_proof)
  raise AssertionError('I74_VALID_MAC_REVOKED_SESSION_BYPASS')
 except psycopg.errors.InsufficientPrivilege:pass
assert sql(f"select count(*) from prumo_export_auth.nonces_i74 where nonce='{_session_proof[-2]}'")=='0'
assert int(sql('select count(*) from prumo_export_ledger.s1_70_export_reservas'))==_before
print('PASS I74-SEC-02: valid MAC after real GoTrue logout denied; nonce and quota rolled back')

# Revoke DB key after independent signer issued a fresh, otherwise valid proof.
_db_key_proof=signed_gateway.proof(principal,fields,'Bearer '+token53)
sql(f"update prumo_export_auth.chaves_i74 set active=false where id='{key}'::uuid")
try:
 with psycopg.connect(signed_dsn) as _con:
  try:
   _con.execute(_SQL_SIGNED_EXPORT,_db_key_proof)
   raise AssertionError('I74_DB_REVOKED_KEY_BYPASS')
  except psycopg.errors.InsufficientPrivilege:pass
 assert sql(f"select count(*) from prumo_export_auth.nonces_i74 where nonce='{_db_key_proof[-2]}'")=='0'
 assert int(sql('select count(*) from prumo_export_ledger.s1_70_export_reservas'))==_before
finally:
 # Only restore this test-created key for the unchanged original signer test 08.
 sql(f"update prumo_export_auth.chaves_i74 set active=true where id='{key}'::uuid")
print('PASS I74-SEC-03: DB key revocation denies previously signed proof without nonce or quota')
