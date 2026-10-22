import test from 'node:test';
import assert from 'node:assert/strict';
import {ACTORS, getActor, hasMockCaseOnlyScope, hasMockCaseScope, visibleConversations, visibleMockShops} from '../fixtures.mjs';
import {copyCFDemoFixtures} from '../cf-op-02.mjs';
import {DEMO_SHARED_LEADS,projectSharedNewLeadQueue,requestMockQueueAction} from '../distribution-view.mjs';
import {projectManagedTeam} from '../team-operations.mjs';
import {projectManagerPausePreview} from '../team-pause-preview.mjs';

const records=()=>copyCFDemoFixtures();

test('D-AL-06 fila nova sem titular visível aos dois Gestores concedidos na mesma loja',()=>{
  const marina=projectSharedNewLeadQueue('marina','aurora');
  const daniel=projectSharedNewLeadQueue('daniel','aurora');
  assert.equal(marina.visibility,'shared_queue_demo');
  assert.deepEqual(marina.available.map(x=>x.id),['FILA-A-01']);
  assert.deepEqual(daniel.available.map(x=>x.id),marina.available.map(x=>x.id));
  assert.equal(marina.summary.claimed,1);
  assert.equal(marina.summary.redistributed,1);
});

test('fila respeita concessão gerencial e não cria consulta pelo Consultor/suspenso',()=>{
  assert.equal(projectSharedNewLeadQueue('rafael','aurora').visibility,'forbidden');
  assert.equal(projectSharedNewLeadQueue('otavio','aurora').visibility,'forbidden');
  assert.equal(projectSharedNewLeadQueue('ghost','aurora').visibility,'forbidden');
  assert.equal(projectSharedNewLeadQueue('marina','inexistente').visibility,'forbidden');
  assert.deepEqual(projectSharedNewLeadQueue('marina','horizonte').available.map(x=>x.id),['FILA-H-01']);
});

test('fila nova é distinta de carteira pausada e de etapa IA antiga',()=>{
  const ids=projectSharedNewLeadQueue('marina','aurora').available.map(x=>x.id);
  assert.ok(!ids.includes('A-112')); // fila protegida de caso anterior
  assert.ok(!ids.includes('A-101')); // conversa automatizada sem titular
  assert.ok(!visibleConversations(records(),'daniel','aurora').some(x=>x.id==='A-112'));
});

test('intenção de assunção não transfere titular e duas intenções não provam dois claims',()=>{
  const before=JSON.stringify(DEMO_SHARED_LEADS);
  const a=requestMockQueueAction('marina','aurora','FILA-A-01','queue-a01-v1','claim');
  const b=requestMockQueueAction('daniel','aurora','FILA-A-01','queue-a01-v1','claim');
  assert.equal(a.applied,false);assert.equal(b.applied,false);
  assert.equal(a.state,'requested_demo');assert.equal(b.state,'requested_demo');
  assert.equal(JSON.stringify(DEMO_SHARED_LEADS),before);
  assert.equal(projectSharedNewLeadQueue('marina','aurora').available.length,1);
});

test('assunção exige versão corrente e proíbe caso já assumido ou de outra loja',()=>{
  for(const [id,version] of [['FILA-A-01','outdated'],['FILA-A-02','queue-a02-v2'],
    ['FILA-H-01','queue-h01-v1']]){
    assert.throws(()=>requestMockQueueAction('marina','aurora',id,version,'claim'),/QUEUE_NOT_ELIGIBLE/);
  }
  assert.throws(()=>requestMockQueueAction('marina','aurora','FILA-A-01','queue-a01-v1','claim','rafael'),
    /QUEUE_CLAIM_TARGET_INVALID/);
});

