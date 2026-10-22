import test from 'node:test';
import assert from 'node:assert/strict';
import { COMMERCIAL_STATUSES, ACTORS } from '../fixtures.mjs';
import { copyCFDemoFixtures } from '../cf-op-02.mjs';
import { projectTeamMonitoring, describeMonitoring } from '../team-monitoring.mjs';

const sample=()=>copyCFDemoFixtures();

test('G3: Marina acompanha apenas sua equipe incluindo as duas lojas concedidas',()=>{
  const view=projectTeamMonitoring('marina',sample());
  assert.equal(view.visibility,'team_summary');
  assert.deepEqual(view.operators.map(x=>x.id),['rafael','lia']);
  assert.equal(view.summary.operatorCount,2);
  assert.equal(view.summary.activeCases,14); // inclui A-117 (caso-only da Lia)
  assert.equal(view.summary.unreadCases,3);
  assert.equal(view.summary.managerOwnedCases,1);
  assert.equal(view.summary.bankReplyPendingCases,1);
  assert.equal(view.summary.protectedQueueCases,1);
  assert.equal(view.summary.unassignedTeamCases,3);
});

test('G3: Daniel não herda casos, indicadores ou profissionais de Marina',()=>{
  const d=projectTeamMonitoring('daniel',sample());
  assert.deepEqual(d.operators.map(x=>x.id),['bianca','otavio']);
  assert.equal(d.summary.activeCases,2);
  assert.equal(d.summary.unreadCases,1);
  assert.equal(d.summary.protectedQueueCases,0);
  assert.equal(d.summary.bankReplyPendingCases,0);
  assert.equal(d.summary.managerOwnedCases,0);
  assert.equal(d.summary.windowAttentionCases,0);
});

test('G3: pausa de novos leads não remove casos antigos nem equivale a suspensão da conta',()=>{
  const d=projectTeamMonitoring('daniel',sample());
  const b=d.operators.find(x=>x.id==='bianca');
  const o=d.operators.find(x=>x.id==='otavio');
  assert.equal(b.intake,'paused_confirmed');
  assert.equal(b.activeCount,2);
  assert.equal(b.shopsCount,2);
  assert.equal(o.intake,'unavailable');
  assert.equal(d.summary.intakePausedCount,1);
  assert.equal(d.summary.intakeUnavailableCount,1);
  assert.equal(ACTORS.find(x=>x.id==='bianca').teamState,'active');
});

test('G3: perfil operador, inválido ou suspenso não recebe resumo da equipe',()=>{
  for(const actor of ['rafael','bianca','otavio','inexistente']){
    const p=projectTeamMonitoring(actor,sample());
    assert.equal(p.visibility,'forbidden');
    assert.equal(p.summary,null);
    assert.deepEqual(p.operators,[]);
  }
});

test('G3: não expõe identificadores de clientes, conteúdo de mensagens ou ficha D3/D4',()=>{
  const view=projectTeamMonitoring('marina',sample());
  const data=JSON.stringify(view);
  for(const fragment of ['Cliente Exemplo','a105-1','Valor fictício confirmado','bank-demo-v1','Mensagem ilustrativa','cpf','sourceRef']){
    assert.equal(data.includes(fragment),false);
  }
  assert.equal(view.timing,'unverified');
  assert.equal(view.source,'synthetic_fixture');
});

test('G3: etapas comerciais são separadas de alertas técnicos e usam os oito status',()=>{
  const p=projectTeamMonitoring('marina',sample());
  assert.deepEqual(p.commercialStages.map(x=>x.status),COMMERCIAL_STATUSES);
  assert.equal(p.commercialStages.reduce((sum,x)=>sum+x.count,0),p.summary.activeCases);
  assert.equal(p.commercialStages.some(x=>x.status==='janela expirada'),false);
  assert.ok(p.summary.windowAttentionCases>0);
  assert.equal(p.summary.windowAttentionCases,3);
});

test('G3: histórico preservado não infla casos ativos e nenhum relógio é inferido',()=>{
  const p=projectTeamMonitoring('marina',sample());
  assert.equal(p.summary.historicalCases,3);
  assert.equal(p.summary.activeCases,14); // inclui A-117
  assert.equal(p.summary.activeCases+p.summary.historicalCases,17);
  assert.equal(p.summary.unreadCases,3);
  assert.equal('waitingMinutes' in p.summary,false);
  assert.equal('slaExceeded' in p.summary,false);
});

test('G3: equipe sem casos conserva operadores, mas indicadores ficam zerados',()=>{
  const p=projectTeamMonitoring('marina',[]);
  assert.equal(p.summary.operatorCount,2);
  assert.equal(p.summary.activeCases,0);
  assert.equal(p.summary.windowAttentionCases,0);
  assert.equal(p.summary.bankReplyPendingCases,0);
  assert.ok(p.operators.every(x=>x.activeCount===0));
});

test('G3: casos de outra equipe, ainda na mesma concessionária, não entram em soma',()=>{
  const rows=sample();
  rows.push({
    id:'G3-OTHER',assignedTo:'bianca',shopId:'aurora',status:'em atendimento pelo operador',
    inboxProjection:'active',unread:25,metaWindowProjection:'expired',
    humanCompletionProjection:'pending',bankProjection:{phase:'reply_pending'}
  });
  const marina=projectTeamMonitoring('marina',rows);
  const daniel=projectTeamMonitoring('daniel',rows);
  assert.equal(marina.summary.activeCases,14);
  assert.equal(marina.summary.unreadCases,3);
  assert.equal(marina.summary.bankReplyPendingCases,1);
  assert.equal(daniel.summary.activeCases,3);
  assert.equal(daniel.summary.windowAttentionCases,1);
});

test('G3: projeções duplicadas por id não inflam contagens, sem mutar casos',()=>{
  const rows=sample(),count=rows.length;
  rows.push(rows[0]);
  const p=projectTeamMonitoring('marina',rows);
  assert.equal(p.summary.activeCases,14); // inclui A-117
  assert.equal(rows.length,count+1);
  assert.equal(rows[0].status,'em atendimento pelo operador');
});

test('G3: indicadores descrevem projeções e não prometem prazos ou decisão de banco',()=>{
  assert.match(describeMonitoring('windowAttentionCases'),/projeção/);
  assert.match(describeMonitoring('bankReplyPendingCases'),/pendentes de prova/);
  assert.equal(describeMonitoring('unknown'),'Indicador indisponível');
});
