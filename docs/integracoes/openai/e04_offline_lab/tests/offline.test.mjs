// E04 Offline Lab / synthetic regression. Run: node --test tests/offline.test.mjs
import test from 'node:test';
import assert from 'node:assert/strict';
import {versionGate,validateF01,validateF02,prepareF03History,validateF03Proposal} from '../core.mjs';

function defineCases(api,assert,test){
  const {versionGate,validateF01,validateF02,prepareF03History,validateF03Proposal}=api;
  const base=()=>({authenticated:true,authorized:true,tenantAllowed:true,storeId:"FAKE_A",caseId:"K1",expected:{case:1,cycle:2,form:3,catalog:4,assignment:5},current:{case:1,cycle:2,form:3,catalog:4,assignment:5}});
  const f01=()=>({scope:base(),owner:"ai",handoff:false,humanized:false,nowMs:1700000000000,sources:[{id:"fA",storeId:"FAKE_A",approved:true,active:true,mode:"current"}]});
  const p01=()=>({text:"Preço sujeito a confirmação.",commercial:true,sourceIds:["fA"],modality:"text"});
  const f02=()=>({scope:base(),explicitS0Request:true,optOut:false,handoffPlanReuse:false,ownerRoute:"human",purpose:"post_human",maxAttempts:2,windowStart:"2026-11-01T10:00:00-03:00",windowEnd:"2026-11-10T10:00:00-03:00",allowedTemplates:[{id:"templ",version:"v1",storeId:"FAKE_A",purpose:"post_human",active:true}]});
  const p02=()=>({attempts:[{templateId:"templ",version:"v1",purpose:"post_human",at:"2026-11-02T10:00:00-03:00"}],finalTemplate:{templateId:"templ",version:"v1",purpose:"post_human",at:"2026-11-05T10:00:00-03:00"}});
  const f03=()=>({scope:base(),humanClosed:true,closureAuthenticated:true,closureId:"E1",personId:"P1",cutoffSequence:7,records:[{id:"m1",storeId:"FAKE_A",personId:"P1",caseId:"K0",sequence:1,author:"customer",kind:"text",available:true,contentAuthorized:true},{id:"m7",storeId:"FAKE_A",personId:"P1",caseId:"K1",sequence:7,author:"customer",kind:"text",available:true,contentAuthorized:true},{id:"m8",storeId:"FAKE_A",personId:"P1",caseId:"K1",sequence:8,author:"customer",kind:"text",available:true,contentAuthorized:true}],catalog:[{code:"renda",essential:true},{code:"cor",essential:false}],verifiedWithdrawalSourceIds:["m7"]});
  const p03=()=>({fields:[{code:"renda",value:3500,sourceId:"m7"},{code:"cor",value:"azul",sourceId:"m1"}],conflicts:[],commercialAdvisory:null});
  test("GATE01_accepted_separate_versions",()=>assert.equal(versionGate(base()).status,"READY"));
  test("GATE02_unauth_precedes_stale",()=>{let x=base();x.authorized=false;x.current.form=9;assert.deepEqual(versionGate(x),{status:"DENIED"});});
  test("GATE03_stale_form",()=>{let x=base();x.current.form=9;assert.equal(versionGate(x).status,"STALE");});
  test("GATE04_stale_cycle_distinct_from_form",()=>{let x=base();x.current.cycle=9;assert.equal(versionGate(x).status,"STALE");});
  test("GATE05_invalid_missing_tenant",()=>{let x=base();delete x.storeId;assert.equal(versionGate(x).status,"INVALID_INPUT");});
  test("GATE06_mismatched_version_keys",()=>{let x=base();delete x.current.form;assert.equal(versionGate(x).status,"INVALID_INPUT");});
  test("F01_01_valid_proposal_never_send",()=>assert.deepEqual(validateF01(f01(),p01()),{status:"PROPOSED"}));
  test("F01_02_handoff_blocks",()=>{let x=f01();x.handoff=true;assert.equal(validateF01(x,p01()).status,"DENIED");});
  test("F01_03_human_owner_blocks",()=>{let x=f01();x.owner="human";assert.equal(validateF01(x,p01()).status,"DENIED");});
  test("F01_04_roster_never_pass",()=>{let x=f01();x.staffRoster=["Consultor 1"];assert.equal(validateF01(x,p01()).status,"INVALID_INPUT");});
  test("F01_05_cross_tenant_input",()=>{let x=f01();x.sources[0].storeId="FAKE_B";assert.equal(validateF01(x,p01()).status,"INVALID_INPUT");});
  test("F01_06_expired_offer",()=>{let x=f01();x.sources[0].validUntil="2020-01-01T00:00:00Z";assert.equal(validateF01(x,p01()).status,"SOURCE_INVALID");});
  test("F01_07_historical_not_current_offer",()=>{let x=f01();x.sources[0].mode="historical";assert.equal(validateF01(x,p01()).status,"SOURCE_INVALID");});
  test("F01_08_model_cannot_set_sold",()=>{let x=p01();x.status="vendido";assert.equal(validateF01(f01(),x).status,"SCHEMA_INVALID");});
  test("F01_09_missing_source_for_commercial",()=>{let x=p01();x.sourceIds=[];assert.equal(validateF01(f01(),x).status,"SOURCE_INVALID");});
  test("F02_01_plan_no_send",()=>assert.deepEqual(validateF02(f02(),p02()),{status:"PROPOSED"}));
  test("F02_02_no_separate_S0_request",()=>{let x=f02();x.explicitS0Request=false;assert.equal(validateF02(x,p02()).status,"DENIED");});
  test("F02_03_optout_blocks",()=>{let x=f02();x.optOut=true;assert.equal(validateF02(x,p02()).status,"DENIED");});
  test("F02_04_prior_plan_cannot_revive",()=>{let x=f02();x.handoffPlanReuse=true;assert.equal(validateF02(x,p02()).status,"DENIED");});
  test("F02_05_unknown_template",()=>{let x=p02();x.attempts[0].templateId="unknown";assert.equal(validateF02(f02(),x).status,"SOURCE_INVALID");});
  test("F02_06_version_mismatch",()=>{let x=p02();x.attempts[0].version="v2";assert.equal(validateF02(f02(),x).status,"SOURCE_INVALID");});
  test("F02_07_no_slot_fill",()=>{let x=p02();x.attempts[0].slots={nome:"João"};assert.equal(validateF02(f02(),x).status,"SCHEMA_INVALID");});
  test("F02_08_no_sent_claim",()=>{let x=p02();x.sent=true;assert.equal(validateF02(f02(),x).status,"SCHEMA_INVALID");});
  test("F02_09_max_attempts",()=>{let x=p02();x.attempts.push({...x.attempts[0],at:"2026-11-03T10:00:00-03:00"}, {...x.attempts[0],at:"2026-11-04T10:00:00-03:00"});assert.equal(validateF02(f02(),x).status,"SCHEMA_INVALID");});
  test("F02_10_final_before_regular",()=>{let x=p02();x.finalTemplate.at="2026-11-01T10:00:00-03:00";assert.equal(validateF02(f02(),x).status,"SCHEMA_INVALID");});
  test("F02_11_cross_store_catalog_blocked",()=>{let x=f02();x.allowedTemplates[0].storeId="FAKE_B";assert.equal(validateF02(x,p02()).status,"INVALID_INPUT");});
  test("F03_01_multi_case_cutoff",()=>{let h=prepareF03History(f03());assert.equal(h.status,"READY");assert.deepEqual(h.sources.map(x=>x.id),["m1","m7"]);assert.deepEqual(h.sources.map(x=>x.caseId),["K0","K1"]);});
  test("F03_02_handoff_not_closure",()=>{let x=f03();x.humanClosed=false;assert.equal(prepareF03History(x).status,"DENIED");});
  test("F03_03_unauthenticated_closure",()=>{let x=f03();x.closureAuthenticated=false;assert.equal(prepareF03History(x).status,"DENIED");});
  test("F03_04_cross_tenant_evidence",()=>{let x=f03();x.records[0].storeId="FAKE_B";assert.equal(prepareF03History(x).status,"INVALID_INPUT");});
  test("F03_05_cross_person_evidence",()=>{let x=f03();x.records[0].personId="P2";assert.equal(prepareF03History(x).status,"INVALID_INPUT");});
  test("F03_06_unavailable_media_no_content",()=>{let x=f03();x.records[0]={id:"a1",storeId:"FAKE_A",personId:"P1",caseId:"K0",sequence:1,author:"customer",kind:"media",available:false,contentAuthorized:false};let y=prepareF03History(x);assert.equal(y.status,"READY");assert.equal(y.sources[0].available,false);assert.equal("content" in y.sources[0],false);});
  test("F03_07_available_without_authorization",()=>{let x=f03();x.records[0].contentAuthorized=false;assert.equal(prepareF03History(x).status,"DENIED");});
  test("F03_08_optional_proposed",()=>{let x=f03(), h=prepareF03History(x);assert.equal(validateF03Proposal(x,h,p03()).status,"PROPOSED");});
  test("F03_09_missing_essential_review",()=>{let x=f03(),h=prepareF03History(x),p=p03();p.fields=p.fields.filter(y=>y.code!=="renda");assert.equal(validateF03Proposal(x,h,p).status,"REVIEW_REQUIRED");});
  test("F03_10_missing_optional_not_block",()=>{let x=f03(),h=prepareF03History(x),p=p03();p.fields=p.fields.filter(y=>y.code!=="cor");assert.equal(validateF03Proposal(x,h,p).status,"PROPOSED");});
  test("F03_11_source_after_cutoff",()=>{let x=f03(),h=prepareF03History(x),p=p03();p.fields[0].sourceId="m8";assert.equal(validateF03Proposal(x,h,p).status,"SOURCE_INVALID");});
  test("F03_12_invalid_field",()=>{let x=f03(),h=prepareF03History(x),p=p03();p.fields[0].code="cpf";assert.equal(validateF03Proposal(x,h,p).status,"SOURCE_INVALID");});
  test("F03_13_sold_never_model",()=>{let x=f03(),h=prepareF03History(x),p=p03();p.commercialAdvisory={kind:"vendido",sourceIds:["m7"]};assert.equal(validateF03Proposal(x,h,p).status,"SOURCE_INVALID");});
  test("F03_14_withdrawal_advisory_only",()=>{let x=f03(),h=prepareF03History(x),p=p03();p.commercialAdvisory={kind:"perdido",sourceIds:["m7"]};assert.equal(validateF03Proposal(x,h,p).status,"PROPOSED");});
  test("F03_15_unverified_withdrawal_denied",()=>{let x=f03(),h=prepareF03History(x),p=p03();p.commercialAdvisory={kind:"perdido",sourceIds:["m1"]};assert.equal(validateF03Proposal(x,h,p).status,"SOURCE_INVALID");});
  test("F03_16_conflict_requires_review",()=>{let x=f03(),h=prepareF03History(x),p=p03();p.conflicts=[{code:"renda",sourceIds:["m1","m7"]}];assert.equal(validateF03Proposal(x,h,p).status,"REVIEW_REQUIRED");});
  test("F03_17_stale_apply_blocked",()=>{let x=f03(),h=prepareF03History(x);x.scope.current.form=7;assert.equal(validateF03Proposal(x,h,p03()).status,"STALE");});
  test("F03_18_revocation_precedes_stale",()=>{let x=f03(),h=prepareF03History(x);x.scope.current.form=7;x.scope.authorized=false;assert.deepEqual(validateF03Proposal(x,h,p03()),{status:"DENIED"});});

  test("F01_10_missing_handoff_is_denied",()=>{let x=f01();delete x.handoff;assert.equal(validateF01(x,p01()).status,"DENIED");});
  test("F02_12_missing_optout_is_denied",()=>{let x=f02();delete x.optOut;assert.equal(validateF02(x,p02()).status,"DENIED");});
  test("F02_13_posthuman_requires_human_route",()=>{let x=f02();x.ownerRoute="seller_ai";assert.equal(validateF02(x,p02()).status,"DENIED");});
  test("F03_20_five_version_domains_required",()=>{let x=f03();delete x.scope.expected.form;delete x.scope.current.form;assert.equal(prepareF03History(x).status,"INVALID_INPUT");});
  test("F03_21_cutoff_snapshot_binds_versions",()=>{let x=f03(),h=prepareF03History(x);x.scope.expected.form=9;x.scope.current.form=9;assert.equal(validateF03Proposal(x,h,p03()).status,"INVALID_INPUT");});
  test("F03_19_no_mutation_claim",()=>{let x=f03(),h=prepareF03History(x),p=p03();p.applied=true;assert.equal(validateF03Proposal(x,h,p).status,"SCHEMA_INVALID");});
}

defineCases({versionGate,validateF01,validateF02,prepareF03History,validateF03Proposal},assert,test);