test('atribuição individual deve ficar na própria equipe, sem conceder loja pela UI',()=>{
  const before=ACTORS.find(x=>x.id==='lia').shops.slice();
  const req=requestMockQueueAction('marina','aurora','FILA-A-01','queue-a01-v1','assign_team','lia');
  assert.equal(req.assigneeId,'lia');assert.equal(req.applied,false);
  assert.deepEqual(ACTORS.find(x=>x.id==='lia').shops,before);
  assert.throws(()=>requestMockQueueAction('marina','aurora','FILA-A-01','queue-a01-v1','assign_team','bianca'),
    /QUEUE_ASSIGNEE_OUT_OF_TEAM/);
  assert.throws(()=>requestMockQueueAction('daniel','aurora','FILA-A-01','queue-a01-v1','assign_team','otavio'),
    /QUEUE_ASSIGNEE_OUT_OF_TEAM/);
});

test('projeções desconhecidas, falsas, duplicadas ou inconsistentes não habilitam claim',()=>{
  const base={...DEMO_SHARED_LEADS[0]};
  const invalid=[
    {...base,origin:'browser'}, {...base,queueState:'unassigned',assignedTo:'rafael'},
    {...base,queueState:'claimed',assignedTo:null}, {...base,versionRef:''},
    {...base,kind:'protected_case'}, {...base,allowedActionsProjection:'claim'}
  ];
  for(const row of invalid){
    const view=projectSharedNewLeadQueue('marina','aurora',[row]);
    assert.ok(view.available.length===0 || view.available[0].actions.length===0);
  }
  assert.equal(projectSharedNewLeadQueue('marina','aurora',[base,base]).available.length,0);
});

test('escopo excepcional Lia/Aurora é estritamente A-117 e preserva histórico de concessões',()=>{
  const rows=records(),special=rows.find(x=>x.id==='A-117');
  assert.equal(hasMockCaseOnlyScope(special,'lia','aurora'),true);
  assert.equal(hasMockCaseScope(special,'lia','aurora'),true);
  assert.ok(visibleMockShops(rows,'lia').includes('aurora'));
  assert.deepEqual(visibleConversations(rows,'lia','aurora').map(x=>x.id),['A-117']);
  assert.ok(!getActor('lia').shops.includes('aurora'));
  assert.ok(visibleConversations(rows,'marina','aurora').some(x=>x.id==='A-117'));
  assert.ok(!visibleConversations(rows,'daniel','aurora').some(x=>x.id==='A-117'));
  assert.equal(visibleConversations(rows,'lia','horizonte').some(x=>x.id==='B-201'),true);
  assert.ok(projectManagedTeam('marina',rows).find(x=>x.id==='lia').cases>=2);
});

test('case-only recusa falsificação, versão vazia, titular antigo, outra loja e suspensão',()=>{
  const special=records().find(x=>x.id==='A-117'),p=special.caseOnlyAccessProjection;
  for(const altered of [
    {...special,assignedTo:'rafael'}, {...special,shopId:'horizonte'},
    {...special,caseOnlyAccessProjection:{...p,confirmed:false}},
    {...special,caseOnlyAccessProjection:{...p,scope:'all_shop'}},
    {...special,caseOnlyAccessProjection:{...p,actorId:'bianca'}},
    {...special,caseOnlyAccessProjection:{...p,versionRef:''}},
    {...special,caseOnlyAccessProjection:{...p,origin:'client'}}
  ]) assert.equal(hasMockCaseOnlyScope(altered,'lia','aurora'),false);
  assert.equal(hasMockCaseOnlyScope(special,'rafael','aurora'),false);
  assert.equal(hasMockCaseOnlyScope(special,'otavio','aurora'),false);
});

test('projeção de pausa não redistribui automaticamente caso com concessão excepcional',()=>{
  const rows=records(),before=rows.find(x=>x.id==='A-117').assignedTo;
  const view=projectManagerPausePreview('marina','lia',rows);
  assert.ok(view.cases.some(x=>x.caseId==='A-117'));
  assert.equal(rows.find(x=>x.id==='A-117').assignedTo,before);
});
