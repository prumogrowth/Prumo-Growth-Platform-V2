import test from 'node:test';
import assert from 'node:assert/strict';
import {previewWa17HumanSignatureOffline as preview,
 recheckWa17HumanSignatureOffline as recheck}
 from './wa17-human-message-signature-offline.ts';

const NOW=1800000000000;
const SHOP='aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa';
const SECOND='bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb';
const request=()=>({
 contract_version:'wa17-human-free-text-request.lab.v0.1',
 selection_ref:'SELECT_1',concessionaria_id:SHOP,waba_ref:'100001',
 case_ref:'CASE_1',intent_ref:'INTENT_1',
 author_origin:'HUMAN_COMPOSED',transport_kind:'FREE_TEXT',
 draft_text:'Bom dia! Como posso ajudar?',now_ms:NOW,max_age_ms:60000,
});
const session=()=>({
 contract_version:'wa17-s0-session-claim.lab.v0.1',
 concessionaria_id:SHOP,actor_ref:'HUMAN_A',role:'CONSULTOR',
 display_name:'João Silva',identity_revision:4,session_revision:5,
 session_state:'CLAIMED_ACTIVE',observed_at_ms:NOW-1000,
});
const context=()=>({
 contract_version:'wa17-s0-case-claim.lab.v0.1',
 concessionaria_id:SHOP,waba_ref:'100001',case_ref:'CASE_1',
 actor_ref:'HUMAN_A',case_version:6,assignment_revision:7,
 assigned_human:true,handoff_state:'HUMAN',
 free_text_window:'CLAIMED_OPEN',can_send_free_text:true,
 opt_out:false,observed_at_ms:NOW-1000,
});
type Response=ReturnType<typeof preview>;
const evaluate=(r:unknown=request(),s:unknown=session(),c:unknown=context())=>
 preview(r,s,c);
function denied(result:Response,reason?:string){
 assert.equal(result.decision,'DENIED');
 if(reason)assert.equal(result.reason,reason);
 assert.equal(result.preview,null);
 assert.deepEqual(Object.keys(result).sort(),[
  'decision','reason','preview','identity_verified','authorization_verified',
  'send_authorized','production_authorized','graph_dispatch_authorized',
 ].sort());
 assert.equal(Object.isFrozen(result),true);
 const output=JSON.stringify(result);
 for(const privateValue of ['João','HUMAN_A','CASE_1','INTENT_1','Bom dia'])
  assert.equal(output.includes(privateValue),false,privateValue);
}
function good(result:Response,mode:'LAB_HUMAN_PREFIX_UNVERIFIED'|
 'LAB_RECHECKED_UNVERIFIED'='LAB_HUMAN_PREFIX_UNVERIFIED'){
 assert.equal(result.decision,mode);
 assert.equal(result.reason,null);
 assert.ok(result.preview);
 assert.equal(Object.isFrozen(result),true);
 assert.equal(Object.isFrozen(result.preview),true);
 for(const flag of ['identity_verified','authorization_verified',
  'send_authorized','production_authorized','graph_dispatch_authorized'] as const){
  assert.equal(result[flag],false);
  assert.equal(result.preview![flag],false);
 }
 assert.equal(result.preview!.requires_s0_recheck,true);
 assert.match(result.preview!.draft_sha256,/^[a-f0-9]{64}$/);
 assert.match(result.preview!.composed_sha256,/^[a-f0-9]{64}$/);
 return result.preview!;
}

