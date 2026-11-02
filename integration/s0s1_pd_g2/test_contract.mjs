import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const data=JSON.parse(readFileSync(new URL('./contract_manifest.json',import.meta.url),'utf8'));
const {interfaces:i,version_semantics:v,handoff_policy:p}=data;
test('G2-CONTRACT-01 manifest pins exact S0/M09/Meta baselines',()=>{
 assert.equal(data.base_s0_sha,'fb06741b16eee9f9709acaed412daf5ea73a6d19');
 assert.equal(data.pinned_meta_m18_sha,'2a535ceb543418a76bb753a368eabc45bdbe4b0f');
 assert.equal(data.pinned_m09_ingress_sha,'01ffdb093013664b73b18d23f92aac2202578210');
});
test('G2-CONTRACT-02 snapshot is a distinct version, not covert S0 v0.2 alias',()=>{
 assert.notEqual(i.s0_g2_snapshot,i.s0_reservation);
 assert.notEqual(i.s0_g2_snapshot,i.meta_m18_pre_dispatch);
 assert.equal(p.meta_m18_original_accepts_g2_snapshot,false);
});
test('G2-CONTRACT-03 five independent M09 revisions retained',()=>{
 assert.deepEqual(v.m09_revision_keys,['route','app','binding','grant','principal']);
 assert.equal(v.can_replace_m09_five_with_meta_registry_scalar,false);
});
test('G2-CONTRACT-04 PRE_DISPATCH maintains eight explicit revisions',()=>{
 assert.equal(v.pre_dispatch_revision_keys.length,8);
 assert.equal(new Set(v.pre_dispatch_revision_keys).size,8);
 assert.equal(v.cycle_revision_independent,true);
 assert.equal(v.assignment_revision_independent,true);
});
test('G2-CONTRACT-05 no cross-provider hash alias without semantics',()=>{
 assert.equal(v.can_alias_body_sha256_to_content_sha256_without_canonicalization,false);
 assert.equal(v.can_alias_destination_sha256_to_recipient_sha256_without_canonicalization,false);
});
test('G2-CONTRACT-06 no fictional store UUID or old consumer coercion',()=>{
 assert.equal(v.can_map_store_A_fixture_to_tenant_uuid,false);
 assert.equal(v.can_convert_s0_v02_to_s0_v01,false);
 assert.equal(p.meta_m18_original_accepts_s0_v02,false);
});
test('G2-CONTRACT-07 no historical snapshot as Graph or retry permission',()=>{
 for(const k of ['g2_snapshot_is_authorization','g2_snapshot_linearizable_for_hosted_writers',
  'may_issue_graph_lease','may_send_message','may_auto_retry_commit_unknown'])
  assert.equal(p[k],false,k);
 assert.equal(p.m18_dispatch_candidate,null);
});
test('G2-CONTRACT-08 all external authority remains pending',()=>{
 for(const k of ['requires_meta_consumer_review','requires_hosted_identity',
  'requires_real_consent_provenance','requires_writer_atomicity_and_postcommit_CAS',
  'requires_outbox_and_wamid_correlation'])assert.equal(p[k],true,k);
});
test('G2-CONTRACT-09 state matrix has unknown, confirmed and cancellation',()=>{
 assert.equal(data.state_examples.length,5);
 assert.ok(data.state_examples.some(x=>x.s0_v02==='LAB_COMMIT_UNKNOWN'&&x.meaning==='NO_EXTERNAL_RETRY'));
 assert.ok(data.state_examples.some(x=>x.s0_v02==='LAB_COMMITTED_RECEIPT_NO_DISPATCH'&&x.meaning==='HISTORICAL_PG17_ONLY_NO_GRAPH'));
});
test('G2-CONTRACT-10 cross-front owners distinct',()=>{
 for(const key of ['s0','meta','infra','openai','frontend'])assert.ok(data.ownership[key]);
 assert.notEqual(data.ownership.s0,data.ownership.meta);
});
