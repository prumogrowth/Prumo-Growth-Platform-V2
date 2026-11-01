"""20 physical PG17 commercial-source metadata and F01 owner recheck cases."""
import os,unittest,threading
from concurrent.futures import ThreadPoolExecutor
try:
 import psycopg
except ImportError:
 psycopg=None
from integration.s0s1_f01_ownership import test_pg17_service as inherited
from .pg17_service import prepare,review,FLAGS

@unittest.skipUnless(os.getenv('M09_PG17_DISPOSABLE')=='YES' and psycopg,
                     'requires PG17 disposable fixture')
class F01CommercialPhysical(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  inherited.F01OwnershipPhysical.setUpClass.__func__(cls)
  try:
   with cls.lab.admin() as c:
    c.execute("SET s0_meta.disposable='YES'")
    c.execute("SET s0_f01.install='COMMERCIAL_SOURCES_LAB_ONLY'")
    c.execute((cls.origin/'integration/s0s1_f01_sources/pg17_schema.sql').read_text())
  except BaseException:
   inherited.F01OwnershipPhysical.tearDownClass.__func__(cls)
   raise
 @classmethod
 def tearDownClass(cls):
  try:
   with cls.lab.admin() as c:
    c.execute('DROP SCHEMA IF EXISTS s0_f01_sources_lab CASCADE')
  finally:
   inherited.F01OwnershipPhysical.tearDownClass.__func__(cls)
 def setUp(self):
  inherited.F01OwnershipPhysical.setUp(self)
  with self.lab.admin() as c:
   c.execute('TRUNCATE s0_f01_sources_lab.reviews,'
     's0_f01_sources_lab.aliases,s0_f01_sources_lab.selections,'
     's0_f01_sources_lab.sources,s0_f01_sources_lab.contexts CASCADE')
   c.execute("""INSERT INTO s0_f01_sources_lab.contexts
     (case_ref,store_ref,person_ref,purpose_ref,catalog_revision,
     knowledge_revision,policy_revision,consent_revision,grant_revision,
     content_policy,consent_state) VALUES
     ('case_A','store-A','person_A','offer_info',1,1,1,1,1,
      'LAB_ALLOWED','LAB_ALLOWED'),
     ('case_B','store-B','person_B','offer_info',1,1,1,1,1,
      'LAB_ALLOWED','LAB_ALLOWED')""")
   c.execute("""INSERT INTO s0_f01_sources_lab.sources
    (source_ref,case_ref,store_ref,purpose_ref,kind,approval_state,
     source_version,valid_until,corrected_by_ref,claim_codes,
     content_grant_active,provenance_lab_asserted,minimized_lab_asserted)
     VALUES
     ('src_current_A','case_A','store-A','offer_info','current',
      'APPROVED_ACTIVE',1,clock_timestamp()+interval '1 hour',NULL,
      '["PRODUCT_FEATURE"]'::jsonb,true,true,true),
     ('src_history_A','case_A','store-A','offer_info','historical',
      'EXPIRED',1,clock_timestamp()-interval '1 day',NULL,
      '["OLD_EXPLANATION"]'::jsonb,true,true,true),
     ('src_other_B','case_B','store-B','offer_info','current',
      'APPROVED_ACTIVE',1,clock_timestamp()+interval '1 hour',NULL,
      '["OTHER_FEATURE"]'::jsonb,true,true,true)""")
  self.claims=[dict(source_ref='src_current_A',
     claim_code='PRODUCT_FEATURE',usage='commercial')]
  self.grant=1
  self.assertEqual(self.start()['status'],'LAB_TURN_RECORDED_NO_MODEL')
 def select(self,claims=None,grant=None):
  with self.lab.admin() as c:
   return prepare(c,request_ref='turn_A',scope=self.scope,
    expected=self.expected,grant_revision=self.grant if grant is None else grant,
    claims=self.claims if claims is None else claims)
 def assess(self,rows=None,claims=None):
  if rows is None:
   rows=[dict(alias='src_001',claimCode='PRODUCT_FEATURE',usage='commercial')]
  with self.lab.admin() as c:
   return review(c,request_ref='turn_A',scope=self.scope,
     expected=self.expected,grant_revision=self.grant,
     claims=self.claims if claims is None else claims,proposal_aliases=rows)
 def mutate(self,sql):
  with self.lab.admin() as c: c.execute(sql)
 def count(self):
  with self.lab.admin() as c:
   return tuple(c.execute('SELECT COUNT(*) AS n FROM s0_f01_sources_lab.'+t)
    .fetchone()['n'] for t in ('selections','aliases','reviews'))
 def safe(self,x):
  self.assertTrue(x['lab_only'])
  for f in FLAGS:self.assertFalse(x[f],f)
 def test_01_selected_only_opaque_alias_no_offer(self):
  x=self.select();self.assertEqual(x['status'],'LAB_SELECTION_RECORDED_NO_MODEL')
  self.assertEqual(x['aliases'],[{'alias':'src_001','claimCode':'PRODUCT_FEATURE','usage':'commercial'}])
  self.assertNotIn('src_current_A',str(x))
  self.safe(x);self.assertEqual(self.count(),(1,1,0))
 def test_02_exact_replay_no_duplicate(self):
  self.select();self.assertEqual(self.select()['status'],'LAB_SELECTION_REPLAY_NO_MODEL')
  self.assertEqual(self.count(),(1,1,0))
 def test_03_missing_or_cross_store_source_denies(self):
  for source in ('src_other_B','missing'):
   x=self.select([dict(source_ref=source,claim_code='PRODUCT_FEATURE',usage='commercial')])
   self.assertEqual(x['reason'],'SOURCE_NOT_IN_SCOPE')
  self.assertEqual(self.count(),(0,0,0))
 def test_04_historical_cannot_back_commercial_offer(self):
  x=self.select([dict(source_ref='src_history_A',
                claim_code='OLD_EXPLANATION',usage='commercial')])
  self.assertEqual(x['reason'],'HISTORICAL_CANNOT_OFFER')
 def test_05_historical_interpretive_only(self):
  x=self.select([dict(source_ref='src_history_A',
                claim_code='OLD_EXPLANATION',usage='interpretive')])
  self.assertEqual(x['status'],'LAB_SELECTION_RECORDED_NO_MODEL')
  self.safe(x)
 def test_06_paused_revoked_draft_expired_source_denied(self):
  for state in ('PAUSED','REVOKED','DRAFT','EXPIRED'):
   self.mutate("UPDATE s0_f01_sources_lab.sources SET approval_state='"+state+
               "' WHERE source_ref='src_current_A'")
   self.assertEqual(self.select()['reason'],'SOURCE_INACTIVE')
  self.assertEqual(self.count(),(0,0,0))
 def test_07_expired_or_unbounded_current_denied(self):
  for ddl in ("valid_until=NULL",
              "valid_until=clock_timestamp()-interval '1 second'"):
   self.mutate("UPDATE s0_f01_sources_lab.sources SET "+ddl+
               " WHERE source_ref='src_current_A'")
   self.assertEqual(self.select()['reason'],'EXPIRED_OR_UNBOUNDED')
 def test_08_source_corrected_denied(self):
  self.mutate("UPDATE s0_f01_sources_lab.sources "
              "SET corrected_by_ref='new_ref' WHERE source_ref='src_current_A'")
  self.assertEqual(self.select()['reason'],'SOURCE_CORRECTED')
 def test_09_unknown_claim_never_becomes_price_fact(self):
  x=self.select([dict(source_ref='src_current_A',claim_code='PRICE',
                      usage='commercial')])
  self.assertEqual(x['reason'],'CLAIM_UNSUPPORTED')
 def test_10_missing_grant_or_provenance_or_minimization_denied(self):
  for k in ('content_grant_active','provenance_lab_asserted','minimized_lab_asserted'):
   self.mutate('UPDATE s0_f01_sources_lab.sources SET '+k+
      "=false WHERE source_ref='src_current_A'")
   self.assertEqual(self.select()['reason'],'GRANT_OR_PROVENANCE_MISSING')
   self.mutate('UPDATE s0_f01_sources_lab.sources SET '+k+
      "=true WHERE source_ref='src_current_A'")
 def test_11_content_or_consent_denied_or_unknown(self):
  for k in ('content_policy','consent_state'):
   for state in ('LAB_DENIED','LAB_UNKNOWN'):
    self.mutate("UPDATE s0_f01_sources_lab.contexts SET "+k+"='"+state+
                "' WHERE case_ref='case_A'")
    self.assertEqual(self.select()['reason'],'CONTENT_POLICY_DENIED')
   self.mutate("UPDATE s0_f01_sources_lab.contexts SET "+k+
               "='LAB_ALLOWED' WHERE case_ref='case_A'")
 def test_12_catalog_knowledge_policy_consent_grant_versions(self):
  for col in ('catalog','knowledge','policy','consent','grant'):
   self.mutate('UPDATE s0_f01_sources_lab.contexts SET '+col+
     "_revision=2 WHERE case_ref='case_A'")
   self.assertEqual(self.select()['reason'],'STALE_VERSIONS')
   self.mutate('UPDATE s0_f01_sources_lab.contexts SET '+col+
     "_revision=1 WHERE case_ref='case_A'")
 def test_13_stable_sources_review_only(self):
  self.select()
  x=self.assess();self.assertEqual(x['status'],'LAB_REVIEW_RECORDED_NO_PUBLISH')
  self.safe(x);self.assertEqual(self.count(),(1,1,1))
 def test_14_replay_review_no_second_record(self):
  self.select();self.assess()
  self.assertEqual(self.assess()['status'],'LAB_REVIEW_REPLAY_NO_PUBLISH')
  self.assertEqual(self.count(),(1,1,1))
 def test_15_changed_claim_alias_denied(self):
  self.select()
  x=self.assess([dict(alias='src_999',claimCode='PRODUCT_FEATURE',usage='commercial')])
  self.assertEqual(x['reason'],'CLAIMS_NOT_EXACT')
  self.assertEqual(self.count(),(1,1,0))
 def test_16_direct_source_change_without_revision_denies(self):
  self.select()
  self.mutate("UPDATE s0_f01_sources_lab.sources SET source_version=2 "
              "WHERE source_ref='src_history_A'")
  self.assertEqual(self.assess()['reason'],'SOURCES_CHANGED')
  self.assertEqual(self.count(),(1,1,0))
 def test_17_new_unselected_source_detected(self):
  self.select()
  self.mutate("""INSERT INTO s0_f01_sources_lab.sources
   (source_ref,case_ref,store_ref,purpose_ref,kind,approval_state,
    source_version,claim_codes) VALUES
   ('added','case_A','store-A','offer_info','historical','EXPIRED',
    1,'[]'::jsonb)""")
  self.assertEqual(self.assess()['reason'],'SOURCES_CHANGED')
 def test_18_alias_remapped_after_prepare_denied(self):
  self.select()
  self.mutate("UPDATE s0_f01_sources_lab.aliases SET source_ref='src_history_A' "
              "WHERE request_ref='turn_A'")
  self.assertEqual(self.assess()['reason'],'ALIAS_CHANGED')
 def test_19_handoff_after_selection_prevents_review(self):
  self.select();self.assertEqual(
    self.handoff()['status'],'LAB_HANDOFF_DURABLY_RECORDED_NO_PUBLISH')
  self.assertEqual(self.assess()['reason'],'HUMAN_ONLY')
  self.assertEqual(self.count(),(1,1,0))
 def test_20_rollback_and_acl(self):
  with self.assertRaises(RuntimeError):
   with self.lab.admin() as c:
    self.assertEqual(prepare(c,request_ref='turn_A',scope=self.scope,
      expected=self.expected,grant_revision=1,claims=self.claims)['status'],
      'LAB_SELECTION_RECORDED_NO_MODEL')
    raise RuntimeError('abort')
  self.assertEqual(self.count(),(0,0,0))
  for table in ('contexts','sources','selections','aliases','reviews'):
   with psycopg.connect(self.lab.runtime_dsn) as c:
    with self.assertRaises(psycopg.Error):
     c.execute('SELECT * FROM s0_f01_sources_lab.'+table)
if __name__=='__main__':unittest.main()