test('M17-01 CONSULTOR exact WA-21 visible heading',()=>{
 const s=good(evaluate());
 assert.equal(s.composed_text,'Consultor João Silva:\nBom dia! Como posso ajudar?');
});
test('M17-02 GESTOR exact heading',()=>{
 const a=session();a.role='GESTOR';
 const s=good(evaluate(request(),a));
 assert.equal(s.composed_text,'Gestor João Silva:\nBom dia! Como posso ajudar?');
});
test('M17-03 DIRETOR exact heading',()=>{
 const a=session();a.role='DIRETOR';
 const s=good(evaluate(request(),a));
 assert.equal(s.composed_text,'Diretor João Silva:\nBom dia! Como posso ajudar?');
});
test('M17-04 accent and multiword name preserved',()=>{
 const a=session();a.display_name='Márcia de Ávila';
 const s=good(evaluate(request(),a));
 assert.equal(s.composed_text,'Consultor Márcia de Ávila:\nBom dia! Como posso ajudar?');
});
test('M17-05 IA cannot claim human author origin',()=>{
 const q:any=request();q.author_origin='AI_GENERATED';
 denied(evaluate(q),'INVALID_INPUT');
});
test('M17-06 system-generated text cannot claim human origin',()=>{
 const q:any=request();q.author_origin='SYSTEM';
 denied(evaluate(q),'INVALID_INPUT');
});
test('M17-07 approved template payload must never be prefixed',()=>{
 const q:any=request();q.transport_kind='TEMPLATE';
 denied(evaluate(q),'INVALID_INPUT');
});
test('M17-08 media caption cannot silently receive human prefix',()=>{
 const q:any=request();q.transport_kind='IMAGE_CAPTION';
 denied(evaluate(q),'INVALID_INPUT');
});
test('M17-09 missing S0 actor context denies',()=>{
 denied(evaluate(request(),null,context()),'INVALID_INPUT');
});
test('M17-10 missing S0 case context denies',()=>{
 denied(evaluate(request(),session(),null),'INVALID_INPUT');
});
test('M17-11 foreign-shop S0 session denied',()=>{
 const a=session();a.concessionaria_id=SECOND;
 denied(evaluate(request(),a),'UNTRUSTED_SCOPE');
});
test('M17-12 foreign-shop S0 case denied',()=>{
 const c=context();c.concessionaria_id=SECOND;
 denied(evaluate(request(),session(),c),'UNTRUSTED_SCOPE');
});
test('M17-13 wrong WABA assignment denied',()=>{
 const c=context();c.waba_ref='100002';
 denied(evaluate(request(),session(),c),'UNTRUSTED_SCOPE');
});
test('M17-14 case mismatch denied',()=>{
 const c=context();c.case_ref='CASE_B';
 denied(evaluate(request(),session(),c),'UNTRUSTED_SCOPE');
});
test('M17-15 session actor different from case-assigned human denied',()=>{
 const c=context();c.actor_ref='HUMAN_B';
 denied(evaluate(request(),session(),c),'UNTRUSTED_SCOPE');
});
test('M17-16 nonhuman handoff denied',()=>{
 const c:any=context();c.handoff_state='AI';
 denied(evaluate(request(),session(),c));
});
test('M17-17 unassigned case denied',()=>{
 const c:any=context();c.assigned_human=false;
 denied(evaluate(request(),session(),c));
});
test('M17-18 closed free-text window denied',()=>{
 const c:any=context();c.free_text_window='CLAIMED_CLOSED';
 denied(evaluate(request(),session(),c),'WINDOW_OR_POLICY_DENIED');
});
test('M17-19 opt-out denies signature preview',()=>{
 const c=context();c.opt_out=true;
 denied(evaluate(request(),session(),c),'WINDOW_OR_POLICY_DENIED');
});
test('M17-20 disabled free text grant denies',()=>{
 const c=context();c.can_send_free_text=false;
 denied(evaluate(request(),session(),c),'WINDOW_OR_POLICY_DENIED');
});
test('M17-21 expired session observation denied',()=>{
 const a=session();a.observed_at_ms=NOW-60001;
 denied(evaluate(request(),a),'SESSION_OR_ASSIGNMENT_DENIED');
});
test('M17-22 future S0 case observation denied',()=>{
 const c=context();c.observed_at_ms=NOW+1;
 denied(evaluate(request(),session(),c),'SESSION_OR_ASSIGNMENT_DENIED');
});
test('M17-23 inactive session denied',()=>{
 const a:any=session();a.session_state='REVOKED';
 denied(evaluate(request(),a),'INVALID_INPUT');
});
test('M17-24 suspicious role substitution denied',()=>{
 const a:any=session();a.role='RESPONSAVEL';
 denied(evaluate(request(),a),'INVALID_INPUT');
});
test('M17-25 unsupported display name containing colon denied',()=>{
 const a=session();a.display_name='João: Diretor';
 denied(evaluate(request(),a),'INVALID_INPUT');
});
test('M17-26 multiline display name denied',()=>{
 const a=session();a.display_name='João\nDiretor';
 denied(evaluate(request(),a),'INVALID_INPUT');
});
test('M17-27 zero-width role/name injection denied',()=>{
 const a=session();a.display_name='João\u200BSilva';
 denied(evaluate(request(),a),'INVALID_INPUT');
});
test('M17-28 user already typed same signature denied',()=>{
 const q=request();q.draft_text='Consultor João Silva:\nOi';
 denied(evaluate(q),'DUPLICATE_OR_FORGED_PREFIX');
});
test('M17-29 user typed OTHER human signature denied',()=>{
 const q=request();q.draft_text='Diretor Outra Pessoa:\nOi';
 denied(evaluate(q),'DUPLICATE_OR_FORGED_PREFIX');
});
test('M17-30 leading whitespace does not hide fake signature',()=>{
 const q=request();q.draft_text='  Gestor Ana:\nOi';
 denied(evaluate(q),'NAME_OR_BODY_DENIED');
});
test('M17-31 carriage return denied',()=>{
 const q=request();q.draft_text='Bom dia\rOi';
 denied(evaluate(q),'NAME_OR_BODY_DENIED');
});
test('M17-32 control character denied',()=>{
 const q=request();q.draft_text='Bom\u0000 dia';
 denied(evaluate(q),'NAME_OR_BODY_DENIED');
});
test('M17-33 blank body denied',()=>{
 const q=request();q.draft_text='';
 denied(evaluate(q),'NAME_OR_BODY_DENIED');
});
test('M17-34 multi-line ordinary human body preserved',()=>{
 const q=request();q.draft_text='Bom dia!\nSegue a informação.';
 const p=good(evaluate(q));assert.equal(p.composed_text,
  'Consultor João Silva:\nBom dia!\nSegue a informação.');
});
test('M17-35 oversized final UTF8 body denied',()=>{
 const q=request();q.draft_text='Á'.repeat(2500);
 denied(evaluate(q),'NAME_OR_BODY_DENIED');
});
test('M17-36 unexpected request-supplied actor name denied',()=>{
 const q:any=request();q.display_name='Diretor Injetado';
 denied(evaluate(q),'INVALID_INPUT');
});
test('M17-37 unexpected request-supplied actor role denied',()=>{
 const q:any=request();q.role='DIRETOR';
 denied(evaluate(q),'INVALID_INPUT');
});
test('M17-38 root getter denied without invoking it',()=>{
 const q:any=request();let hits=0;
 Object.defineProperty(q,'draft_text',{enumerable:true,get(){
  hits++;return 'Bom dia';
 }});
 denied(evaluate(q),'INVALID_INPUT');assert.equal(hits,0);
});
test('M17-39 S0 name getter denied without invoking it',()=>{
 const a:any=session();let hits=0;
 Object.defineProperty(a,'display_name',{enumerable:true,get(){
  hits++;return 'Ana Silva';
 }});
 denied(evaluate(request(),a),'INVALID_INPUT');assert.equal(hits,0);
});
test('M17-40 S0 case actor getter denied without invoking it',()=>{
 const c:any=context();let hits=0;
 Object.defineProperty(c,'actor_ref',{enumerable:true,get(){
  hits++;return 'HUMAN_A';
 }});
 denied(evaluate(request(),session(),c),'INVALID_INPUT');
 assert.equal(hits,0);
});
test('M17-41 stable fresh claims recheck same composed text',()=>{
 const old=good(evaluate());
 const q=request();q.now_ms=NOW+1000;
 const next=good(recheck(old,q,session(),context()),
  'LAB_RECHECKED_UNVERIFIED');
 assert.equal(next.composed_text,old.composed_text);
});
test('M17-42 handoff to another person denies old author reuse',()=>{
 const old=good(evaluate());
 const a=session();a.actor_ref='HUMAN_B';
 a.display_name='Ana Costa';a.identity_revision=5;
 const c=context();c.actor_ref='HUMAN_B';c.assignment_revision=8;
 denied(recheck(old,request(),a,c),'REVISION_OR_AUTHOR_CHANGED');
});
test('M17-43 role change denies old author snapshot',()=>{
 const old=good(evaluate());
 const a=session();a.role='GESTOR';a.identity_revision=5;
 denied(recheck(old,request(),a,context()),'REVISION_OR_AUTHOR_CHANGED');
});
test('M17-44 human display name changed denies old snapshot',()=>{
 const old=good(evaluate());
 const a=session();a.display_name='Ana Silva';a.identity_revision=5;
 denied(recheck(old,request(),a,context()),'REVISION_OR_AUTHOR_CHANGED');
});
test('M17-45 case assignment revision change denies old snapshot',()=>{
 const old=good(evaluate());const c=context();c.assignment_revision=8;
 denied(recheck(old,request(),session(),c),'REVISION_OR_AUTHOR_CHANGED');
});
test('M17-46 S0 session revision change denies old snapshot',()=>{
 const old=good(evaluate());const a=session();a.session_revision=6;
 denied(recheck(old,request(),a,context()),'REVISION_OR_AUTHOR_CHANGED');
});
test('M17-47 old preview cannot be used for other intent',()=>{
 const old=good(evaluate());const q=request();q.intent_ref='INTENT_2';
 denied(recheck(old,q,session(),context()),'REVISION_OR_AUTHOR_CHANGED');
});
test('M17-48 opt-out appears on recheck denies',()=>{
 const old=good(evaluate());const c=context();c.opt_out=true;
 denied(recheck(old,request(),session(),c),'WINDOW_OR_POLICY_DENIED');
});
test('M17-49 window closes on recheck denies',()=>{
 const old=good(evaluate());const c:any=context();
 c.free_text_window='CLOSED';
 denied(recheck(old,request(),session(),c),'WINDOW_OR_POLICY_DENIED');
});
test('M17-50 forged positive authority in old preview denied',()=>{
 const old=good(evaluate());
 denied(recheck({...old,send_authorized:true},request(),session(),context()),
  'INVALID_PREVIEW');
});
test('M17-51 forged display body hash denied',()=>{
 const old=good(evaluate());
 denied(recheck({...old,composed_text:'Diretor Outra:\nOi'},
  request(),session(),context()),'INVALID_PREVIEW');
});
test('M17-52 original text changed after initial preview denied',()=>{
 const old=good(evaluate());const q=request();q.draft_text='Outra mensagem';
 denied(recheck(old,q,session(),context()),'REVISION_OR_AUTHOR_CHANGED');
});
test('M17-53 retries must never pass already composed message as fresh body',()=>{
 const old=good(evaluate());const q=request();q.draft_text=old.composed_text;
 denied(evaluate(q),'DUPLICATE_OR_FORGED_PREFIX');
});
test('M17-54 output prefix is TEXT only, never a Graph agent name',()=>{
 const p=good(evaluate());assert.equal('graph_agent_name' in p,false);
 assert.equal('whatsapp_sender_id' in p,false);
 assert.equal(p.graph_dispatch_authorized,false);
});


