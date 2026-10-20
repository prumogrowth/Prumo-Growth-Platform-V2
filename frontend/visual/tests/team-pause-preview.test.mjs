import test from 'node:test';
import assert from 'node:assert/strict';
import {copyCFDemoFixtures} from '../cf-op-02.mjs';
import {projectManagerPausePreview, classifyPauseCase,
  DEMO_PAUSE_EVIDENCE, PAUSE_PREVIEW_VERSION} from '../team-pause-preview.mjs';

const rows=()=>copyCFDemoFixtures();
const pick=(report,id)=>report.cases.find(row=>row.caseId===id);

test('G2 pausa: gestor vê apenas a própria equipe; operador não vê carteira gerencial',()=>{
  assert.equal(projectManagerPausePreview('rafael','rafael',rows()).visibility,'forbidden');
  assert.equal(projectManagerPausePreview('daniel','rafael',rows()).visibility,'forbidden');
  assert.equal(projectManagerPausePreview('marina','bianca',rows()).visibility,'forbidden');
  assert.equal(projectManagerPausePreview('marina','otavio',rows()).visibility,'forbidden');
  assert.equal(projectManagerPausePreview('marina','rafael',rows()).visibility,'ready');
});

test('G2 pausa: primeiro contato humano comprovado impede redistribuição',()=>{
  const view=projectManagerPausePreview('marina','rafael',rows());
  assert.equal(pick(view,'A-102').outcome,'retain_started');
  assert.equal(view.applied,false);
});

test('G2 pausa: sem destinatário elegível mesma equipe/loja, mantém titular',()=>{
  const a=projectManagerPausePreview('marina','rafael',rows());
  assert.equal(pick(a,'A-107').outcome,'retain_no_recipient');
  assert.equal(pick(a,'A-114').outcome,'retain_no_recipient');
  const b=projectManagerPausePreview('daniel','bianca',rows());
  assert.equal(pick(b,'A-103').outcome,'retain_no_recipient');
  assert.equal(pick(b,'B-203').outcome,'retain_started');
});

test('G2 pausa: elegível mesma equipe com grant e intake gera proposta, não atribuição',()=>{
  const row={id:'B-999',shopId:'horizonte',assignedTo:'rafael',inboxProjection:'active',status:'em atendimento pelo operador'};
  const proof={source:'s0_fixture',caseId:'B-999',ownerId:'rafael',shopId:'horizonte',version:'fixture-1',contactConfirmed:false};
  const candidates=[{id:'lia',role:'operador',managerId:'marina',teamState:'active',leadIntakeProjection:'receiving',shops:['horizonte']}];
  assert.equal(classifyPauseCase(row,proof,candidates,'rafael','marina'),'proposed_same_team');
  assert.equal(row.assignedTo,'rafael');
});

test('G2 pausa: outra equipe e falta de grant não produzem proposta',()=>{
  const row={id:'A-999',shopId:'aurora',assignedTo:'rafael',inboxProjection:'active',status:'em atendimento pelo operador'};
  const proof={source:'s0_fixture',caseId:'A-999',ownerId:'rafael',shopId:'aurora',version:'fixture-1',contactConfirmed:false};
  const another=[{id:'bianca',role:'operador',managerId:'daniel',teamState:'active',leadIntakeProjection:'receiving',shops:['aurora']}];
  const noGrant=[{id:'lia',role:'operador',managerId:'marina',teamState:'active',leadIntakeProjection:'receiving',shops:['horizonte']}];
  assert.equal(classifyPauseCase(row,proof,another,'rafael','marina'),'retain_no_recipient');
  assert.equal(classifyPauseCase(row,proof,noGrant,'rafael','marina'),'retain_no_recipient');
  assert.equal(classifyPauseCase(row,proof,[{...another[0],managerId:'marina',leadIntakeProjection:'paused_confirmed'}],'rafael','marina'),'retain_no_recipient');
});

test('G2 pausa: evento desconhecido, sem fonte ou desencontrado impede movimentação',()=>{
  const original=projectManagerPausePreview('marina','rafael',rows());
  assert.ok(original.summary.unverified>0);
  for(const altered of [[],[{caseId:'A-107',ownerId:'bianca',shopId:'aurora',source:'s0_fixture',version:'v1',contactConfirmed:false}],
    [{caseId:'A-107',ownerId:'rafael',shopId:'aurora',source:'browser_guess',version:'v1',contactConfirmed:false}]]){
    const preview=projectManagerPausePreview('marina','rafael',rows(),altered);
    assert.equal(pick(preview,'A-107').outcome,'retain_unverified');
  }
});

test('G2 pausa: ciclo bancário e histórico não retornam como transferências elegíveis',()=>{
  const view=projectManagerPausePreview('marina','rafael',rows());
  assert.equal(pick(view,'A-105').outcome,'retain_protected');
  assert.equal(pick(view,'A-115'),undefined);
  assert.equal(pick(view,'A-111'),undefined);
});

test('G2 pausa: relatório não contém conversa, dados bancários ou métricas de atraso',()=>{
  const a=projectManagerPausePreview('marina','rafael',rows());
  assert.equal(a.source,PAUSE_PREVIEW_VERSION);
  assert.deepEqual(Object.keys(a.cases[0]).sort(),['caseId','label','outcome','shopName']);
  assert.ok(!JSON.stringify(a).includes('Quero falar com a equipe'));
  assert.ok(!JSON.stringify(a).includes('observedWaitMinutes'));
  assert.ok(Object.isFrozen(a.cases));
});

test('G2 pausa: apenas leitura, nenhum dado fictício original é modificado',()=>{
  const input=rows(),prior=JSON.stringify(input),proof=JSON.stringify(DEMO_PAUSE_EVIDENCE);
  projectManagerPausePreview('marina','rafael',input);
  projectManagerPausePreview('daniel','bianca',input);
  assert.equal(JSON.stringify(input),prior);
  assert.equal(JSON.stringify(DEMO_PAUSE_EVIDENCE),proof);
});
