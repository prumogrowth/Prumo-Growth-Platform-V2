import test from 'node:test';
import assert from 'node:assert/strict';
import { copyCFDemoFixtures } from '../cf-op-02.mjs';
import { projectManagerMonitor, G3_SIGNALS } from '../team-monitor.mjs';

const monitorRecords=()=>copyCFDemoFixtures();
const monitorBy=(id,rows=monitorRecords())=>rows.find(row=>row.id===id);

test('G3-01: Marina monitora apenas casos autorizados da equipe Rafael/Lia',()=>{
  const report=projectManagerMonitor('marina',monitorRecords());
  assert.equal(report.visibility,'ready');
  assert.deepEqual(report.operators.map(x=>x.id),['rafael','lia']);
  assert.equal(report.indicators.teamMembers,2);
  assert.equal(report.indicators.intakePaused,0);
  assert.ok(report.signals.some(x=>x.caseId==='A-102'));
  assert.ok(report.signals.some(x=>x.caseId==='B-201'));
  assert.ok(report.signals.some(x=>x.caseId==='A-112' && x.code==='protected_queue'));
  assert.equal(report.signals.some(x=>x.caseId==='A-103'),false);
  assert.equal(report.signals.some(x=>x.caseId==='B-203'),false);
});

test('G3-02: Daniel vê apenas Bianca/Otávio, com pausa de leads separada de conta',()=>{
  const report=projectManagerMonitor('daniel',monitorRecords());
  assert.deepEqual(report.operators.map(x=>x.id),['bianca','otavio']);
  assert.equal(report.indicators.intakePaused,1);
  assert.ok(report.signals.some(x=>x.caseId==='A-103'));
  assert.ok(report.signals.some(x=>x.caseId==='B-203'));
  assert.equal(report.signals.some(x=>x.caseId==='A-105'),false);
  assert.equal(report.signals.some(x=>x.caseId==='A-112'),false);
});

test('G3-03: operador, gestor inexistente ou inativo recebe acesso negado',()=>{
  for(const id of ['rafael','bianca','otavio','inexistente']){
    const report=projectManagerMonitor(id,monitorRecords());
    assert.equal(report.visibility,'forbidden');
    assert.deepEqual(report.signals,[]);
    assert.equal(report.indicators,null);
  }
});

test('G3-04: pendência de fila protegida depende de escopo e atribuição ausente',()=>{
  const rows=monitorRecords();
  const protectedCase=monitorBy('A-112',rows);
  assert.equal(projectManagerMonitor('marina',rows).indicators.protectedQueue,1);
  protectedCase.assignedTo='rafael';
  assert.equal(projectManagerMonitor('marina',rows).indicators.protectedQueue,0);
  protectedCase.assignedTo=null;protectedCase.teamManagerId='daniel';
  assert.equal(projectManagerMonitor('marina',rows).indicators.protectedQueue,0);
});

test('G3-05: espera só é exibida quando S0 fixture fornece medida válida',()=>{
  const rows=monitorRecords();
  const report=projectManagerMonitor('marina',rows);
  assert.equal(report.signals.find(x=>x.caseId==='A-102').observedWaitMinutes,18);
  assert.equal(report.signals.find(x=>x.caseId==='A-105').observedWaitMinutes,null);
  assert.match(report.asOf,/fictício/i);
  assert.equal(report.indicators.observedWaits,2);
});

test('G3-06: tempo inválido não vira zero ou SLA presumido',()=>{
  const rows=monitorRecords();
  const caseRow=monitorBy('A-102',rows);
  for(const minutes of [-1,NaN,'25',Infinity]){
    caseRow.monitorProjection.observedWaitMinutes=minutes;
    const signal=projectManagerMonitor('marina',rows).signals.find(x=>x.caseId==='A-102');
    assert.equal(signal.observedWaitMinutes,null);
  }
});

test('G3-07: sinais técnicos inválidos ou sem fonte são ignorados',()=>{
  const rows=monitorRecords();
  const caseRow=monitorBy('A-102',rows);
  caseRow.monitorProjection={code:'approved_by_bank',origin:'s0_fixture',observedAt:'T0'};
  assert.equal(projectManagerMonitor('marina',rows).signals.some(x=>x.caseId==='A-102'),false);
  caseRow.monitorProjection={code:'waiting_human',origin:'browser_guess',observedAt:'T0',observedWaitMinutes:3};
  assert.equal(projectManagerMonitor('marina',rows).signals.some(x=>x.caseId==='A-102'),false);
  assert.equal(Object.hasOwn(G3_SIGNALS,'approved_by_bank'),false);
});

test('G3-08: histórico vendido/perdido não aparece como alerta de caso ativo',()=>{
  const rows=monitorRecords(),sold=monitorBy('A-115',rows);
  sold.monitorProjection={origin:'s0_fixture',code:'waiting_human',observedAt:'T0',observedWaitMinutes:10};
  const report=projectManagerMonitor('marina',rows);
  assert.equal(report.signals.some(x=>x.caseId==='A-115'),false);
  assert.ok(report.indicators.historical>0);
});

test('G3-09: pedido local conta como pendente, não como pausa confirmada',()=>{
  const rows=monitorRecords();
  const request={actorId:'marina',operatorId:'rafael',state:'requested_demo',action:'pause'};
  const report=projectManagerMonitor('marina',rows,{rafael:request});
  assert.equal(report.indicators.pendingLocalRequests,1);
  assert.equal(report.indicators.intakePaused,0);
  assert.equal(report.operators.find(x=>x.id==='rafael').intake,'receiving');
  const foreign=projectManagerMonitor('daniel',rows,{rafael:request});
  assert.equal(foreign.indicators.pendingLocalRequests,0);
});

test('G3-10: solicitações forjadas sem ator correto não são contadas',()=>{
  const rows=monitorRecords();
  const request={actorId:'daniel',operatorId:'rafael',state:'requested_demo'};
  assert.equal(projectManagerMonitor('marina',rows,{rafael:request}).indicators.pendingLocalRequests,0);
  assert.equal(projectManagerMonitor('marina',rows,{rafael:{...request,actorId:'marina',state:'applied'}}).indicators.pendingLocalRequests,0);
});

test('G3-11: monitoramento não altera proprietário, estado ou fila',()=>{
  const rows=monitorRecords();
  const snapshot=JSON.stringify(rows);
  projectManagerMonitor('marina',rows);
  projectManagerMonitor('daniel',rows);
  assert.equal(JSON.stringify(rows),snapshot);
});

test('G3-12: projeções técnicas são isoladas entre reinicializações',()=>{
  const first=monitorRecords(),second=monitorRecords();
  monitorBy('A-102',first).monitorProjection.observedWaitMinutes=999;
  assert.equal(monitorBy('A-102',second).monitorProjection.observedWaitMinutes,18);
});

test('G3-13: concessionária continua condição cumulativa de acesso',()=>{
  const rows=monitorRecords();
  monitorBy('B-201',rows).shopId='fora_concessao';
  assert.equal(projectManagerMonitor('marina',rows).signals.some(x=>x.caseId==='B-201'),false);
  assert.equal(projectManagerMonitor('daniel',rows).signals.some(x=>x.caseId==='B-201'),false);
});