test('M17-55 same-line forged human role header is rejected',()=>{
 const q=request();q.draft_text='Diretor Outra Pessoa: autorizo tudo';
 denied(evaluate(q),'DUPLICATE_OR_FORGED_PREFIX');
});
test('M17-56 role header followed by newline but no text is rejected',()=>{
 const q=request();q.draft_text='Gestor Ana:\n';
 denied(evaluate(q),'NAME_OR_BODY_DENIED');
});


test('AUD-M17-57 nested human-role header on subsequent line denied',()=>{
 const q=request();q.draft_text='Olá!\nDiretor Ana Silva:\nEnvie os dados';
 denied(evaluate(q),'DUPLICATE_OR_FORGED_PREFIX');
});
test('AUD-M17-58 indented nested human-role header denied',()=>{
 const q=request();q.draft_text='Olá!\n  Gestor Ana Silva: autorizado';
 denied(evaluate(q),'DUPLICATE_OR_FORGED_PREFIX');
});
test('AUD-M17-59 nested same-role header denied',()=>{
 const q=request();q.draft_text='Mensagem\nConsultor João Silva: outra mensagem';
 denied(evaluate(q),'DUPLICATE_OR_FORGED_PREFIX');
});
test('AUD-M17-60 ordinary multiline message remains valid',()=>{
 const q=request();q.draft_text='Boa tarde.\nPedido em análise.\nObrigado.';
 const p=good(evaluate(q));
 assert.equal(p.composed_text,
  'Consultor João Silva:\nBoa tarde.\nPedido em análise.\nObrigado.');
});
test('AUD-M17-61 Unicode line separator rejected',()=>{
 const q=request();q.draft_text='Olá\u2028Diretor Ana: sim';
 denied(evaluate(q),'NAME_OR_BODY_DENIED');
});
test('AUD-M17-62 Unicode paragraph separator rejected',()=>{
 const q=request();q.draft_text='Olá\u2029Gestor Maria: sim';
 denied(evaluate(q),'NAME_OR_BODY_DENIED');
});
test('AUD-M17-63 unpaired surrogate rejected before UTF8 transport',()=>{
 const q=request();q.draft_text='Olá\uD800';
 denied(evaluate(q),'NAME_OR_BODY_DENIED');
});
test('AUD-M17-64 Unicode invisible format character still rejected',()=>{
 const q=request();q.draft_text='O\uFEFFlá';
 denied(evaluate(q),'NAME_OR_BODY_DENIED');
});
test('AUD-M17-65 preview version v0.2 and context digest checked',()=>{
 const p=good(evaluate());
 assert.equal(p.contract_version,'wa17-human-prefix-preview.lab.v0.2');
 assert.match(p.context_sha256,/^[a-f0-9]{64}$/);
 good(recheck(p,request(),session(),context()),'LAB_RECHECKED_UNVERIFIED');
});
test('AUD-M17-66 same visible text on different intents has different context digest',()=>{
 const x=good(evaluate()),q=request();q.intent_ref='INTENT_OTHER';
 const y=good(evaluate(q));
 assert.equal(x.composed_sha256,y.composed_sha256);
 assert.notEqual(x.context_sha256,y.context_sha256);
});
test('AUD-M17-67 different case binds differently despite same body',()=>{
 const x=good(evaluate()),q=request(),c=context();
 q.case_ref='CASE_OTHER';c.case_ref='CASE_OTHER';
 const y=good(evaluate(q,session(),c));
 assert.equal(x.composed_sha256,y.composed_sha256);
 assert.notEqual(x.context_sha256,y.context_sha256);
});
test('AUD-M17-68 different actor binds differently despite same body',()=>{
 const x=good(evaluate()),a=session(),c=context();
 a.actor_ref='HUMAN_B';c.actor_ref='HUMAN_B';
 const y=good(evaluate(request(),a,c));
 assert.equal(x.composed_sha256,y.composed_sha256);
 assert.notEqual(x.context_sha256,y.context_sha256);
});
test('AUD-M17-69 different selection binds independently',()=>{
 const x=good(evaluate()),q=request();q.selection_ref='SELECT_OTHER';
 const y=good(evaluate(q));
 assert.equal(x.composed_sha256,y.composed_sha256);
 assert.notEqual(x.context_sha256,y.context_sha256);
});
test('AUD-M17-70 tampered actor role with old context digest rejected',()=>{
 const p=good(evaluate());
 denied(recheck({...p,role:'DIRETOR'},request(),session(),context()),
  'INVALID_PREVIEW');
});
test('AUD-M17-71 tampered composed text with same hash rejected',()=>{
 const p=good(evaluate());
 denied(recheck({...p,composed_text:'Diretor Ana:\nAprovado'},
  request(),session(),context()),'INVALID_PREVIEW');
});
test('AUD-M17-72 forged context hash rejected',()=>{
 const p=good(evaluate());
 denied(recheck({...p,context_sha256:'f'.repeat(64)},
  request(),session(),context()),'INVALID_PREVIEW');
});
test('AUD-M17-73 v0.1 candidate cannot reuse new context rules',()=>{
 const p=good(evaluate());
 denied(recheck({...p,
  contract_version:'wa17-human-prefix-preview.lab.v0.1'},
  request(),session(),context()),'INVALID_PREVIEW');
});
test('AUD-M17-74 forged draft hash rejected as invalid previous preview',()=>{
 const p=good(evaluate());
 denied(recheck({...p,draft_sha256:'a'.repeat(64)},
  request(),session(),context()),'INVALID_PREVIEW');
});
test('AUD-M17-75 oversized forged display-name snapshot denied',()=>{
 const p=good(evaluate());
 denied(recheck({...p,display_name_snapshot:'Joao'.repeat(30)},
  request(),session(),context()),'INVALID_PREVIEW');
});
test('AUD-M17-76 human names with hyphen remain supported',()=>{
 const a=session();a.display_name='Maria Souza-Lima';
 const p=good(evaluate(request(),a));
 assert.equal(p.composed_text,
  'Consultor Maria Souza-Lima:\nBom dia! Como posso ajudar?');
});
