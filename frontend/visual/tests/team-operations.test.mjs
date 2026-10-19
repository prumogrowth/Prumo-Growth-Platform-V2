import test from 'node:test';
import assert from 'node:assert/strict';
import { ACTORS, managedOperators, visibleConversations } from '../fixtures.mjs';
import { copyCFDemoFixtures } from '../cf-op-02.mjs';
import { projectManagedTeam, requestMockIntake } from '../team-operations.mjs';

const records=()=>copyCFDemoFixtures();

test('G2: dois gestores enxergam equipes distintas, não a concessionária inteira',()=>{
  assert.deepEqual(managedOperators('marina').map(x=>x.id),['rafael','lia']);
  assert.deepEqual(managedOperators('daniel').map(x=>x.id),['bianca','otavio']);
  assert.deepEqual(managedOperators('rafael'),[]);
  const a=visibleConversations(records(),'marina','aurora');
  const b=visibleConversations(records(),'daniel','aurora');
  assert.ok(a.some(x=>x.id==='A-105'));
  assert.ok(!a.some(x=>x.id==='A-103'));
  assert.ok(b.some(x=>x.id==='A-103'));
  assert.ok(!b.some(x=>x.id==='A-105'));
});

test('G2: gestor vê casos da equipe por loja, sem acesso de outra equipe',()=>{
  const rows=records();
  const ma=visibleConversations(rows,'marina','horizonte');
  const da=visibleConversations(rows,'daniel','horizonte');
  assert.ok(ma.some(x=>x.id==='B-201'));
  assert.ok(!ma.some(x=>x.id==='B-203'));
  assert.ok(da.some(x=>x.id==='B-203'));
  assert.ok(!da.some(x=>x.id==='B-201'));
  assert.equal(visibleConversations(rows,'daniel','aurora').some(x=>x.id==='A-101'),false);
});

test('G2: status de novos leads não altera acesso humano ao caso já atribuído',()=>{
  const rows=records();
  const bianca=ACTORS.find(a=>a.id==='bianca');
  assert.equal(bianca.leadIntakeProjection,'paused_confirmed');
  assert.deepEqual(bianca.shops,['aurora','horizonte']);
  assert.ok(visibleConversations(rows,'bianca','aurora').some(x=>x.id==='A-103'));
  assert.ok(visibleConversations(rows,'bianca','horizonte').some(x=>x.id==='B-203'));
});

test('G2: equipe e lojas retornadas são somente leitura em projeção, não comandos',()=>{
  const rows=records(),members=projectManagedTeam('daniel',rows);
  assert.deepEqual(members.map(x=>x.id),['bianca','otavio']);
  assert.deepEqual(members[0].shops,['aurora','horizonte']);
  assert.equal(members[0].intake,'paused_confirmed');
  assert.equal(members[1].intake,'unavailable');
  assert.ok(Object.isFrozen(members[0].shops));
  assert.deepEqual(projectManagedTeam('rafael',rows),[]);
});

test('G2: gestor somente pode pedir pausa global de sua operadora elegível',()=>{
  const req=requestMockIntake('marina','rafael','pause');
  assert.equal(req.action,'pause');
  assert.equal(req.state,'requested_demo');
  assert.equal(req.scope,'all_granted_shops');
  assert.equal(ACTORS.find(x=>x.id==='rafael').leadIntakeProjection,'receiving');
});

test('G2: solicitação de retomada não efetiva a disponibilidade',()=>{
  const req=requestMockIntake('daniel','bianca','resume');
  assert.equal(req.state,'requested_demo');
  assert.equal(req.scope,'all_granted_shops');
  assert.equal(ACTORS.find(x=>x.id==='bianca').leadIntakeProjection,'paused_confirmed');
});

test('G2: gestor não pode controlar operador de outra equipe',()=>{
  for(const [manager,operator] of [['marina','bianca'],['daniel','rafael'],['rafael','bianca'],['marina','marina']]){
    assert.throws(()=>requestMockIntake(manager,operator,'pause'),/FORBIDDEN_TEAM/);
  }
});

test('G2: pausa e retomada não são alterações genéricas nem per-store',()=>{
  assert.throws(()=>requestMockIntake('marina','rafael','pause_aurora'),/INVALID_ACTION/);
  assert.throws(()=>requestMockIntake('daniel','bianca','pause'),/INVALID_TRANSITION/);
  assert.throws(()=>requestMockIntake('marina','rafael','resume'),/INVALID_TRANSITION/);
});

test('G2: suspensão de conta é distinta da pausa de entrada de leads',()=>{
  assert.throws(()=>requestMockIntake('daniel','otavio','pause'),/FORBIDDEN_TEAM/);
  const suspended=ACTORS.find(x=>x.id==='otavio');
  assert.equal(suspended.teamState,'suspended');
  assert.equal(suspended.leadIntakeProjection,'unknown');
});

test('G2: solicitações não reatribuem casos, mudam status ou concessões',()=>{
  const rows=records(),before=rows.map(x=>[x.id,x.assignedTo,x.shopId,x.status]);
  const shops=ACTORS.find(x=>x.id==='rafael').shops.slice();
  requestMockIntake('marina','rafael','pause');
  assert.deepEqual(rows.map(x=>[x.id,x.assignedTo,x.shopId,x.status]),before);
  assert.deepEqual(ACTORS.find(x=>x.id==='rafael').shops,shops);
});
