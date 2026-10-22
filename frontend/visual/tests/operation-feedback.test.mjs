import test from 'node:test';
import assert from 'node:assert/strict';
import {DEMO_OPERATION_STATES,projectDemoOperationFeedback} from '../operation-feedback.mjs';

test('FV-UI-020: sete cenários técnicos são rotulados, sem efeito nem autorização',()=>{
  assert.deepEqual(DEMO_OPERATION_STATES,
    ['accepted','partial','failed','stale','uncertain','denied','unavailable']);
  for(const kind of DEMO_OPERATION_STATES){
    const view=projectDemoOperationFeedback(kind);
    assert.equal(view.kind,kind);
    assert.ok(view.title.length>10);
    assert.ok(view.description.length>15);
    assert.ok(view.nextStep.length>15);
    assert.equal(view.effectConfirmed,false);
    assert.equal(view.automaticRetryAllowed,false);
    assert.equal(view.commercialTransition,false);
    assert.ok(Object.isFrozen(view));
  }
});

test('FV-UI-020: resposta desconhecida/malformada não revela detalhe externo',()=>{
  for(const raw of [undefined,null,1,[],{},'APPLIED','timeout: usuario@exemplo.test',
    'VENDIDO','C13','AUTH_BYPASS']){
    const view=projectDemoOperationFeedback(raw);
    assert.equal(view.kind,'untrusted');
    assert.equal(view.effectConfirmed,false);
    assert.equal(view.automaticRetryAllowed,false);
    assert.equal(JSON.stringify(view).includes('usuario@exemplo.test'),false);
  }
});

test('FV-UI-020: incerteza não vira erro definitivo nem tentativa automática',()=>{
  const uncertain=projectDemoOperationFeedback('uncertain');
  const stale=projectDemoOperationFeedback('stale');
  assert.match(uncertain.description,/não prova falha nem execução/);
  assert.match(uncertain.nextStep,/não repetir a solicitação/);
  assert.match(stale.nextStep,/não reenviar automaticamente/);
});

test('FV-UI-020: negado não revela causa protegida nem concede permissão',()=>{
  const denied=projectDemoOperationFeedback('denied');
  assert.match(denied.description,/Nenhuma informação protegida/);
  assert.match(denied.nextStep,/não executar ação/i);
  assert.equal(Object.hasOwn(denied,'actorId'),false);
  assert.equal(Object.hasOwn(denied,'reasonCode'),false);
});

test('FV-UI-020: falha F03 não libera correção cadastral improvisada',()=>{
  for(const kind of ['failed','unavailable','partial']){
    const d=projectDemoOperationFeedback(kind);
    assert.equal(d.effectConfirmed,false);
    assert.equal(d.commercialTransition,false);
    assert.equal('canEditRegistration' in d,false);
  }
});
